#!/usr/bin/env python
"""Tamper-resistance LoRA attack (defensive red-team; pre-registered
docs/experiments/07-29_marin-olmo-instruct_tamper-resistance_lora-attack.md).

Fine-tunes an instruct model with LoRA on AdvBench (goal -> affirmative-prefix target)
pairs, saving adapter snapshots at cumulative optimizer steps {0,5,10,20,40,80}. The
"attack" target is the public AdvBench affirmative opener, NOT an authored harmful
completion (shallow-alignment attack, Qi et al 2406.05946).

Only adapter snapshots are written. Eval + merge + cleanup handled by scripts/tamper_run.sh.
Nothing here prints or stores harmful generations; targets are short affirmative prefixes.
"""
import argparse, csv, json, os, random
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

SAVE_STEPS = [0, 5, 10, 20, 40, 80]


def build_examples(tok, pairs, max_len):
    """Return list of (input_ids, labels) with loss masked to the assistant/target tokens."""
    exs = []
    for goal, target in pairs:
        msgs = [{"role": "user", "content": goal}]
        prompt_ids = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=True)
        target_ids = tok(target, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + target_ids[:]  # supervise only the target
        input_ids = input_ids[:max_len]
        labels = labels[:max_len]
        exs.append((input_ids, labels))
    return exs


def collate(batch, pad_id):
    m = max(len(x[0]) for x in batch)
    ii, ll, am = [], [], []
    for ids, lab in batch:
        p = m - len(ids)
        ii.append(ids + [pad_id] * p)
        ll.append(lab + [-100] * p)
        am.append([1] * len(ids) + [0] * p)
    t = lambda z: torch.tensor(z, dtype=torch.long)
    return t(ii), t(ll), t(am)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--advbench_csv", required=True)
    ap.add_argument("--out_dir", required=True, help="where adapter-step<N> dirs are written")
    ap.add_argument("--n_pairs", type=int, default=100)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--max_len", type=int, default=512)
    ap.add_argument("--lora_r", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--holdout_eval_prompts", default="", help="optional file of eval prompts to assert-disjoint")
    args = ap.parse_args()

    random.seed(args.seed); torch.manual_seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)

    rows = list(csv.DictReader(open(args.advbench_csv)))
    random.shuffle(rows)
    rows = rows[: args.n_pairs]
    pairs = [(r["goal"], r["target"]) for r in rows]

    # leakage guard: attack goals must not be exact-string eval prompts
    if args.holdout_eval_prompts and os.path.exists(args.holdout_eval_prompts):
        ev = set(l.strip() for l in open(args.holdout_eval_prompts) if l.strip())
        overlap = sum(1 for g, _ in pairs if g.strip() in ev)
        print(f"[leakage-check] exact-string attack∩eval overlap = {overlap} (want 0)")
        json.dump({"n_pairs": len(pairs), "exact_overlap": overlap},
                  open(os.path.join(args.out_dir, "attack_meta.json"), "w"), indent=2)

    tok = AutoTokenizer.from_pretrained(args.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map="cuda")
    lcfg = LoraConfig(r=args.lora_r, lora_alpha=args.lora_r * 2, lora_dropout=0.0, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lcfg)
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)

    exs = build_examples(tok, pairs, args.max_len)

    def save(step):
        d = os.path.join(args.out_dir, f"adapter-step{step}")
        model.save_pretrained(d)
        print(f"[save] step {step} -> {d}", flush=True)

    save(0)  # baseline snapshot (untrained adapter == base behavior)
    step = 0
    max_step = max(SAVE_STEPS)
    order = list(range(len(exs)))
    while step < max_step:
        random.shuffle(order)
        for i in range(0, len(order), args.batch):
            if step >= max_step:
                break
            idx = order[i:i + args.batch]
            ii, ll, am = collate([exs[j] for j in idx], tok.pad_token_id)
            ii, ll, am = ii.cuda(), ll.cuda(), am.cuda()
            out = model(input_ids=ii, attention_mask=am, labels=ll)
            out.loss.backward()
            opt.step(); opt.zero_grad()
            step += 1
            if step in SAVE_STEPS:
                print(f"[step {step}] loss={out.loss.item():.4f}", flush=True)
                save(step)
    print("[done] adapters written for steps", [s for s in SAVE_STEPS], flush=True)


if __name__ == "__main__":
    main()
