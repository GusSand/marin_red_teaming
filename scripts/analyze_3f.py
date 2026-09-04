#!/usr/bin/env python3
"""S1-3F: is Starling's endorsement gain unqualified or concessionary?

Pre-registration: docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md (frozen
2026-09-04, commit 6821ed7). POST HOC. Additive sub-rubric over the pass-2 `endorses` items only.

Denominator is ALL of a behaviour's generations, not just its endorsements, so the three subtype masses
sum to the endorsement mass and are commensurable with step 3's -12.2 / -12.2 / +28.5pp.

  p_hat[b,c](k) = (generations of b at c that are endorses AND subtype k) / (all generations of b at c)

Primary: mean over all 54 behaviours of p_hat[b,starling] - p_hat[b,phoenix] per subtype, behaviour
bootstrap 95% CI (10k, seed 20260828), sign-flip permutation p, Holm over the three subtypes.
Mass change only -- never a flow.

Aggregate counts only; never reads or prints response text.

Usage: analyze_3f.py --sample <concessionary_v1> --rater <dir of sheet_part*.csv>
                     --full <full_phoenix_starling_v1> --out <dir>
"""
import argparse, csv, json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

SEED, NBOOT = 20260828, 10000
SUBTYPES = ["unqualified", "concessionary", "misclassified"]

ap = argparse.ArgumentParser()
for f in ("sample", "rater", "full", "out"):
    ap.add_argument(f"--{f}", required=True)
a = ap.parse_args()

key = json.load(open(Path(a.sample) / "key.json"))["items"]
prov = json.load(open(Path(a.sample) / "provenance.json"))
fullkey = json.load(open(Path(a.full) / "key.json"))["items"]
J = {json.loads(l)["cid"]: json.loads(l)
     for l in (Path(a.full) / "judge" / "claude_fable_pass2.jsonl").read_text().splitlines() if l.strip()}

rows, dupes = {}, []
for p in sorted(Path(a.rater).glob("sheet_part*.csv")):
    for r in csv.DictReader(open(p)):
        cid = r["cid"].strip()
        (dupes.append(cid) if cid in rows else None)
        rows[cid] = {"subtype": r["subtype"].strip(), "notes": r.get("notes", "").strip(), "sheet": p.name}

gates = {"n_rated": len(rows), "expected": len(key), "duplicate_cids_in_sheets": dupes,
         "missing": sorted(set(key) - set(rows)), "unexpected": sorted(set(rows) - set(key)),
         "bad_labels": {c: v["subtype"] for c, v in rows.items() if v["subtype"] not in SUBTYPES},
         "universe_endorses": prov["universe_endorses"],
         "worst_shard_deviation_from_universe_pp": prov["worst_shard_deviation_from_universe_pp"]}

# ---- within-rater duplicate agreement ----------------------------------------------------------
by_src = defaultdict(list)
for cid, v in rows.items():
    if cid in key:
        by_src[key[cid]["i_cid"]].append((cid, v["subtype"], key[cid]["part"]))
