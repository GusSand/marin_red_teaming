#!/usr/bin/env python3
"""Stage 1, step 2/3: run a local judge on blinded items with the LOCKED rubric (config/judge_rubric_v1).

One response per call, four calls per item (one per dimension), greedy, JSON output. Quality is asked
for every item and nulled downstream when task == no_attempt (keeps calls uniform).

Input: items.jsonl ({"cid","request","response"}). Output: <out>/<judge_name>.jsonl, one row per cid
with the four parsed fields plus raw strings, and a provenance sidecar. Never prints response text.

Usage: judge_dimensions.py --judge <hf snapshot dir or repo id> --name qwen72 --items items.jsonl --out <dir> [--quant fp8]
"""
import argparse, hashlib, json, os, platform, re, subprocess, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--judge", required=True); ap.add_argument("--name", required=True)
ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--rubric", default=str(Path(__file__).resolve().parents[1] / "config" / "judge_rubric_v1"))
ap.add_argument("--quant", default=None); ap.add_argument("--max-model-len", type=int, default=8192)
ap.add_argument("--tp", type=int, default=1)
a = ap.parse_args()

rub = Path(a.rubric)
files = sorted(p for p in rub.iterdir() if p.suffix in (".txt", ".md"))
rubric_sha = hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()
system = (rub / "system.txt").read_text().strip()
DIMS = ["relevance", "task", "stance", "quality"]
prompts = {d: (rub / f"prompt_{d}.txt").read_text() for d in DIMS}

items = [json.loads(l) for l in Path(a.items).read_text().splitlines() if l.strip()]
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
dst = out / f"{a.name}.jsonl"
if dst.exists(): raise SystemExit(f"REFUSING: {dst} exists")

def fill(d, it):
    return prompts[d].replace("{request}", it["request"]).replace("{response}", it["response"][:6000])

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(a.judge)
kw = dict(model=a.judge, dtype="bfloat16", seed=0, max_model_len=a.max_model_len, gpu_memory_utilization=0.92, tensor_parallel_size=a.tp)
if a.quant: kw["quantization"] = a.quant
t0 = time.time(); llm = LLM(**kw)
sp = SamplingParams(temperature=0.0, max_tokens=64, seed=0)

reqs = []
for it in items:
    for d in DIMS:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": fill(d, it)}]
        reqs.append((it["cid"], d, tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)))
outs = llm.generate([r[2] for r in reqs], sp)

def parse(txt):
    m = re.search(r"\{.*?\}", txt, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

rows = {it["cid"]: {"cid": it["cid"]} for it in items}
n_bad = 0
for (cid, d, _), o in zip(reqs, outs):
    txt = o.outputs[0].text; js = parse(txt)
    rows[cid][f"raw_{d}"] = txt
    if js is None: n_bad += 1; continue
    if d == "quality":
        for k in ("specificity", "coherence", "persuasiveness"):
            v = js.get(k); rows[cid][k] = int(v) if isinstance(v, (int, float)) and 1 <= v <= 5 else None
    else:
        rows[cid][d] = js.get(d)
for cid, r in rows.items():
    if r.get("task") == "no_attempt":
        for k in ("specificity", "coherence", "persuasiveness"): r[k] = None
with dst.open("w") as f:
    for cid in (it["cid"] for it in items): f.write(json.dumps(rows[cid]) + "\n")

def sh(c):
    try: return subprocess.check_output(c, shell=True, text=True).strip()
    except Exception as e: return f"unavailable: {e}"
import vllm, torch, transformers
(out / f"{a.name}.provenance.json").write_text(json.dumps({
    "judge": a.judge, "name": a.name, "quant": a.quant, "rubric_dir": str(rub), "rubric_sha256": rubric_sha,
    "n_items": len(items), "n_calls": len(reqs), "n_unparsed": n_bad, "seconds": round(time.time() - t0),
    "decoding": {"temperature": 0.0, "max_tokens": 64}, "hostname": platform.node(),
    "gpu": sh("nvidia-smi --query-gpu=name,uuid,driver_version --format=csv,noheader"),
    "vllm": vllm.__version__, "torch": torch.__version__, "transformers": transformers.__version__,
    "vllm_v1_multiprocessing": os.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING")}, indent=2))
print(f"[judge] {a.name}: {len(items)} items, {len(reqs)} calls, unparsed={n_bad}, {time.time()-t0:.0f}s -> {dst}")
