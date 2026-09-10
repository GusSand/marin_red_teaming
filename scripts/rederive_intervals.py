#!/usr/bin/env python3
"""S1-STATS: what every in-scope recorded contrast becomes under each candidate procedure.

Plan: docs/experiments/09-09_inference-procedure_recalibration.md (frozen 2026-09-09, bc0a32e).

The frozen plan's re-derivation step is conditional on a WINNING procedure. Selection returned
NO CANDIDATE PASSES, so this script does NOT declare a canonical interval. It reports what each
candidate gives beside the recorded P0 value, as a clearly-labelled sensitivity. The recorded
numbers stand; nothing here replaces them.

Covers the contrasts reachable from the preserved per-instance data:
  S1-TRAJ / S1-CKPT / S1-PREFIX   -- WildGuard harmful and refusal, from all.json
  S1-FORMAT                       -- the five mechanical format measures, from items/key

Counts only; never prints response text.
"""
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_inference_procedure import CANDS, matrix  # noqa: E402
from analyze_format_carryover import MEASURES, measure, tag_of  # noqa: E402
from grade_benign_twins_v2 import grade  # noqa: E402

SEED_RE = re.compile(r"-s(\d+)$")


def report(A, B, label, rows, paired_seeds):
    rec = {"contrast": label, "n_behaviors": int(A.shape[0]),
           "seeds": [int(A.shape[1]), int(B.shape[1])]}
    for k, fn in CANDS.items():
        rng = np.random.default_rng(20260909)
        m, lo, hi = fn(A, B, rng, paired_seeds)
        rec[k] = {"delta_pp": round(100 * m, 2),
                  "ci95_pp": [round(100 * lo, 2), round(100 * hi, 2)],
                  "width_pp": round(100 * (hi - lo), 2),
                  "excludes_zero": bool(lo > 0 or hi < 0)}
    rows.append(rec)
    p0, p1 = rec["P0"], rec["P1"]
    flag = "" if p0["excludes_zero"] == p1["excludes_zero"] else "   <-- P0 and P1 DISAGREE on zero"
    print(f"  {label:44s} {p0['delta_pp']:+7.2f}pp  P0 [{p0['ci95_pp'][0]:+7.2f},{p0['ci95_pp'][1]:+7.2f}]"
          f"  P1 [{p1['ci95_pp'][0]:+7.2f},{p1['ci95_pp'][1]:+7.2f}]"
          f"  P2 [{rec['P2']['ci95_pp'][0]:+7.2f},{rec['P2']['ci95_pp'][1]:+7.2f}]{flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--items"); ap.add_argument("--key")
    ap.add_argument("--twins"); ap.add_argument("--twin-responses")
    ap.add_argument("--cooldown-prefix", default="2026-09-08-cooldown-h200")
    ap.add_argument("--traj-prefix", default="2026-08-28-traj4-h200")
    ap.add_argument("--prefix", default="2026-09-08-prefix-h200")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []

    print("=== S1-TRAJ / S1-CKPT: WildGuard series, 10 seeds per tag ===")
    tags = ["jellyfish", "phoenix", "starling", "deeper-starling"]
    M = {(t, f): matrix(a.labels, a.traj_prefix, t, 10, f) for t in tags for f in ("harmful", "refusal")}
    for f in ("harmful", "refusal"):
        for A, B in (("jellyfish", "phoenix"), ("phoenix", "starling"), ("phoenix", "deeper-starling")):
            report(M[(B, f)], M[(A, f)], f"{f}: {B} - {A}", rows, paired_seeds=True)

    print("\n=== S1-CKPT: cooldown intermediates vs phoenix and starling, 10 seeds ===")
    for ck in ("cooldown-1340000", "cooldown-1360000", "cooldown-1380000"):
        C = matrix(a.labels, a.cooldown_prefix, ck, 10, "refusal")
        report(C, M[("phoenix", "refusal")], f"refusal: {ck} - phoenix", rows, paired_seeds=True)
        report(C, M[("starling", "refusal")], f"refusal: {ck} - starling", rows, paired_seeds=True)

    print("\n=== S1-PREFIX: 5 seeds per arm ===")
    P = {t: matrix(a.labels, a.prefix, t, 5, "harmful") for t in ("none", "delivery", "deflect")}
    report(P["delivery"], P["none"], "harmful: delivery - none", rows, paired_seeds=True)
    report(P["deflect"], P["none"], "harmful: deflect - none", rows, paired_seeds=True)

    if a.items and a.key:
        print("\n=== S1-FORMAT: five mechanical measures, 10 seeds per cell ===")
        items = {json.loads(l)["cid"]: json.loads(l)
                 for l in Path(a.items).read_text().splitlines() if l.strip()}
        key = json.load(open(a.key))["items"]
        cell = {m: defaultdict(dict) for m in MEASURES}
        for cid, k in key.items():
            t = tag_of(k["run"])
            sm = SEED_RE.search(k["run"])
            if not sm:
                raise SystemExit(f"cannot recover a seed from run name {k['run']!r}")
            s = int(sm.group(1))
            vals, _ropen, _body = measure(items[cid]["response"])
            for name, v in vals.items():
                cell[name][t].setdefault(k["BehaviorID"], {})[s] = float(v)
        for name in MEASURES:
            mats = {}
            for t, d in cell[name].items():
                ids = sorted(d)
                seeds = sorted(set().union(*[set(d[b]) for b in ids]))
                mats[t] = np.array([[d[b][s] for s in seeds] for b in ids])
            report(mats["starling"], mats["phoenix"], f"{name}: starling - phoenix", rows,
                   paired_seeds=True)

    if a.twins and a.twin_responses:
        print("\n=== S1-05B: benign twins, mean constraints met (0-4), only 3 seeds ===")
        twins = {t["twin_id"]: t for t in
                 (json.loads(l) for l in Path(a.twins).read_text().splitlines() if l.strip())}
        cell = defaultdict(dict)
        for l in Path(a.twin_responses).read_text().splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            g, _echo = grade(r["response"], twins[r["twin_id"]])
            cell[r["checkpoint"]].setdefault(twins[r["twin_id"]]["BehaviorID"], {})[r["seed"]] = \
                float(sum(g.values()))
        mats = {}
        for t, d in cell.items():
            ids = sorted(d)
            seeds = sorted(set().union(*[set(d[b]) for b in ids]))
            mats[t] = np.array([[d[b][s] for s in seeds] for b in ids])
        # NOTE: reported in CONSTRAINTS x100, not pp -- the units of this primary are 0-4 constraints.
        report(mats["starling"], mats["phoenix"], "constraints(x100): starling - phoenix", rows,
               paired_seeds=True)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "rederived_intervals.json").write_text(json.dumps(
        {"experiment": "docs/experiments/09-09_inference-procedure_recalibration.md",
         "note": "SENSITIVITY ONLY. Selection returned NO CANDIDATE PASSES, so no interval here "
                 "is canonical. Recorded P0 values stand as the registered numbers.",
         "contrasts": rows}, indent=2) + "\n")
    dis = [r["contrast"] for r in rows if r["P0"]["excludes_zero"] != r["P1"]["excludes_zero"]]
    print(f"\ncontrasts where P0 and P1 disagree on excluding zero: {len(dis)} of {len(rows)}")
    for d in dis:
        print("   ", d)


if __name__ == "__main__":
    main()
