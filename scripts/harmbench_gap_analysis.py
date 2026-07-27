#!/usr/bin/env python
"""Break down the HarmBench refusal gap between two models by category, and list the
specific behaviors one complies with that the other refuses. Reads raw all.json (3 runs).
Usage: python scripts/harmbench_gap_analysis.py <prefixA> <prefixB>
  e.g.  ... 2026-07-26-marin-instruct 2026-07-26-instruct
Default compares marin-instruct vs olmo-instruct."""
import json, sys
from collections import defaultdict, Counter
RUNS = "/home/paperspace/marin/repro-olmo3-safety/runs"
A = sys.argv[1] if len(sys.argv) > 1 else "2026-07-26-marin-instruct"
B = sys.argv[2] if len(sys.argv) > 2 else "2026-07-26-instruct"

def load(prefix):
    beh = defaultdict(lambda: {"harm": [], "meta": None, "resp": None})
    for rn in [1, 2, 3]:
        d = json.load(open(f"{RUNS}/{prefix}-harmbench-r{rn}/all.json")); k = list(d.keys())[0]
        for x in d[k]:
            bid = x.get("BehaviorID") or x.get("id")
            h = (x.get("response_harmfulness") == "harmful")
            beh[bid]["harm"].append(h)
            if beh[bid]["meta"] is None:
                beh[bid]["meta"] = (x.get("FunctionalCategory"), x.get("SemanticCategory"), x.get("Behavior"))
            if h and beh[bid]["resp"] is None:
                beh[bid]["resp"] = x.get("response")
    return beh

M, O = load(A), load(B)
rate = lambda b: sum(b["harm"]) / len(b["harm"])
def agg(beh, idx):
    cat = defaultdict(lambda: [0, 0.0])
    for b in beh.values():
        cat[b["meta"][idx]][0] += 1; cat[b["meta"][idx]][1] += rate(b)
    return {c: (n, s / n) for c, (n, s) in cat.items()}
for label, idx in [("SemanticCategory", 1), ("FunctionalCategory", 0)]:
    ma, oa = agg(M, idx), agg(O, idx)
    print(f"\n=== {label}: ASR {A} vs {B} ===")
    for c in sorted(ma, key=lambda c: -(ma[c][1] - oa.get(c, (0, 0))[1])):
        n, mr = ma[c]; orr = oa.get(c, (0, 0))[1]
        print(f"  {str(c):30}{n:>4}  A={mr*100:5.1f}  B={orr*100:5.1f}  Δ={mr*100-orr*100:+5.1f}")
gaps = [(M[bid]["meta"][1], M[bid]["meta"][2]) for bid in M if rate(M[bid]) >= 0.66 and rate(O[bid]) == 0.0]
print(f"\nBehaviors {A} complies (>=2/3) but {B} refuses (0/3): {len(gaps)}")
print("by category:", dict(Counter(g[0] for g in gaps)))
