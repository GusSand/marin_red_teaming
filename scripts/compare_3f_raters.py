#!/usr/bin/env python3
"""S1-3F second-rater agreement (experiment 09-04, IN-004).

Compares the second frontier rater's labels on the 150-item slice against the primary Claude subtypes.
Pre-registered thresholds: three-subtype kappa < 0.50 -> POOR, weakens the stance-shift claim;
0.50-0.60, or three-way agreement < 0.75, -> MODERATE, reported with the caveat quoted; otherwise
ADEQUATE. The `concessionary` vs `misclassified` boundary is called out explicitly, because the internal
duplicate check produced zero such pairs and this slice is the only instrument for it.

IMPORTANT: the slice is stratified EQUALLY by primary subtype (25 per subtype per arm), so these
agreement figures are a BOUNDARY TEST on a balanced design, not a population agreement estimate. A
population-weighted kappa is reported alongside, reweighting each primary class to its share of the 469.

Labels only; no response text. CPU, seconds.

Usage: compare_3f_raters.py --slice <concessionary_second_rater_v1> --out <dir>
"""
import argparse, csv, json
from collections import Counter
from pathlib import Path

SUB = ["unqualified", "concessionary", "misclassified"]
ap = argparse.ArgumentParser()
ap.add_argument("--slice", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
S = Path(a.slice)

key = json.load(open(S / "key.json"))["items"]
second = {r["cid"].strip(): r["subtype"].strip() for r in csv.DictReader(open(S / "sheet_second.csv"))}

gates = {"n_key": len(key), "n_second": len(second),
         "missing": sorted(set(key) - set(second)), "unexpected": sorted(set(second) - set(key)),
         "bad_labels": {c: v for c, v in second.items() if v not in SUB}}

pairs = [(key[c]["primary_subtype"], second[c], key[c]["arm"]) for c in sorted(key) if c in second]
A = [p for p, _, _ in pairs]; B = [b for _, b, _ in pairs]
n = len(pairs)

def kappa(x, y, w=None):
    labs = SUB
    w = w or {l: 1.0 for l in labs}
    tw = sum(w[l] for l in x) or 1.0
    po = sum(w[u] for u, v in zip(x, y) if u == v) / tw
    px = {l: sum(w[u] for u in x if u == l) / tw for l in labs}
    py = {l: sum(w[xx] for xx, v in zip(x, y) if v == l) / tw for l in labs}
    pe = sum(px[l] * py[l] for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan"), po

k, po = kappa(A, B)
conf = Counter(zip(A, B))

# population reweighting: the slice is balanced by design, the 469 are not
POP = {"unqualified": 277, "concessionary": 128, "misclassified": 64}   # 87+190, 40+88, 33+31
slice_n = Counter(A)
w = {l: (POP[l] / sum(POP.values())) / (slice_n[l] / n) for l in SUB if slice_n[l]}
kw, pow_ = kappa(A, B, w)

res = {"experiment": "docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md",
       "inbox": "IN-004", "n": n, "gates": gates,
       "second_rater_distribution": dict(Counter(B)),
       "primary_distribution_in_slice": dict(slice_n),
       "three_subtype_agreement": round(po, 3),
       "cohens_kappa": round(k, 3),
       "population_weighted_agreement": round(pow_, 3),
       "population_weighted_kappa": round(kw, 3),
       "confusion_primary_to_second": {f"{x}->{y}": c for (x, y), c in sorted(conf.items())},
       "per_class": {l: {"primary_n": slice_n[l], "second_n": Counter(B)[l],
                         "both": conf[(l, l)],
                         "recall_primary": round(conf[(l, l)] / slice_n[l], 3) if slice_n[l] else None,
                         "precision_second": round(conf[(l, l)] / Counter(B)[l], 3) if Counter(B)[l] else None}
                     for l in SUB}}

# the boundary the decision turns on
cm = conf[("concessionary", "misclassified")] + conf[("misclassified", "concessionary")]
res["concessionary_vs_misclassified"] = {
    "cross_count": cm,
    "conc->misc": conf[("concessionary", "misclassified")],
    "misc->conc": conf[("misclassified", "concessionary")],
    "note": "the internal duplicate check produced ZERO such pairs; this slice is the only measurement"}

# per-arm
res["by_arm"] = {}
for arm in ("phoenix", "starling"):
    sub = [(x, y) for x, y, t in pairs if t == arm]
    kk, pp = kappa([x for x, _ in sub], [y for _, y in sub])
    res["by_arm"][arm] = {"n": len(sub), "agreement": round(pp, 3), "kappa": round(kk, 3)}

# ---- POST-HOC sensitivity: would the verdict survive the second rater's labels? ----------------
# Agreement being adequate is not the same as the verdict being robust. The disagreement here is
# DIRECTIONAL -- the second rater moves items from `unqualified` to `concessionary` -- and the frozen
# verdict rests on unqualified holding >= 60% of the endorsement-mass increase. Apply the observed
# per-class transition rates to the full 469 and recompute the share. Clearly post hoc; it does not
# replace the registered verdict, which is computed on the primary labels.
trans = {x: {y: conf[(x, y)] / slice_n[x] for y in SUB} for x in SUB if slice_n[x]}
COUNTS = {"phoenix": {"unqualified": 87, "concessionary": 40, "misclassified": 33},
          "starling": {"unqualified": 190, "concessionary": 88, "misclassified": 31}}
GEN = 540  # generations per arm: 54 behaviours x 10 seeds
proj = {arm: {y: sum(COUNTS[arm][x] * trans[x][y] for x in SUB) for y in SUB} for arm in COUNTS}
mass = {arm: {y: 100 * proj[arm][y] / GEN for y in SUB} for arm in proj}
d = {y: mass["starling"][y] - mass["phoenix"][y] for y in SUB}
tot2 = d["unqualified"] + d["concessionary"]
share_u = d["unqualified"] / tot2 if tot2 else float("nan")
if d["unqualified"] > d["concessionary"] and share_u >= 0.60:
    proj_verdict = "MAINLY UNQUALIFIED"
elif d["concessionary"] > d["unqualified"] and (1 - share_u) >= 0.60:
    proj_verdict = "MAINLY CONCESSIONARY"
else:
    proj_verdict = "MIXED"
res["posthoc_sensitivity_under_second_rater"] = {
    "note": "POST HOC. Observed per-class transition rates applied to the full 469. Does not replace "
            "the registered verdict, which stands on the primary labels.",
    "transition_rates_primary_to_second": {x: {y: round(v, 3) for y, v in trans[x].items()} for x in trans},
    "projected_counts": {a: {y: round(v, 1) for y, v in proj[a].items()} for a in proj},
    "projected_mass_pct": {a: {y: round(v, 2) for y, v in mass[a].items()} for a in mass},
    "projected_delta_pp": {y: round(v, 2) for y, v in d.items()},
    "projected_unqualified_share_of_increase": round(share_u, 4),
    "projected_verdict": proj_verdict,
    "registered_verdict_robust_to_second_rater": proj_verdict == "MAINLY UNQUALIFIED"}

if k < 0.50:
    verdict = "POOR — weakens the stance-shift claim per the frozen rule"
elif k < 0.60 or po < 0.75:
    verdict = "MODERATE — reported with the caveat quoted"
else:
    verdict = "ADEQUATE"
res["verdict"] = verdict

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "second_rater_agreement.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
