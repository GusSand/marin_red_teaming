#!/usr/bin/env python3
"""IFEval generation for a Marin base checkpoint under the base scaffold (Stage 1, step 1).

Spec: docs/experiments/08-28_phoenix-starling_distribution-decomposition.md

Greedy (the official IFEval protocol), max_new_tokens 2048 to match the misinfo runs, NO stop
strings at generation time. Two response files are written from the one generation:
  responses_raw.jsonl        -- untouched
  responses_truncated.jsonl  -- cut at the first "\nUser:" (a base model starting a fake next
                                turn is a scaffold artefact, not an instruction failure). PRIMARY.
Both are scored by the official evaluation_main.py so the choice is visible, not hidden.

Usage: ifeval_generate.py --model <snapshot dir> --template <file> --input <jsonl> --out <dir>
"""
import argparse, json, os, platform, subprocess, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--template", required=True)
ap.add_argument("--input", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--max-new-tokens", type=int, default=2048)
ap.add_argument("--tag", default="")
a = ap.parse_args()

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out / "responses_raw.jsonl").exists():
    print(f"REFUSING: {out}/responses_raw.jsonl exists (no silent overwrite)", file=sys.stderr); sys.exit(3)

template = Path(a.template).read_text()
assert "{instruction}" in template, "scaffold must contain {instruction}"
rows = [json.loads(l) for l in Path(a.input).read_text().splitlines() if l.strip()]
prompts = [template.replace("{instruction}", r["prompt"]) for r in rows]

from vllm import LLM, SamplingParams  # noqa: E402
import vllm, torch, transformers  # noqa: E402

t0 = time.time()
llm = LLM(model=a.model, dtype="bfloat16", seed=0, gpu_memory_utilization=0.85, max_model_len=4096)
sp = SamplingParams(temperature=0.0, max_tokens=a.max_new_tokens, seed=0)
outs = llm.generate(prompts, sp)
gen_s = time.time() - t0

def trunc(s):
    i = s.find("\nUser:")
    return s if i < 0 else s[:i]

with (out / "responses_raw.jsonl").open("w") as fr, (out / "responses_truncated.jsonl").open("w") as ft:
    for r, o in zip(rows, outs):
        txt = o.outputs[0].text
        fr.write(json.dumps({"prompt": r["prompt"], "response": txt}) + "\n")
        ft.write(json.dumps({"prompt": r["prompt"], "response": trunc(txt)}) + "\n")

n_empty = sum(1 for o in outs if not o.outputs[0].text.strip())
n_fake_turn = sum(1 for o in outs if "\nUser:" in o.outputs[0].text)
n_maxlen = sum(1 for o in outs if o.outputs[0].finish_reason == "length")

def sh(c):
    try: return subprocess.check_output(c, shell=True, text=True).strip()
    except Exception as e: return f"unavailable: {e}"

prov = {
    "tag": a.tag, "model_path": a.model, "template": a.template, "template_text": template,
    "input": a.input, "n_prompts": len(rows), "decoding": {"temperature": 0.0, "max_new_tokens": a.max_new_tokens, "seed": 0},
    "n_empty": n_empty, "n_fake_next_turn": n_fake_turn, "n_hit_max_len": n_maxlen, "gen_seconds": round(gen_s, 1),
    "hostname": platform.node(), "gpu": sh("nvidia-smi --query-gpu=name,uuid,driver_version --format=csv,noheader"),
    "vllm": vllm.__version__, "torch": torch.__version__, "transformers": transformers.__version__,
    "vllm_v1_multiprocessing": os.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING"),
    "ifeval_sha": sh(f"git -C {Path(a.input).resolve().parents[2]} rev-parse HEAD"),
}
(out / "provenance.json").write_text(json.dumps(prov, indent=2))
print(f"[ifeval-gen] {a.tag}: {len(rows)} prompts, empty={n_empty} fake_turn={n_fake_turn} maxlen={n_maxlen} in {gen_s:.0f}s")
