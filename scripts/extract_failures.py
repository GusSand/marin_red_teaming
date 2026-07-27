#!/usr/bin/env python
"""Expand failure examples: per model, per HarmBench SemanticCategory, sample up to N behaviors where
that model FAILED (response_harmfulness=harmful across >=2/3 runs), with the paired other-model outcome.
Truncate responses to preamble. Output readable markdown. Reads existing all.json (no GPU)."""
import json, sys
from collections import defaultdict
RUNS = "/home/paperspace/marin/repro-olmo3-safety/runs"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10

def load(prefix, bench):
    beh = {}
    for rn in [1, 2, 3]:
        d = json.load(open(f"{RUNS}/{prefix}-{bench}-r{rn}/all.json")); items = d[list(d.keys())[0]]
        for x in items:
            bid = x.get("BehaviorID") or x.get("id")
            e = beh.setdefault(bid, {"harm": 0, "n": 0, "meta": None, "resp": None, "refusal": None})
            e["harm"] += (x.get("response_harmfulness") == "harmful"); e["n"] += 1
            if e["meta"] is None:
                e["meta"] = (x.get("SemanticCategory"), x.get("Behavior"))
            if x.get("response_harmfulness") == "harmful" and e["resp"] is None:
                e["resp"] = x.get("response"); e["refusal"] = x.get("response_refusal")
    return beh

M = load("2026-07-26-marin-instruct", "harmbench")
O = load("2026-07-26-instruct", "harmbench")
rate = lambda e: e["harm"] / e["n"]

def failures_by_cat(model, other):
    cat = defaultdict(list)
    for bid, e in model.items():
        if rate(e) >= 0.66:  # failed majority of runs
            oth = other.get(bid, {})
            othr = rate(oth) if oth.get("n") else 0
            cat[e["meta"][0]].append((bid, e, othr))
    return cat

out = ["# Expanded failure examples — Marin & Olmo instruct (HarmBench, grades verified)\n",
       "Per model, per category: behaviors the model failed (response_harmfulness=harmful in >=2/3 runs).",
       "Response truncated to preamble. 'other' = the other model's harmful-rate on the same behavior.\n"]
for name, model, other in [("MARIN-8b-instruct", M, O), ("OLMo-3-7B-instruct", O, M)]:
    out.append(f"\n## {name} failures\n")
    cats = failures_by_cat(model, other)
    for c in sorted(cats, key=lambda c: -len(cats[c])):
        rows = cats[c][:N]
        out.append(f"\n### {c}  ({len(cats[c])} total, showing {len(rows)})")
        for bid, e, othr in rows:
            other_note = "other model ALSO fails" if othr >= 0.66 else ("other model REFUSES" if othr == 0 else f"other={othr*100:.0f}%")
            out.append(f"- **{e['meta'][1][:120]}**")
            out.append(f"  - grade: harm={('harmful')} refusal={e['refusal']} | {other_note}")
            out.append(f"  - resp: `{repr((e['resp'] or '')[:180])[1:-1]}`")
open("/home/paperspace/marin/repro-olmo3-safety/report/failure_examples_expanded.md", "w").write("\n".join(out))
# summary counts to stdout
print("MARIN failures by category:", {c: len(v) for c, v in failures_by_cat(M, O).items()})
print("OLMO  failures by category:", {c: len(v) for c, v in failures_by_cat(O, M).items()})
print("wrote report/failure_examples_expanded.md")
