#!/usr/bin/env python3
"""Iron Law hand inspection: is (harmful AND refusal) empty by construction of the judge?

Raw row-level cross-tabulation, no behaviour aggregation, over every S1-PREFIX arm and the
traj4 reference. Also dumps the DISTINCT label vocabularies actually present. Counts only.
"""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, "scripts")
from analyze_trajectory import MISINFO  # noqa: E402

L = Path("/scratch/gs157/marin-misinfo-labels")
RUNS = [("2026-09-08-prefix-h200", t, 5) for t in ("none", "delivery", "deflect")] + \
       [("2026-08-28-traj4-h200", t, 10) for t in ("phoenix", "starling")]

vocab_h, vocab_r, grand = Counter(), Counter(), Counter()
print(f"{'tag':12s} {'n':>5s} {'h&r':>5s} {'h&NOTr':>7s} {'NOTh&r':>7s} {'NOTh&NOTr':>10s}")
for prefix, tag, ns in RUNS:
    c = Counter()
    for s in range(ns):
        raw = json.load(open(L / f"{prefix}-{tag}-harmbench-s{s}" / "all.json"))
        for r in next(v for v in raw.values() if isinstance(v, list)):
            if r.get("SemanticCategory") != MISINFO:
                continue
            hv, rv = r.get("response_harmfulness"), r.get("response_refusal")
            vocab_h[str(hv)] += 1; vocab_r[str(rv)] += 1
            c[(hv == "harmful", rv == "refusal")] += 1
    grand.update(c)
    n = sum(c.values())
    print(f"{tag:12s} {n:5d} {c[(1,1)]:5d} {c[(1,0)]:7d} {c[(0,1)]:7d} {c[(0,0)]:10d}")
print(f"\nGRAND n={sum(grand.values())}  harmful&refusal={grand[(1,1)]}")
print("harmfulness vocabulary:", dict(vocab_h))
print("refusal vocabulary:    ", dict(vocab_r))
