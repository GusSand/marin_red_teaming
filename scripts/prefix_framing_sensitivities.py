#!/usr/bin/env python3
"""S1-PREFIX: ADDED analyses, clearly labelled. These do NOT replace the registered analysis.

Three questions the frozen plan does not answer, all raised by the result:
  A  Is the harmful rise just the arithmetic complement of the (pre-declared partly forced)
     refusal drop? Decompose the 2x2 of harmful x refusal per arm.
  B  Does f survive using the WITHIN-JOB none arm as the Phoenix baseline instead of the
     cross-job traj4 phoenix? (The frozen f uses traj4; this is sensitivity, not a substitute.)
  C  How much can the 1 missing WildGuard label per tag move any rate? Bound it both ways.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts")
from analyze_trajectory import MISINFO  # noqa: E402

L = Path("/scratch/gs157/marin-misinfo-labels")
B_BOOT, RNG_SEED = 10000, 20260908


def cells(prefix, tag, nseeds):
    """Behaviour-level means of the four harmful x refusal cells, plus missing-label mask."""
    acc = {}
    for s in range(nseeds):
        raw = json.load(open(L / f"{prefix}-{tag}-harmbench-s{s}" / "all.json"))
        rows = next(v for v in raw.values() if isinstance(v, list))
        for r in rows:
            if r.get("SemanticCategory") != MISINFO:
                continue
            h = r.get("response_harmfulness") == "harmful"
            f = r.get("response_refusal") == "refusal"
            miss = r.get("response_harmfulness") is None
            acc.setdefault(r["BehaviorID"], []).append((h, f, miss))
    ids = sorted(acc)
    A = {k: np.array([np.mean([x[i] for x in acc[b]]) for b in ids])
         for i, k in ((0, "harmful"), (1, "refusal"), (2, "missing"))}
    A["h_and_nr"] = np.array([np.mean([x[0] and not x[1] for x in acc[b]]) for b in ids])
    A["h_and_r"] = np.array([np.mean([x[0] and x[1] for x in acc[b]]) for b in ids])
    A["nh_and_nr"] = np.array([np.mean([not x[0] and not x[1] for x in acc[b]]) for b in ids])
    return ids, A


P = "2026-09-08-prefix-h200"
T = "2026-08-28-traj4-h200"
arms = {t: cells(P, t, 5) for t in ("none", "delivery", "deflect")}
traj = {t: cells(T, t, 10) for t in ("phoenix", "starling")}
ids = arms["none"][0]
assert all(v[0] == ids for v in arms.values()), "behaviour sets differ across arms"

print(f"=== A. harmful x refusal decomposition (behaviour-level pct, in scope n={len(ids)}) ===")
print(f"{'arm':10s} {'harmful':>8s} {'refusal':>8s} {'harm&NOTrefuse':>15s} {'harm&refuse':>12s} {'neither':>9s}")
for t, (_, A) in list(arms.items()) + [(f"~{k}", v) for k, v in traj.items()]:
    print(f"{t:10s} {100*A['harmful'].mean():8.2f} {100*A['refusal'].mean():8.2f} "
          f"{100*A['h_and_nr'].mean():15.2f} {100*A['h_and_r'].mean():12.2f} "
          f"{100*A['nh_and_nr'].mean():9.2f}")

dh = 100 * (arms["delivery"][1]["harmful"].mean() - arms["none"][1]["harmful"].mean())
dr = 100 * (arms["delivery"][1]["refusal"].mean() - arms["none"][1]["refusal"].mean())
print(f"\ndelivery-none:  d_harmful={dh:+.2f}pp   d_refusal={dr:+.2f}pp   "
      f"d_harmful+d_refusal={dh+dr:+.2f}pp")
print("  If the harmful rise were ONLY suppressed refusals converting 1:1, the sum would be ~0.")
# CORRECTED after the raw cross-tab (scripts/tmp_prefix_checks/xtab_raw.py): WildGuard labels
# harmful AND refusal for 0 of 1890 in-scope rows, so harmful-and-not-refusing IS harmful and
# that cell carries no independent information. The informative one is the compliant-but-
# UNHARMFUL cell -- responses that already complied and were not harmful, then turned harmful.
dnn = 100 * (arms["delivery"][1]["nh_and_nr"].mean() - arms["none"][1]["nh_and_nr"].mean())
print(f"  Fall in compliant-but-unharmful: {dnn:+.2f}pp -- the ONLY part of the harmful rise")
print(f"  not sourced from the (pre-declared partly forced) refusal drop.")

print("\n=== B. f sensitivity: which Phoenix baseline? (frozen f uses traj4) ===")
rng = np.random.default_rng(RNG_SEED)
idx = rng.integers(0, len(ids), (B_BOOT, len(ids)))
num = arms["delivery"][1]["harmful"] - arms["none"][1]["harmful"]
for name, den in (("traj4 phoenix->starling  [FROZEN]",
                   traj["starling"][1]["harmful"] - traj["phoenix"][1]["harmful"]),
                  ("within-job none->traj4 starling [sensitivity]",
                   traj["starling"][1]["harmful"] - arms["none"][1]["harmful"])):
    fb = num[idx].mean(axis=1) / den[idx].mean(axis=1)
    print(f"  {name:46s} den={100*den.mean():6.2f}pp  f={num.mean()/den.mean():.3f} "
          f"CI[{np.percentile(fb,2.5):.3f}, {np.percentile(fb,97.5):.3f}]")

print("\n=== C. missing-label bound (1 row per tag; rate moves at most 1/270 or 1/540) ===")
for t, (_, A) in list(arms.items()) + [(f"~{k}", v) for k, v in traj.items()]:
    ns = 5 if not t.startswith("~") else 10
    n = 54 * ns
    # A["missing"] is a behaviour-level MEAN over seeds, so the row count is sum x nseeds.
    print(f"  {t:10s} missing_rows={int(round(A['missing'].sum() * ns))} of {n} "
          f"max_swing={100/n:.3f}pp  (bootstrap CI half-widths are ~4-8pp)")
