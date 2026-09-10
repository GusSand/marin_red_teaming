#!/usr/bin/env python3
"""S1-STATS gap check: the calibration validated the UNPAIRED procedures, but the recorded
contrasts are applied PAIRED.

`select_inference_procedure.py` measures type-I error on disjoint 5-vs-5 seed splits, which is
an unpaired comparison. Every real contrast here (starling vs phoenix, delivery vs none) is
applied with `paired_seeds=True`, because seed s is the same sampling seed on both sides. The
paired variant of P1 and P2 was therefore never calibrated.

This closes that gap. Same 126 disjoint splits, but seed i of half A is paired with seed i of
half B -- an ARTIFICIAL pairing of independent seeds, which is the worst case for pairing: if
the paired variant holds its nominal rate when the pairing carries no information, it is safe.
True difference is still zero by construction.

ADDED analysis. Does not replace the registered calibration. Counts only.
"""
import argparse, itertools, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_inference_procedure import CANDS, matrix, RNG_SEED  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--labels", required=True)
ap.add_argument("--traj-prefix", default="2026-08-28-traj4-h200")
ap.add_argument("--out", required=True)
a = ap.parse_args()

TAGS = ["phoenix", "starling", "deeper-starling", "jellyfish"]
res = {"experiment": "docs/experiments/09-09_inference-procedure_recalibration.md",
       "note": "ADDED gap check: type-I error of the PAIRED variant, which the registered "
               "calibration did not cover. Artificial pairing of independent seeds.",
       "paired_null": {}}

print(f"{'tag':18s} {'series':8s} " + " ".join(f"{k:>10s}" for k in CANDS))
for tag in TAGS:
    res["paired_null"][tag] = {}
    for field in ("harmful", "refusal"):
        M = matrix(a.labels, a.traj_prefix, tag, 10, field)
        rej = {k: 0 for k in CANDS}
        n = 0
        for combo in itertools.combinations(range(10), 5):
            if 0 not in combo:
                continue
            other = [s for s in range(10) if s not in combo]
            A, B = M[:, list(combo)], M[:, other]      # seed i of A paired with seed i of B
            n += 1
            for k, fn in CANDS.items():
                rng = np.random.default_rng(RNG_SEED)
                _m, lo, hi = fn(A, B, rng, paired_seeds=True)
                rej[k] += int(lo > 0 or hi < 0)
        row = {k: round(100 * rej[k] / n, 1) for k in CANDS}
        res["paired_null"][tag][field] = row
        print(f"{tag:18s} {field:8s} " + " ".join(f"{row[k]:9.1f}%" for k in CANDS))

LO, HI = 2.0, 12.0
print(f"\n=== against the same [{LO}%, {HI}%] band, PAIRED variant ===")
for k in CANDS:
    rates = [res["paired_null"][t][f][k] for t in TAGS for f in ("harmful", "refusal")]
    res.setdefault("in_band", {})[k] = all(LO <= r <= HI for r in rates)
    print(f"  {k}: {rates} -> {'in band' if res['in_band'][k] else 'OUT OF BAND'}")

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "paired_variant_calibration.json").write_text(json.dumps(res, indent=2) + "\n")
