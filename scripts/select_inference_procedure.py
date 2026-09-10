#!/usr/bin/env python3
"""S1-STATS: select a calibrated interval procedure. Plan frozen 2026-09-09, commit bc0a32e.

docs/experiments/09-09_inference-procedure_recalibration.md

Four candidates, evaluated by the false-positive rate they produce on splits of a tag against
ITSELF, where the true difference is zero by construction:

  P0  incumbent -- percentile bootstrap over BEHAVIOURS, conditioning on the seed draw.
      Carried as the reference line only; not eligible to win.
  P1  seed as the unit -- t interval over per-seed rates (paired when the two seed sets are
      identical, Welch when they are disjoint).
  P2  two-way cluster bootstrap -- resample behaviours AND seeds, recompute the contrast.
  P3  variance components -- Wald interval from a behaviour term plus a seed term.

Selection runs on phoenix. Confirmation runs on starling / deeper-starling / jellyfish, which
selection never sees. Bar: type-I error inside [2.0%, 12.0%] for a nominal 5%, both series,
both sets. Tie-break among passers: narrowest median width on S1-PREFIX delivery-none.

Counts only; never prints response text.
"""
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_trajectory import MISINFO  # noqa: E402

NBOOT = 10000
RNG_SEED = 20260909


def matrix(labels, prefix, tag, nseeds, field):
    """behaviours x seeds matrix of the 0/1 indicator."""
    acc = {}
    for s in range(nseeds):
        raw = json.load(open(Path(labels) / f"{prefix}-{tag}-harmbench-s{s}" / "all.json"))
        for r in next(v for v in raw.values() if isinstance(v, list)):
            if r.get("SemanticCategory") != MISINFO:
                continue
            hit = (r.get("response_harmfulness") == "harmful") if field == "harmful" \
                else (r.get("response_refusal") == "refusal")
            acc.setdefault(r["BehaviorID"], {})[s] = float(hit)
    ids = sorted(acc)
    return np.array([[acc[b][s] for s in range(nseeds)] for b in ids])


# ---------------------------------------------------------------- candidates
def p0(A, B, rng, paired_seeds):
    """Incumbent: resample behaviours, condition on the seed draw."""
    d = A.mean(axis=1) - B.mean(axis=1)
    n = len(d)
    boots = d[rng.integers(0, n, (NBOOT, n))].mean(axis=1)
    return d.mean(), *np.percentile(boots, [2.5, 97.5])


def p1(A, B, rng, paired_seeds):
    """Seed as the unit."""
    a, b = A.mean(axis=0), B.mean(axis=0)          # per-seed rates
    if paired_seeds:
        d = a - b
        m, se, df = d.mean(), d.std(ddof=1) / np.sqrt(len(d)), len(d) - 1
    else:
        m = a.mean() - b.mean()
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        se = np.sqrt(va + vb)
        df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))  # Welch
    if se == 0:
        return m, m, m
    t = stats.t.ppf(0.975, df)
    return m, m - t * se, m + t * se


def p2(A, B, rng, paired_seeds):
    """Two-way cluster bootstrap: behaviours AND seeds resampled."""
    nb, na_s, nb_s = A.shape[0], A.shape[1], B.shape[1]
    bi = rng.integers(0, nb, (NBOOT, nb))
    si_a = rng.integers(0, na_s, (NBOOT, na_s))
    si_b = si_a if paired_seeds else rng.integers(0, nb_s, (NBOOT, nb_s))
    boots = np.empty(NBOOT)
    for k in range(NBOOT):
        boots[k] = (A[np.ix_(bi[k], si_a[k])].mean(axis=1)
                    - B[np.ix_(bi[k], si_b[k])].mean(axis=1)).mean()
    d = A.mean(axis=1) - B.mean(axis=1)
    return d.mean(), *np.percentile(boots, [2.5, 97.5])


def p3(A, B, rng, paired_seeds):
    """Wald interval from a behaviour component plus a seed component.

    Behaviour term is the P0 variance (behaviour sampling, seeds held). Seed terms are the
    between-seed variance of the per-seed rate. The two overlap slightly in within-cell noise,
    which makes this mildly CONSERVATIVE by construction -- stated rather than hidden.
    """
    d = A.mean(axis=1) - B.mean(axis=1)
    v_beh = d.var(ddof=1) / len(d)
    a, b = A.mean(axis=0), B.mean(axis=0)
    if paired_seeds:
        v_seed = (a - b).var(ddof=1) / len(a)
    else:
        v_seed = a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)
    se = np.sqrt(v_beh + v_seed)
    if se == 0:
        return d.mean(), d.mean(), d.mean()
    z = stats.norm.ppf(0.975)
    return d.mean(), d.mean() - z * se, d.mean() + z * se


CANDS = {"P0": p0, "P1": p1, "P2": p2, "P3": p3}