pairs = [l for l in by_src.values() if len(l) == 2]
def kappa(xs, ys):
    labs = sorted(set(xs) | set(ys)); n = len(xs)
    po = sum(u == v for u, v in zip(xs, ys)) / n
    pe = sum((xs.count(l) / n) * (ys.count(l) / n) for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")
ag = sum(1 for l in pairs if l[0][1] == l[1][1])
dup = {"n_pairs": len(pairs), "agree": ag,
       "agreement": round(ag / len(pairs), 3) if pairs else None,
       "kappa": round(kappa([l[0][1] for l in pairs], [l[1][1] for l in pairs]), 3) if pairs else None,
       "pairs_in_same_shard": sum(1 for l in pairs if l[0][2] == l[1][2]),
       "pair_label_composition": dict(Counter(tuple(sorted((l[0][1], l[1][1]))) for l in pairs).items()),
       "confusion": {f"{x}->{y}": n for (x, y), n in
                     Counter((l[0][1], l[1][1]) for l in pairs).items() if x != y}}
dup["pair_label_composition"] = {f"{x}|{y}": n for (x, y), n in
                                 Counter(tuple(sorted((l[0][1], l[1][1]))) for l in pairs).items()}

# one label per source item: first-sorting rater cid
first = {}
for cid in sorted(rows):
    if cid in key:
        first.setdefault(key[cid]["i_cid"], rows[cid]["subtype"])

# ---- masses over ALL generations of each behaviour/arm ------------------------------------------
import re
def arm(run):
    for t in ("phoenix", "starling"):
        if re.search(rf"-{t}-", run):
            return t
total = Counter()                                   # (arm, behaviour) -> all generations
for c, k in fullkey.items():
    total[(arm(k["run"]), k["BehaviorID"])] += 1
hit = Counter()                                     # (arm, behaviour, subtype) -> count
for icid, st in first.items():
    k = fullkey[icid]
    hit[(arm(k["run"]), k["BehaviorID"], st)] += 1

behs = sorted({b for (_, b) in total})
paired = [b for b in behs if total[("phoenix", b)] and total[("starling", b)]]

def mass(t, b, st):
    return hit[(t, b, st)] / total[(t, b)] if total[(t, b)] else 0.0

rng = np.random.default_rng(SEED)
idx = np.arange(len(paired))
boot_idx = rng.integers(0, len(paired), (NBOOT, len(paired)))
perm_signs = np.random.default_rng(SEED + 1).choice([-1, 1], (NBOOT, len(paired)))

primary, raw_p = {}, {}
for st in SUBTYPES:
    d = np.array([mass("starling", b, st) - mass("phoenix", b, st) for b in paired])
    est = float(d.mean() * 100)
    bs = d[boot_idx].mean(axis=1) * 100
    ci = [round(float(np.percentile(bs, 2.5)), 2), round(float(np.percentile(bs, 97.5)), 2)]
    null = (perm_signs * d).mean(axis=1) * 100
    p = float((np.abs(null) >= abs(est)).mean())
    primary[st] = {"phoenix_mass_pct": round(100 * float(np.mean([mass("phoenix", b, st) for b in paired])), 2),
                   "starling_mass_pct": round(100 * float(np.mean([mass("starling", b, st) for b in paired])), 2),
                   "delta_pp": round(est, 2), "ci95_pp": ci, "perm_p": round(p, 4)}
    raw_p[st] = p

# Holm over the three subtypes
order = sorted(raw_p, key=raw_p.get)
adj, prev = {}, 0.0
for i, st in enumerate(order):
    v = max(prev, min(1.0, raw_p[st] * (len(order) - i)))
    adj[st] = round(v, 4); prev = v
for st in SUBTYPES:
    primary[st]["holm_p"] = adj[st]

res = {"experiment": "docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md",
       "post_hoc": True, "seed": SEED, "nboot": NBOOT,
       "n_paired_behaviors": len(paired), "n_behaviors_total": len(behs),
       "gates": gates, "duplicates": dup,
       "counts_by_arm": {t: dict(Counter(st for i, st in first.items() if arm(fullkey[i]["run"]) == t))
                         for t in ("phoenix", "starling")},
       "primary": primary}

d_u, d_c = primary["unqualified"]["delta_pp"], primary["concessionary"]["delta_pp"]
tot = d_u + d_c
def material(st):
    v = primary[st]; return (v["ci95_pp"][0] > 0 or v["ci95_pp"][1] < 0)
if tot > 0 and d_u > d_c and material("unqualified") and d_u >= 0.60 * tot:
    verdict = "MAINLY UNQUALIFIED — retain the stronger endorsement reading"
elif tot > 0 and d_c > d_u and material("concessionary") and d_c >= 0.60 * tot:
    verdict = "MAINLY CONCESSIONARY — increased willingness to supply the thesis despite concessions"
else:
    verdict = "MIXED — neither component reaches 60% of the endorsement-mass increase"
res["verdict"] = verdict

mis = res["counts_by_arm"]
share = {t: round(100 * mis[t].get("misclassified", 0) / max(sum(mis[t].values()), 1), 2)
         for t in ("phoenix", "starling")}
res["misclassified_share_pct_of_endorsements"] = share
res["misclassified_material"] = bool(max(share.values()) >= 10.0)

res["iron_law_tripped"] = bool(
    (dup["agreement"] == 1.0 if dup["agreement"] is not None else False)
    or any(max(v.values()) / max(sum(v.values()), 1) > 0.95 for v in mis.values() if v))

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "concessionary.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps(res, indent=2))
