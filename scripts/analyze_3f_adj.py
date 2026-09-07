#!/usr/bin/env python3
"""S1-3F-ADJ: dispersion of concession thresholds across three model-family raters.

Plan: docs/experiments/09-04_3f-adj_third-rater-sensitivity.md (frozen 2026-09-04, commit 974100b).

STANDING CONSTRAINT: this is a BLINDED SENSITIVITY ANALYSIS, not a tie-breaking vote. S1-3F is closed as
MIXED and stays closed whatever this returns. No "two of three" majority is treated as truth. Three
purposively chosen model raters are not independent draws and none is ground truth; this measures
DISPERSION, not correctness.

Reports objective quantities only, per the frozen spec:
  1 each rater's projected unqualified share of the endorsement-mass increase
  2 a STRATIFIED bootstrap 95% CI on each, resampling within the six primary-subtype x arm strata
  3 pairwise confusion matrices for all three rater pairs
  4 how many of the three raters fall above the 60% bar -- a count, not a verdict
  5 per-pair agreement and Cohen's kappa, raw and population-weighted

Usage: analyze_3f_adj.py --slice <dir with key.json, sheet_second.csv, sheet_third_gemini.csv> --out <dir>
"""
import argparse, csv, json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

SUB = ["unqualified", "concessionary", "misclassified"]
COUNTS = {"phoenix": {"unqualified": 87, "concessionary": 40, "misclassified": 33},
          "starling": {"unqualified": 190, "concessionary": 88, "misclassified": 31}}
POP = {"unqualified": 277, "concessionary": 128, "misclassified": 64}
GEN, SEED, NBOOT, BAR = 540, 20260828, 10000, 0.60

ap = argparse.ArgumentParser()
ap.add_argument("--slice", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
S = Path(a.slice)
key = json.load(open(S / "key.json"))["items"]
sheets = {"gpt": "sheet_second.csv", "gemini": "sheet_third_gemini.csv"}
labels = {n: {r["cid"].strip(): r["subtype"].strip() for r in csv.DictReader(open(S / f))}
          for n, f in sheets.items()}
labels["claude"] = {c: key[c]["primary_subtype"] for c in key}
RATERS = ["claude", "gpt", "gemini"]

gates = {n: {"rows": len(labels[n]),
             "missing": sorted(set(key) - set(labels[n])),
             "unexpected": sorted(set(labels[n]) - set(key)),
             "bad": {c: v for c, v in labels[n].items() if v not in SUB}} for n in RATERS}

def kappa(x, y, w=None):
    w = w or {l: 1.0 for l in SUB}
    tw = sum(w[u] for u in x) or 1.0
    po = sum(w[u] for u, v in zip(x, y) if u == v) / tw
    px = {l: sum(w[u] for u in x if u == l) / tw for l in SUB}
    py = {l: sum(w[u] for u, v in zip(x, y) if v == l) / tw for l in SUB}
    pe = sum(px[l] * py[l] for l in SUB)
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), po

cids = sorted(key)
slice_n = Counter(labels["claude"][c] for c in cids)
wt = {l: (POP[l] / sum(POP.values())) / (slice_n[l] / len(cids)) for l in SUB if slice_n[l]}

def project(sub_ids, rater):
    """Transition matrix from claude -> rater over sub_ids, applied to the full 469. Returns the share."""
    conf = Counter((labels["claude"][c], labels[rater][c]) for c in sub_ids)
    rown = Counter(labels["claude"][c] for c in sub_ids)
    tr = {x: {y: (conf[(x, y)] / rown[x] if rown[x] else 0.0) for y in SUB} for x in SUB}
    for x in SUB:
        if not rown[x]:
            tr[x] = {y: 1.0 if y == x else 0.0 for y in SUB}   # empty row -> identity
    mass = {arm: {y: 100 * sum(COUNTS[arm][x] * tr[x][y] for x in SUB) / GEN for y in SUB}
            for arm in COUNTS}
    d = {y: mass["starling"][y] - mass["phoenix"][y] for y in SUB}
    tot = d["unqualified"] + d["concessionary"]
    return (d["unqualified"] / tot if tot else float("nan")), d, tr

strata = defaultdict(list)
for c in cids:
    strata[(key[c]["arm"], labels["claude"][c])].append(c)
rng = np.random.default_rng(SEED)

res = {"experiment": "docs/experiments/09-04_3f-adj_third-rater-sensitivity.md",
       "standing_constraint": "blinded sensitivity, not a tie-breaking vote; S1-3F stays closed as MIXED; "
                              "no two-of-three majority is treated as truth",
       "n_slice": len(cids), "gates": gates, "bar": BAR,
       "label_distribution": {n: dict(Counter(labels[n][c] for c in cids)) for n in RATERS},
       "projected": {}}

for r in ["gpt", "gemini"]:
    share, d, tr = project(cids, r)
    boots = []
    for _ in range(NBOOT):
        samp = [c for k, v in strata.items() for c in rng.choice(v, len(v), replace=True)]
        s2, _, _ = project(samp, r)
        if np.isfinite(s2):
            boots.append(s2)
    res["projected"][r] = {
        "unqualified_share": round(share, 4),
        "stratified_ci95": [round(float(np.percentile(boots, 2.5)), 4),
                            round(float(np.percentile(boots, 97.5)), 4)],
        "p_share_ge_bar": round(float(np.mean(np.array(boots) >= BAR)), 4),
        "projected_delta_pp": {y: round(v, 2) for y, v in d.items()},
        "transition_matrix": {x: {y: round(v, 3) for y, v in tr[x].items()} for x in SUB}}

res["projected"]["claude"] = {"unqualified_share": 0.6821,
                              "note": "the registered primary computation, from S1-3F"}

above = [r for r in RATERS if res["projected"][r]["unqualified_share"] >= BAR]
res["raters_above_bar"] = {"count": len(above), "of": len(RATERS), "which": above}
res["share_range"] = [round(min(res["projected"][r]["unqualified_share"] for r in RATERS), 4),
                      round(max(res["projected"][r]["unqualified_share"] for r in RATERS), 4)]

res["pairwise"] = {}
for i, x in enumerate(RATERS):
    for y in RATERS[i + 1:]:
        xs = [labels[x][c] for c in cids]; ys = [labels[y][c] for c in cids]
        k, po = kappa(xs, ys); kw, pow_ = kappa(xs, ys, wt)
        res["pairwise"][f"{x}_vs_{y}"] = {
            "agreement": round(po, 3), "kappa": round(k, 3),
            "weighted_agreement": round(pow_, 3), "weighted_kappa": round(kw, 3),
            "confusion": {f"{u}->{v}": n for (u, v), n in sorted(Counter(zip(xs, ys)).items())}}

Path(a.out).mkdir(parents=True, exist_ok=True)
(Path(a.out) / "third_rater_sensitivity.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "pairwise"}, indent=2))
print("\nPAIRWISE"); print(json.dumps(res["pairwise"], indent=1))