def calibrate(M, rng_seed):
    """All disjoint half-vs-half splits of the seed axis. True difference is 0 by construction."""
    ns = M.shape[1]
    half = ns // 2
    out = {k: {"rej": 0, "n": 0, "width": []} for k in CANDS}
    for combo in itertools.combinations(range(ns), half):
        if 0 not in combo:                      # count each disjoint split once
            continue
        other = [s for s in range(ns) if s not in combo]
        A, B = M[:, list(combo)], M[:, other]
        for k, fn in CANDS.items():
            rng = np.random.default_rng(rng_seed)
            m, lo, hi = fn(A, B, rng, paired_seeds=False)
            out[k]["rej"] += int(lo > 0 or hi < 0)
            out[k]["n"] += 1
            out[k]["width"].append(hi - lo)
    for k in out:
        out[k]["type1_pct"] = round(100 * out[k]["rej"] / out[k]["n"], 1)
        out[k]["median_width_pp"] = round(100 * float(np.median(out[k]["width"])), 2)
        del out[k]["width"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--traj-prefix", default="2026-08-28-traj4-h200")
    ap.add_argument("--prefix", default="2026-09-08-prefix-h200")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    SELECTION = ["phoenix"]
    CONFIRM = ["starling", "deeper-starling", "jellyfish"]
    res = {"experiment": "docs/experiments/09-09_inference-procedure_recalibration.md",
           "nboot": NBOOT, "rng_seed": RNG_SEED, "calibration": {}}

    for tag in SELECTION + CONFIRM:
        res["calibration"][tag] = {}
        for field in ("harmful", "refusal"):
            M = matrix(a.labels, a.traj_prefix, tag, 10, field)
            res["calibration"][tag][field] = calibrate(M, RNG_SEED)

    print(f"{'tag':16s} {'series':8s} " + " ".join(f"{k:>18s}" for k in CANDS))
    print(f"{'':16s} {'':8s} " + " ".join(f"{'type1% / width':>18s}" for _ in CANDS))
    for tag in SELECTION + CONFIRM:
        for field in ("harmful", "refusal"):
            row = res["calibration"][tag][field]
            mark = "SEL " if tag in SELECTION else "conf"
            print(f"{mark}{tag:12s} {field:8s} " + " ".join(
                f"{row[k]['type1_pct']:8.1f}% /{row[k]['median_width_pp']:7.2f}" for k in CANDS))

    # ---- frozen acceptance bar, applied to both sets and both series ----
    LO, HI = 2.0, 12.0
    passes = {}
    for k in CANDS:
        rates = [res["calibration"][t][f][k]["type1_pct"]
                 for t in SELECTION + CONFIRM for f in ("harmful", "refusal")]
        passes[k] = {"all_rates": rates, "passes_bar": all(LO <= r <= HI for r in rates),
                     "eligible": k != "P0"}
    res["bar"] = {"lo_pct": LO, "hi_pct": HI}
    res["candidates"] = passes
    print("\n=== frozen bar: type-I in [2.0%, 12.0%] on BOTH series at ALL FOUR tags ===")
    for k, v in passes.items():
        note = "" if v["eligible"] else "  (reference only, not eligible)"
        print(f"  {k}: rates {v['all_rates']}  -> {'PASS' if v['passes_bar'] else 'FAIL'}{note}")

    # ---- tie-break: narrowest median width on S1-PREFIX delivery - none ----
    arms = {t: matrix(a.labels, a.prefix, t, 5, "harmful") for t in ("none", "delivery")}
    tb = {}
    for k, fn in CANDS.items():
        rng = np.random.default_rng(RNG_SEED)
        m, lo, hi = fn(arms["delivery"], arms["none"], rng, paired_seeds=True)
        tb[k] = {"delta_pp": round(100 * m, 2), "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)],
                 "width_pp": round(100 * (hi - lo), 2)}
    res["tiebreak_delivery_minus_none"] = tb
    print("\n=== tie-break: S1-PREFIX delivery - none (paired seeds) ===")
    for k, v in tb.items():
        print(f"  {k}: {v['delta_pp']:+6.2f}pp  CI [{v['ci95_pp'][0]:+7.2f}, {v['ci95_pp'][1]:+7.2f}]"
              f"  width {v['width_pp']:6.2f}pp")

    winners = [k for k, v in passes.items() if v["passes_bar"] and v["eligible"]]
    if not winners:
        res["selected"] = None
        res["verdict"] = ("NO CANDIDATE PASSES -- keep P0 as the recorded procedure and label every "
                          "interval as conditional on the seed draw. Do NOT add a candidate now.")
    else:
        sel = min(winners, key=lambda k: tb[k]["width_pp"])
        res["selected"] = sel
        res["verdict"] = f"SELECTED {sel} -- passes the bar at all four tags, narrowest width among passers"
    print("\n" + res["verdict"])

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "procedure_selection.json").write_text(json.dumps(res, indent=2) + "\n")


if __name__ == "__main__":
    main()
