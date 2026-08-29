#!/usr/bin/env python3
"""Pick the spot-check subset for the human audit: items where the anchor (sheet_claude.csv) disagrees with
BOTH local judges on any categorical dimension, up to --n, seeded. Writes <d>/spotcheck/items.jsonl and an
empty sheet.csv so scripts/annotate.py can be pointed at <d>/spotcheck. No response text printed.
Usage: build_spotcheck.py <calibration dir> [--n 25]
"""
import csv, json, random, sys
from pathlib import Path
d = Path(sys.argv[1]); n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 25
items = {json.loads(l)["cid"]: json.loads(l) for l in (d / "items.jsonl").read_text().splitlines() if l.strip()}
anchor = {r["cid"]: r for r in csv.DictReader(open(d / "sheet_claude.csv"))}
J = {p.stem: {json.loads(l)["cid"]: json.loads(l) for l in open(p)} for p in (d / "judge").glob("*.jsonl")}
dis = []
for cid, a in anchor.items():
    for dim in ("relevance", "task", "stance"):
        if all(J[j].get(cid, {}).get(dim) != a[dim] for j in J):
            dis.append((cid, dim)); break
rng = random.Random(20260828); rng.shuffle(dis); pick = dis[:n]
out = d / "spotcheck"; out.mkdir(exist_ok=True)
with (out / "items.jsonl").open("w") as f:
    for cid, _ in pick: f.write(json.dumps(items[cid]) + "\n")
with (out / "sheet.csv").open("w", newline="") as f:
    w = csv.writer(f); w.writerow(["cid", "relevance", "task", "stance", "specificity", "coherence", "persuasiveness", "notes"])
    for cid, _ in pick: w.writerow([cid, "", "", "", "", "", "", ""])
(out / "why.json").write_text(json.dumps({"n_disagree_both": len(dis), "picked": pick}, indent=1))
print(f"anchor disagrees with both judges on {len(dis)}/{len(anchor)} items; picked {len(pick)} -> {out}")
