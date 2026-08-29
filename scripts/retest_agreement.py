#!/usr/bin/env python3
"""Test-retest reliability of the blind rubric annotator, pass 1 vs pass 2.

The two passes sharded the same 1,080 items differently, so every item common to both was
labelled twice by independent annotator instances that never saw each other's work. Agreement
between them estimates rater reliability on THIS data, which is a stronger estimate than the
150-item calibration set gave.

Reports overall, and broken down by checkpoint. The breakdown is the one that matters for the
decomposition: if reliability differs between Phoenix and Starling, a paired difference computed
from these labels carries rater noise that is not symmetric across the contrast.

`--key` is used ONLY here, at analysis time, after both passes are locked. Annotators never see it.

Usage:
  retest_agreement.py --pass1 <dir> --pass2 <dir> --key key.json --out <file.json>
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rubric_lib as R

ap = argparse.ArgumentParser()
ap.add_argument("--pass1", required=True, help="dir of pass-1 sheet_part*.csv")
ap.add_argument("--pass2", required=True, help="dir of pass-2 sheet_part*.csv")
ap.add_argument("--key", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--tags", nargs=2, default=["phoenix", "starling"])
a = ap.parse_args()

A = R.load_sheets(sorted(Path(a.pass1).glob("sheet_part*.csv")))
B = R.load_sheets(sorted(Path(a.pass2).glob("sheet_part*.csv")))
key = json.load(open(a.key))["items"]

both = sorted(set(A) & set(B))
if not both:
    sys.exit("FAIL no cids in common between the two passes")


def tag_of(cid):
    run = key[cid]["run"]
    for t in a.tags:
        if f"-{t}-" in run:
            return t
    return None


def block(cids, label):
    out = {"label": label, "n": len(cids)}
    if not cids:
        return out
    for dim in ("relevance", "task", "stance"):
        out[dim] = R.agreement([A[c][dim].strip() for c in cids], [B[c][dim].strip() for c in cids])
    x = [R.category6(A[c]) for c in cids]
    y = [R.category6(B[c]) for c in cids]
    out["derived6"] = R.agreement(x, y)
    out["derived6"]["pass1_counts"] = dict(Counter(x))
    out["derived6"]["pass2_counts"] = dict(Counter(y))
    out["derived3"] = R.agreement([R.collapse3(v) for v in x], [R.collapse3(v) for v in y])
    q = [(R.quality_mean(A[c]), R.quality_mean(B[c])) for c in cids]
    q = [(p, r) for p, r in q if p is not None and r is not None]
    if len(q) >= 10:
        out["quality"] = {
            "n_both_scored": len(q),
            "spearman_tie_aware": round(R.spearman([p for p, _ in q], [r for _, r in q]), 3),
            "mean_abs_diff": round(sum(abs(p - r) for p, r in q) / len(q), 2),
            "pass1_mean": round(sum(p for p, _ in q) / len(q), 2),
            "pass2_mean": round(sum(r for _, r in q) / len(q), 2),
        }
    return out


res = {
    "pass1_dir": a.pass1, "pass2_dir": a.pass2,
    "n_pass1": len(A), "n_pass2": len(B), "n_common": len(both),
    "coverage_note": (
        f"{len(both)} of {len(key)} items labelled in both passes; agreement is estimated on those only"
    ),
    "overall": block(both, "overall"),
}
for t in a.tags:
    res[t] = block([c for c in both if tag_of(c) == t], t)

# The load-bearing comparison: does either pass see the same checkpoint difference?
def cat_mass(rows, cids):
    c = Counter(R.category6(rows[i]) for i in cids)
    n = len(cids)
    return {k: round(c.get(k, 0) / n, 4) for k in R.CATS6}


t0, t1 = a.tags
c0 = [c for c in both if tag_of(c) == t0]
c1 = [c for c in both if tag_of(c) == t1]
if c0 and c1:
    res["pooled_mass_delta_by_pass"] = {
        "note": (
            "Pooled item-level mass difference (starling - phoenix) per category, computed "
            "separately from each pass's labels. NOT the pre-registered statistic (which is "
            "behavior-level with a bootstrap CI); this is a rater-robustness check only. "
            "If the two passes disagree on the SIGN of a category, that category is not "
            "safely measurable with this rater."
        ),
        "pass1": {k: round(cat_mass(A, c1)[k] - cat_mass(A, c0)[k], 4) for k in R.CATS6},
        "pass2": {k: round(cat_mass(B, c1)[k] - cat_mass(B, c0)[k], 4) for k in R.CATS6},
    }
    p1, p2 = res["pooled_mass_delta_by_pass"]["pass1"], res["pooled_mass_delta_by_pass"]["pass2"]
    res["pooled_mass_delta_by_pass"]["sign_disagreements"] = [
        k for k in R.CATS6 if p1[k] * p2[k] < 0
    ]

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps(res, indent=1))
