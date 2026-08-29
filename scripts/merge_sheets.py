#!/usr/bin/env python3
"""Merge the four annotator part-sheets into one judge-style jsonl that decompose_distribution.py can read.

Validates before merging: all expected cids present exactly once, values in vocabulary, quality present
exactly when task != no_attempt. Fails loudly rather than silently dropping rows.

Usage: merge_sheets.py --parts <dir with sheet_part*.csv> --items items.jsonl --out <judge>.jsonl
"""
import argparse, csv, json, sys
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--parts", required=True); ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
V = {"relevance": {"on_topic", "partial", "off_topic"}, "task": {"complete", "partial", "no_attempt"},
     "stance": {"refuses", "corrects", "hedges", "endorses"}}
QK = ("specificity", "coherence", "persuasiveness")
expected = [json.loads(l)["cid"] for l in Path(a.items).read_text().splitlines() if l.strip()]
rows = {}
for p in sorted(Path(a.parts).glob("sheet_part*.csv")):
    n = 0
    for r in csv.DictReader(open(p)):
        cid = r["cid"].strip()
        if cid in rows: sys.exit(f"FAIL duplicate cid {cid} (second copy in {p.name})")
        rows[cid] = r; n += 1
    print(f"  {p.name}: {n} rows")
missing = [c for c in expected if c not in rows]; extra = [c for c in rows if c not in set(expected)]
if missing or extra: sys.exit(f"FAIL missing {len(missing)} (first: {missing[:5]}), unexpected {len(extra)}")
bad = []
for cid, r in rows.items():
    for d, ok in V.items():
        if r[d].strip() not in ok: bad.append((cid, d, r[d]))
    q = [r[k].strip() for k in QK]
    if r["task"].strip() == "no_attempt":
        if any(q): bad.append((cid, "quality", "filled on no_attempt"))
    elif not all(x in {"1", "2", "3", "4", "5"} for x in q):
        bad.append((cid, "quality", "missing/invalid on attempted"))
if bad: sys.exit(f"FAIL {len(bad)} invalid values, first 10: {bad[:10]}")
with open(a.out, "w") as f:
    for cid in expected:
        r = rows[cid]
        o = {"cid": cid, "relevance": r["relevance"].strip(), "task": r["task"].strip(), "stance": r["stance"].strip()}
        for k in QK: o[k] = None if r["task"].strip() == "no_attempt" else int(r[k])
        f.write(json.dumps(o) + "\n")
print(f"OK {len(expected)} rows -> {a.out}")
for d in V: print(" ", d, dict(Counter(rows[c][d].strip() for c in expected)))
