#!/usr/bin/env python3
"""Stage 1, step 1: IFEval summary across tags with the pre-registered trigger:
starling - phoenix >= +5pp prompt-level strict, bootstrap 95% CI over prompts (10k, seed 20260828) excl. 0.
Reads the official scorer's eval_results_strict.jsonl / eval_results_loose.jsonl per tag and variant.
Usage: ifeval_summary.py --root <runs/ifeval/<prefix>> --out <json>
"""
import argparse, json
from pathlib import Path
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("--root", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
TAGS = ["jellyfish", "phoenix", "starling", "deeper-starling"]; rng = np.random.default_rng(20260828)
def load(tag, variant, mode):
    p = Path(a.root) / tag / f"eval_{variant}" / f"eval_results_{mode}.jsonl"
    if not p.exists(): return None
    rows = [json.loads(l) for l in open(p)]
    return {r["prompt"]: (bool(r["follow_all_instructions"]), r["follow_instruction_list"]) for r in rows}
res = {"levels": {}, "contrasts": {}, "provenance": {}}
for tag in TAGS:
    prov = Path(a.root) / tag / "provenance.json"
    if prov.exists():
        pv = json.load(open(prov)); res["provenance"][tag] = {k: pv[k] for k in ("n_empty", "n_fake_next_turn", "n_hit_max_len", "gpu", "ifeval_sha")}
    for variant in ("truncated", "raw"):
        for mode in ("strict", "loose"):
            d = load(tag, variant, mode)
            if d is None: continue
            pl = np.mean([v[0] for v in d.values()]); il = np.mean([x for v in d.values() for x in v[1]])
            res["levels"][f"{tag}/{variant}/{mode}"] = {"prompt_level": round(100 * pl, 2), "instruction_level": round(100 * il, 2), "n": len(d)}
def contrast(A, B, variant="truncated", mode="strict"):
    dA, dB = load(A, variant, mode), load(B, variant, mode)
    if dA is None or dB is None: return None
    ps = sorted(set(dA) & set(dB)); d = np.array([dB[p][0] - dA[p][0] for p in ps], float)
    boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(10000)]
    return {"delta_pp": round(100 * d.mean(), 2), "ci95": [round(100 * np.percentile(boots, 2.5), 2), round(100 * np.percentile(boots, 97.5), 2)], "n": len(ps)}
for A, B in [("phoenix", "starling"), ("jellyfish", "phoenix"), ("starling", "deeper-starling"), ("phoenix", "deeper-starling")]:
    for variant in ("truncated", "raw"):
        c = contrast(A, B, variant)
        if c: res["contrasts"][f"{A}->{B}/{variant}/strict"] = c
c = res["contrasts"].get("phoenix->starling/truncated/strict")
if c: res["trigger_step5"] = {"criterion": ">= +5pp and CI excludes 0", "delta_pp": c["delta_pp"], "ci95": c["ci95"], "fired": bool(c["delta_pp"] >= 5 and c["ci95"][0] > 0)}
json.dump(res, open(a.out, "w"), indent=2); print(json.dumps(res, indent=1))
