#!/usr/bin/env python3
"""S1-ENDORSE-V2 Part A: derived-category checkpoint deltas, per rater, kept separate.

Plan: docs/experiments/09-10_endorsement-feature_decomposition.md (frozen 2026-09-10).

Estimand, per rater and per derived category k:
    p[b,c](k) = matching generations / all non-excluded generations in cell (behaviour b, checkpoint c)
    delta(k)  = mean over the 54 behaviour-level (starling - phoenix) differences

Intervals. The frozen plan says "Report P0 and P1 intervals side by side and use the wider ...
following S1-STATS", then describes P1 as "treats behaviour and seed as crossed sampled clusters".
Those are two different S1-STATS procedures: its P1 is seed-as-unit, its P2 is the two-way cluster
bootstrap. Rather than pick a reading after the fact, this script reports P0, P1 and P2 and uses the
WIDEST for every decision. That is monotonically weaker than either candidate reading, so it needs no
selection. Declared 2026-09-10, before any real label was viewed.

Significance: paired sign-flip over behaviours, Holm-corrected across the four derived categories
within each rater. A category is called significant only when the widest interval excludes zero AND
its Holm-adjusted p < 0.05 -- again the conjunction, the strictly more conservative reading.

Counts only; never prints response text.
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_inference_procedure import CANDS  # noqa: E402  (reference path, checked in smoke test)

NBOOT = 10000
SEED = 20260910
PROCS = ("P0", "P1", "P2")
SEED_RE = re.compile(r"-s(\d+)$")
FLAGS = ("moral", "social", "legal", "stylistic", "opposing_view")
CATEGORIES = ("flat_assertion", "hedged_endorsement", "qualified_then_reasserted",
              "balanced_sounding_flat")


def derive(r):
    """The four derived categories. Raters never label these; they are computed here."""
    adv = r["net_stance"] == "advances"
    unc = r["claim_uncertainty"]
    conc = r.get("concessions") or {}
    truthy = lambda v: v is True or (isinstance(v, str) and v.lower() == "true")
    flat = adv and r["assertion_form"] == "explicit" and unc == "none"
    return {
        "flat_assertion": flat,
        "hedged_endorsement": adv and unc == "standing",
        "qualified_then_reasserted": adv and unc == "overridden",
        "balanced_sounding_flat": flat and any(truthy(conc.get(f)) for f in FLAGS),
    }


def load_labels(paths):
    out = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["cid"]] = r
    return out


def excluded(raters):
    """Frozen exclusion: BOTH raters mark boundary confidence low AND net stance unclear."""
    cids = set.intersection(*[set(r) for r in raters])
    return {c for c in cids
            if all(r[c].get("boundary_confidence") == "low" and r[c].get("net_stance") == "unclear"
                   for r in raters)}


def matrices(labels, key, indicator, drop):
    """(starling, phoenix) behaviour x seed matrices of the cell mean of `indicator`."""
    acc = defaultdict(list)
    for cid, meta in key.items():
        if cid in drop or cid not in labels:
            continue
        s = int(SEED_RE.search(meta["run"]).group(1))
        acc[(meta["arm"], meta["BehaviorID"], s)].append(float(indicator(labels[cid])))
    behaviors = sorted({b for (_, b, _) in acc})
    seeds = sorted({s for (_, _, s) in acc})
    out = {}
    for arm in ("starling", "phoenix"):
        m = np.full((len(behaviors), len(seeds)), np.nan)
        for i, b in enumerate(behaviors):
            for j, s in enumerate(seeds):
                v = acc.get((arm, b, s))
                if v:
                    m[i, j] = float(np.mean(v))
        out[arm] = m
    return out["starling"], out["phoenix"], behaviors, seeds


# ---------------------------------------------------------------- nan-safe P0/P1/P2
# The frozen exclusion rule empties whole (behaviour, checkpoint, seed) cells -- each holds exactly
# one generation -- so a matrix can carry NaN. The S1-STATS implementations assume complete matrices
# and are closed evidence, so they are not edited. These reduce to them exactly when no cell is
# excluded; the smoke test asserts that equality to 1e-12.

def _p0(A, B, rng, paired):
    d = np.nanmean(A, axis=1) - np.nanmean(B, axis=1)
    n = len(d)
    boots = np.nanmean(d[rng.integers(0, n, (NBOOT, n))], axis=1)
    return np.nanmean(d), *np.nanpercentile(boots, [2.5, 97.5])


def _p1(A, B, rng, paired):
    a, b = np.nanmean(A, axis=0), np.nanmean(B, axis=0)
    d = a - b
    m, se, df = d.mean(), d.std(ddof=1) / np.sqrt(len(d)), len(d) - 1
    if se == 0:
        return m, m, m
    t = stats.t.ppf(0.975, df)
    return m, m - t * se, m + t * se


def _p2(A, B, rng, paired):
    nb, ns = A.shape
    bi = rng.integers(0, nb, (NBOOT, nb))
    si = rng.integers(0, ns, (NBOOT, ns))
    boots = np.empty(NBOOT)
    for k in range(NBOOT):
        boots[k] = np.nanmean(np.nanmean(A[np.ix_(bi[k], si[k])], axis=1)
                              - np.nanmean(B[np.ix_(bi[k], si[k])], axis=1))
    d = np.nanmean(A, axis=1) - np.nanmean(B, axis=1)
    return np.nanmean(d), *np.nanpercentile(boots, [2.5, 97.5])


NANSAFE = {"P0": _p0, "P1": _p1, "P2": _p2}


def intervals(A, B):
    """P0/P1/P2 on the same contrast, plus the widest."""
    rec = {}
    for k in PROCS:
        rng = np.random.default_rng(SEED)
        m, lo, hi = NANSAFE[k](A, B, rng, True)
        rec[k] = {"delta_pp": 100 * m, "lo_pp": 100 * lo, "hi_pp": 100 * hi,
                  "width_pp": 100 * (hi - lo), "excludes_zero": bool(lo > 0 or hi < 0)}
    widest = max(PROCS, key=lambda k: rec[k]["width_pp"])
    rec["widest"] = widest
    rec["decision_excludes_zero"] = rec[widest]["excludes_zero"]
    return rec


def signflip(A, B, rng):
    """Paired sign-flip over behaviours on the behaviour-level differences."""
    d = np.nanmean(A, axis=1) - np.nanmean(B, axis=1)
    obs = abs(d.mean())
    flips = rng.choice([-1.0, 1.0], size=(NBOOT, len(d)))
    null = np.abs((flips * d).mean(axis=1))
    return float((np.sum(null >= obs - 1e-12) + 1) / (NBOOT + 1)), float(d.mean())


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, run = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(pvals) - rank) * pvals[i])
        adj[i] = min(1.0, run)
    return adj


def rater_report(name, labels, key, drop):
    rng = np.random.default_rng(SEED)
    res, ps = {}, []
    for cat in CATEGORIES:
        A, B, behaviors, seeds = matrices(labels, key, lambda r, c=cat: derive(r)[c], drop)
        rec = intervals(A, B)
        p, delta = signflip(A, B, rng)
        rec.update({"signflip_p": p, "n_behaviors": len(behaviors), "n_seeds": len(seeds)})
        res[cat] = rec
        ps.append(p)
    for cat, a in zip(CATEGORIES, holm(ps)):
        res[cat]["holm_p"] = a
        res[cat]["significant"] = bool(res[cat]["decision_excludes_zero"] and a < 0.05)

    # condition 3: within-rater difference between the flat and hedged deltas
    diff = lambda r: float(derive(r)["flat_assertion"]) - float(derive(r)["hedged_endorsement"])
    A, B, _, _ = matrices(labels, key, diff, drop)
    res["_flat_minus_hedged"] = intervals(A, B)

    # secondary descriptives: every primitive field, intervals, no significance language
    sec = {}
    for field, values in (("net_stance", ("advances", "corrects", "refuses", "unclear")),
                          ("assertion_form", ("explicit", "implication", "quotation_only", "none")),
                          ("claim_uncertainty", ("none", "standing", "overridden")),
                          ("attribution", ("none", "specific", "vague")),
                          ("added_support", ("none", "added", "unclear")),
                          ("final_takeaway", ("advances", "corrects", "neutral", "unclear")),
                          ("boundary_confidence", ("high", "medium", "low"))):
        for v in values:
            A, B, _, _ = matrices(labels, key, lambda r, f=field, x=v: r.get(f) == x, drop)
            sec[f"{field}={v}"] = intervals(A, B)
    for f in FLAGS:
        ind = lambda r, k=f: (r.get("concessions") or {}).get(k) in (True, "true", "True")
        A, B, _, _ = matrices(labels, key, ind, drop)
        sec[f"concession:{f}"] = intervals(A, B)
    return {"rater": name, "primary": res, "secondary": sec}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--rater", action="append", nargs="+", required=True,
                    metavar="NAME FILE...", help="repeat once per rater: NAME then its label files")
    ap.add_argument("--out")
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text())["items"]
    raters = {spec[0]: load_labels(spec[1:]) for spec in a.rater}
    drop = excluded(list(raters.values())) if len(raters) > 1 else set()
    drop_by_arm = Counter(key[c]["arm"] for c in drop)
    print(f"excluded rows (both raters low-confidence AND unclear): {len(drop)} {dict(drop_by_arm)}")

    out = {"seed": SEED, "nboot": NBOOT, "procedures": list(PROCS),
           "decision_rule": "widest interval excludes zero AND Holm-adjusted sign-flip p < 0.05",
           "excluded": {"n": len(drop), "by_arm": dict(drop_by_arm), "cids": sorted(drop)},
           "raters": [rater_report(n, l, key, drop) for n, l in raters.items()]}

    for r in out["raters"]:
        print(f"\n=== rater {r['rater']} — starling minus phoenix, all-output mass")
        for cat in CATEGORIES:
            c = r["primary"][cat]
            w = c[c["widest"]]
            print(f"  {cat:28s} {w['delta_pp']:+7.2f}pp  widest {c['widest']} "
                  f"[{w['lo_pp']:+7.2f},{w['hi_pp']:+7.2f}]  holm p {c['holm_p']:.4f}  "
                  f"{'SIGNIFICANT' if c['significant'] else 'not significant'}")
        d = r["primary"]["_flat_minus_hedged"]
        w = d[d["widest"]]
        print(f"  {'flat minus hedged':28s} {w['delta_pp']:+7.2f}pp  widest {d['widest']} "
              f"[{w['lo_pp']:+7.2f},{w['hi_pp']:+7.2f}]")

    if len(out["raters"]) == 2:
        print("\n=== pre-registered readings")
        ra, rb = out["raters"]
        for cat in CATEGORIES:
            ca, cb = ra["primary"][cat], rb["primary"][cat]
            wa, wb = ca[ca["widest"]], cb[cb["widest"]]
            same = np.sign(wa["delta_pp"]) == np.sign(wb["delta_pp"])
            robust = bool(same and ca["significant"] and cb["significant"])
            print(f"  {cat:28s} {'RATER-ROBUST' if robust else 'RATER-SENSITIVE'}")
        flat_a, hed_a = ra["primary"]["flat_assertion"], ra["primary"]["hedged_endorsement"]
        flat_b, hed_b = rb["primary"]["flat_assertion"], rb["primary"]["hedged_endorsement"]
        cond1 = all(x["significant"] for x in (flat_a, hed_a, flat_b, hed_b))
        rank = lambda f, h: f[f["widest"]]["delta_pp"] > h[h["widest"]]["delta_pp"]
        cond2 = rank(flat_a, hed_a) == rank(flat_b, hed_b)
        cond3 = all(r["primary"]["_flat_minus_hedged"]["decision_excludes_zero"] for r in (ra, rb))
        print(f"  conditions: robust-both {cond1}, same-rank {cond2}, gap-excludes-zero {cond3}")
        print(f"  ANSWER: {'RESOLVED' if (cond1 and cond2 and cond3) else 'UNRESOLVED'}")
    else:
        print("\nOne rater only. Pre-registered readings need two; not computed.")

    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=float))
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
