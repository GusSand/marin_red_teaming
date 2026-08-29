#!/usr/bin/env python3
"""Export ALL non-empty misinfo responses for a set of runs as blinded judge items + key (Stage 1, step 3
and step 4 judging). Same schema as the calibration set. Output goes OUTSIDE the repo (labels dir).

Usage: export_items.py --labels <dir> --runs <run_name>... --out <dir>
  run_name = directory under --labels holding all.json. Key maps cid -> (run, BehaviorID, wildguard labels).
"""
import argparse, json
from pathlib import Path
MISINFO = "misinformation_disinformation"
ap = argparse.ArgumentParser()
ap.add_argument("--labels", required=True); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
if (out / "key.json").exists(): raise SystemExit(f"REFUSING: {out}/key.json exists")
key, n = {}, 0
with (out / "items.jsonl").open("w") as fi:
    for run in a.runs:
        raw = json.load(open(Path(a.labels) / run / "all.json")); rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
        for idx, r in enumerate(rows):
            if r.get("SemanticCategory") != MISINFO: continue
            resp = str(r.get("response") or "")
            req = r.get("Behavior", ""); ctx = r.get("ContextString") or ""
            if ctx: req = f"{req}\n\n[Context]\n{ctx}"
            cid = f"i{n:05d}"; n += 1
            fi.write(json.dumps({"cid": cid, "request": req, "response": resp}) + "\n")
            key[cid] = {"run": run, "row_index": idx, "BehaviorID": r["BehaviorID"], "wg_harm": r.get("response_harmfulness"), "wg_ref": r.get("response_refusal"), "empty": not resp.strip()}
(out / "key.json").write_text(json.dumps({"runs": a.runs, "items": key}, indent=1))
print(f"{n} items from {len(a.runs)} runs -> {out}")
