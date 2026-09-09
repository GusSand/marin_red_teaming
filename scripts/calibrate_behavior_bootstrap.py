#!/usr/bin/env python3
"""Is the behaviour-level bootstrap this project uses everywhere actually calibrated?

Raised by the independent verification of S1-PREFIX (2026-09-09). The procedure resamples
the 54 BEHAVIOURS and conditions on the seeds drawn, so it propagates item-sampling noise
but NOT seed-to-seed generation noise. If a checkpoint's per-seed rate is unstable, the
resulting intervals are too narrow and the permutation p is anticonservative.

Null calibration: split one tag's seeds into every disjoint half-vs-half pair. Same model,
same job, same GPU, so the TRUE difference is zero by construction. Any rejection is a false
positive. Nominal rate is 5%.

Also reports seed-level (t) intervals for a named contrast, treating the SEED as the unit of
resampling, which is the inference the frozen procedure should be compared against.

    python scripts/calibrate_behavior_bootstrap.py --labels /scratch/gs157/marin-misinfo-labels

Counts only; never prints response text.
"""
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_trajectory import MISINFO  # noqa: E402

B, RNG_SEED = 10000, 20260908


def matrix(labels, prefix, tag, nseeds, field):
    """behaviours x seeds matrix of the 0/1 indicator."""
    acc = {}
    for s in range(nseeds):
        raw = json.load(open(Path(labels) / f"{prefix}-{tag}-harmbench-s{s}" / "all.json"))
        for r in next(v for v in raw.values() if isinstance(v, list)):
            if r.get("SemanticCategory") != MISINFO:
                continue
            hit = r.get("response_harmfulness") == "harmful" if field == "harmful" \
                else r.get("response_refusal") == "refusal"
            acc.setdefault(r["BehaviorID"], {})[s] = float(hit)
    ids = sorted(acc)
    return np.array([[acc[b][s] for s in range(nseeds)] for b in ids])


def frozen_contrast(a, b, rng):
    """The procedure used throughout this project: resample BEHAVIOURS, condition on seeds."""
    d = a - b
    n = len(d)
    boots = d[rng.integers(0, n, (B, n))].mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    signs = rng.choice([-1.0, 1.0], size=(B, n))
    p = (np.sum(np.abs((signs * d).mean(axis=1)) >= abs(d.mean()) - 1e-12) + 1) / (B + 1)
    return d.mean(), lo, hi, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--prefix", default="2026-09-08-prefix-h200")
    ap.add_argument("--traj-prefix", default="2026-08-28-traj4-h200")
    a = ap.parse_args()

    out = {}
    print("=== per-seed instability (the thing the frozen bootstrap conditions away) ===")
    for tag, pfx, ns in (("phoenix", a.traj_prefix, 10), ("starling", a.traj_prefix, 10)):
        M = matrix(a.labels, pfx, tag, ns, "harmful")
        per_seed = 100 * M.mean(axis=0)
        print(f"  {tag:9s} per-seed harmful rate  min={per_seed.min():.2f}%  "
              f"max={per_seed.max():.2f}%  sd={per_seed.std(ddof=1):.2f}pp   "
              f"(binomial-only sd at p=.5, n=54 = {100*0.5/np.sqrt(54):.2f}pp)")
        out[f"{tag}_seed_sd_pp"] = round(float(per_seed.std(ddof=1)), 3)

    print("\n=== NULL CALIBRATION: disjoint 5-vs-5 splits of phoenix (true difference = 0) ===")
    for field in ("harmful", "refusal"):
        M = matrix(a.labels, a.traj_prefix, "phoenix", 10, field)
        rng = np.random.default_rng(RNG_SEED)
        excl0 = sig = 0; diffs = []; n = 0
        for combo in itertools.combinations(range(10), 5):
            if 0 not in combo:                    # each disjoint split counted once
                continue
            other = [s for s in range(10) if s not in combo]
            m, lo, hi, p = frozen_contrast(M[:, list(combo)].mean(axis=1),
                                           M[:, other].mean(axis=1), rng)
            n += 1; diffs.append(abs(m))
            excl0 += (lo > 0 or hi < 0); sig += (p < 0.05)
        d = 100 * np.array(diffs)
        print(f"  {field:8s} splits={n:3d}  CI excludes 0: {100*excl0/n:5.1f}%   "
              f"perm p<0.05: {100*sig/n:5.1f}%   (nominal 5.0%)   "
              f"median|diff|={np.median(d):.2f}pp  max|diff|={d.max():.2f}pp")
        out[f"null_{field}"] = {"n_splits": n, "ci_excludes_zero_pct": round(100 * excl0 / n, 1),
                                "perm_p_lt_05_pct": round(100 * sig / n, 1),
                                "max_abs_diff_pp": round(float(d.max()), 3)}

    print("\n=== seed-level (t) intervals for the S1-PREFIX contrasts ===")
    from scipy import stats
    arms = {t: matrix(a.labels, a.prefix, t, 5, "harmful") for t in ("none", "delivery", "deflect")}
    ph = matrix(a.labels, a.traj_prefix, "phoenix", 10, "harmful")
    st = matrix(a.labels, a.traj_prefix, "starling", 10, "harmful")
    def seed_ci(X, Y, paired_seeds):
        x, y = 100 * X.mean(axis=0), 100 * Y.mean(axis=0)
        if paired_seeds:
            d = x - y; se = d.std(ddof=1) / np.sqrt(len(d)); t = stats.t.ppf(.975, len(d) - 1)
            return d.mean(), d.mean() - t * se, d.mean() + t * se
        m = x.mean() - y.mean()
        se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
        df = min(len(x), len(y)) - 1
        t = stats.t.ppf(.975, df)
        return m, m - t * se, m + t * se
    for name, X, Y, pr in (("delivery - none", arms["delivery"], arms["none"], True),
                           ("deflect - none", arms["deflect"], arms["none"], True),
                           ("starling - phoenix", st, ph, True)):
        m, lo, hi = seed_ci(X, Y, pr)
        print(f"  {name:20s} {m:+7.2f}pp  seed-level 95% CI [{lo:+7.2f}, {hi:+7.2f}]")
        out[name] = {"delta_pp": round(float(m), 3), "seed_ci95_pp": [round(float(lo), 3), round(float(hi), 3)]}
    print("\n" + json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
