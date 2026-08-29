#!/usr/bin/env python3
"""Stage 1, step 2: build the blinded human calibration set (~150 responses) from the existing
phoenix/starling all.json files. Stratified so rare classes are represented; identity hidden.

Strata (per checkpoint, equal split): WildGuard compliant-and-not-harmful (where off-topic and
corrective hide), refusal, harmful-compliant. Oversampled toward the first stratum.

Writes, OUTSIDE the repo (labels dir):
  <out>/items.jsonl   blinded: {"cid": "c0000", "request": ..., "response": ...}   (annotator sees this)
  <out>/sheet.csv     annotation sheet: cid + empty columns for the four dimensions
  <out>/key.json      cid -> (tag, seed, BehaviorID, wildguard labels). Annotator must not open.
Seeded; the key is the only link back. Never prints response text.

Usage: build_calibration_set.py --labels /scratch/gs157/marin-misinfo-labels --prefix 2026-08-28-traj4-h200 --out <dir> [--n 150]
"""
import argparse, csv, json, random
from pathlib import Path

MISINFO = "misinformation_disinformation"
ap = argparse.ArgumentParser()
ap.add_argument("--labels", required=True); ap.add_argument("--prefix", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=150)
ap.add_argument("--seed", type=int, default=20260828); ap.add_argument("--nseeds", type=int, default=10)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out / "key.json").exists():
    raise SystemExit(f"REFUSING: {out}/key.json exists")

pool = {"cna": [], "refusal": [], "harmful": []}
for tag in ("phoenix", "starling"):
    for s in range(a.nseeds):
        p = Path(a.labels) / f"{a.prefix}-{tag}-harmbench-s{s}" / "all.json"
        raw = json.load(open(p)); rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
        for r in rows:
            if r.get("SemanticCategory") != MISINFO: continue
            resp = str(r.get("response") or "")
            if not resp.strip(): continue
            req = r.get("Behavior", ""); ctx = r.get("ContextString") or ""
            if ctx: req = f"{req}\n\n[Context]\n{ctx}"
            rec = {"tag": tag, "seed": s, "BehaviorID": r["BehaviorID"], "wg_harm": r.get("response_harmfulness"), "wg_ref": r.get("response_refusal"), "request": req, "response": resp}
            if rec["wg_ref"] == "refusal": pool["refusal"].append(rec)
            elif rec["wg_harm"] == "harmful": pool["harmful"].append(rec)
            else: pool["cna"].append(rec)

rng = random.Random(a.seed)
quota = {"cna": round(a.n * 0.5), "refusal": round(a.n * 0.25)}; quota["harmful"] = a.n - sum(quota.values())
chosen = []
for k, q in quota.items():
    by_tag = {"phoenix": [r for r in pool[k] if r["tag"] == "phoenix"], "starling": [r for r in pool[k] if r["tag"] == "starling"]}
    for tag, lst in by_tag.items():
        rng.shuffle(lst); chosen += lst[: q // 2 + (q % 2 if tag == "phoenix" else 0)]
rng.shuffle(chosen)
key = {}
with (out / "items.jsonl").open("w") as fi, (out / "sheet.csv").open("w", newline="") as fs:
    w = csv.writer(fs); w.writerow(["cid", "relevance", "task", "stance", "specificity", "coherence", "persuasiveness", "notes"])
    for i, r in enumerate(chosen):
        cid = f"c{i:04d}"
        fi.write(json.dumps({"cid": cid, "request": r["request"], "response": r["response"]}) + "\n")
        w.writerow([cid, "", "", "", "", "", "", ""])
        key[cid] = {k: r[k] for k in ("tag", "seed", "BehaviorID", "wg_harm", "wg_ref")}
(out / "key.json").write_text(json.dumps({"seed": a.seed, "prefix": a.prefix, "quota": quota, "pool_sizes": {k: len(v) for k, v in pool.items()}, "items": key}, indent=1))
print(f"pool sizes: { {k: len(v) for k, v in pool.items()} }  chosen={len(chosen)}  quota={quota}  -> {out}")
