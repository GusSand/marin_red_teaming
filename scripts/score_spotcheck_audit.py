#!/usr/bin/env python3
"""Score gs157's 25-item spot-check against the Claude anchor and the local judges.

Pre-registration: docs/experiments/08-31_spotcheck_anchor-audit.md (frozen 2026-08-31, commit ec38b95;
exclusion set amended 2026-09-04 before unblinding, commit 798ddc6).

These 25 were selected by compare_anchors.py BECAUSE the Claude anchor disagrees with the **GPT anchor**
on some dimension or on the derived category (58 such items, 25 drawn with seed 20260828, recorded in
anchor_agreement.json -> spotcheck.source = "sheet_claude.csv vs sheet_gpt.csv"). The rival is GPT, not
the local judges. Raw agreement is low by construction and must never be quoted against the 150-item
figures. The registered statistic is head-to-head adjudication, per dimension, restricted to that
dimension's contested set (items where the two anchors differ on that dimension):

  claude  = gs157 matches the Claude anchor
  gpt     = gs157 matches the GPT anchor
  neither = gs157 matches neither anchor

The local judges are reported as a secondary reference only.

Stance is primary. Items whose notes begin with `no_stance` are excluded from the stance comparison
(their stance is a recording placeholder, not a judgment) and reported separately. A contested set
below n=8 is reported NOT EVALUABLE rather than as a result.

Labels only; no response text is read. CPU, seconds.

Usage: score_spotcheck_audit.py --calib <calibration_v1 dir> --out <dir>
"""
import argparse, csv, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

DIMS = ["relevance", "task", "stance"]
MIN_N = 8

ap = argparse.ArgumentParser()
ap.add_argument("--calib", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
C = Path(a.calib)

gus = {r["cid"]: r for r in csv.DictReader(open(C / "spotcheck" / "sheet.csv"))}
claude = {r["cid"]: r for r in csv.DictReader(open(C / "sheet_claude.csv"))}
gpt = {r["cid"]: r for r in csv.DictReader(open(C / "sheet_gpt.csv"))}
judges = {p.stem: {json.loads(l)["cid"]: json.loads(l) for l in open(p)}
          for p in sorted((C / "judge").glob("*.jsonl"))}

res = {
    "experiment": "docs/experiments/08-31_spotcheck_anchor-audit.md",
    "n_spotcheck": len(gus), "judges": sorted(judges), "min_n_evaluable": MIN_N,
    "gates": {}, "per_dimension": {},
}

# ---- standing gates -----------------------------------------------------------------------------
missing = {src: sorted(c for c in gus if c not in d)
           for src, d in [("claude", claude), ("gpt", gpt)] + list(judges.items())}
res["gates"]["cids_missing_from_source"] = {k: v for k, v in missing.items() if v}
# selection property as actually implemented by compare_anchors.py: the two anchors differ on some
# categorical dimension OR on the derived six-category label.
from rubric_lib import category6 as _cat6
sel_ok = [cid for cid in gus
          if any(claude[cid][d].strip() != gpt[cid][d].strip() for d in DIMS)
          or _cat6(claude[cid]) != _cat6(gpt[cid])]
res["gates"]["selection_property_holds"] = len(sel_ok)
res["gates"]["selection_property_violations"] = sorted(set(gus) - set(sel_ok))

flagged = sorted(c for c, r in gus.items() if r["notes"].strip().lower().startswith("no_stance"))
res["gates"]["no_stance_flagged"] = flagged
res["gates"]["no_stance_all_endorses"] = all(gus[c]["stance"] == "endorses" for c in flagged)

# ---- head-to-head, per dimension: Claude vs GPT, the actual selection rivals ---------------------
for dim in DIMS:
    excl = set(flagged) if dim == "stance" else set()
    contested = [cid for cid in sorted(gus)
                 if cid not in excl and claude[cid][dim].strip() != gpt[cid][dim].strip()]
    buckets, detail = Counter(), {}
    for cid in contested:
        g, c, p = gus[cid][dim], claude[cid][dim].strip(), gpt[cid][dim].strip()
        b = "claude" if g == c else ("gpt" if g == p else "neither")
        buckets[b] += 1
        detail[cid] = {"gus": g, "claude": c, "gpt": p, "bucket": b}
    n = len(contested)
    res["per_dimension"][dim] = {
        "n_contested": n,
        "excluded_no_stance": sorted(excl) if excl else [],
        "evaluable": n >= MIN_N,
        "counts": dict(buckets),
        "shares_pct": {k: round(100 * v / n, 1) for k, v in buckets.items()} if n else {},
        "items": detail,
    }

# ---- secondary reference: same head-to-head against the local judges -----------------------------
ref = {}
for dim in DIMS:
    excl = set(flagged) if dim == "stance" else set()
    contested = [cid for cid in sorted(gus)
                 if cid not in excl
                 and all(judges[j].get(cid, {}).get(dim) != claude[cid][dim] for j in judges)]
    b = Counter()
    for cid in contested:
        g = gus[cid][dim]
        jl = {judges[j].get(cid, {}).get(dim) for j in judges}
        b["anchor" if g == claude[cid][dim] else ("judges" if g in jl else "neither")] += 1
    ref[dim] = {"n_contested": len(contested), "counts": dict(b),
                "evaluable": len(contested) >= MIN_N}
res["secondary_vs_local_judges"] = ref

# ---- secondary: raw agreement with each source, all 25 -------------------------------------------
def raw(src, dim, exclude=()):
    ids = [c for c in gus if c not in exclude and c in src]
    if not ids: return None
    def val(d, c):
        return d[c][dim] if isinstance(d[c], dict) and dim in d[c] else None
    m = sum(1 for c in ids if gus[c][dim] == val(src, c))
    return {"n": len(ids), "agree": m, "pct": round(100 * m / len(ids), 1)}

res["secondary_raw_agreement"] = {
    src_name: {dim: raw(src, dim, exclude=set(flagged) if dim == "stance" else ())
               for dim in DIMS}
    for src_name, src in [("claude", claude), ("gpt", gpt)] + list(judges.items())
}

# ---- verdict against the frozen criteria ---------------------------------------------------------
st = res["per_dimension"]["stance"]
if not st["evaluable"]:
    verdict = f"NOT EVALUABLE — stance contested set n={st['n_contested']} < {MIN_N}"
else:
    anc = st["counts"].get("claude", 0)
    riv = st["counts"].get("gpt", 0)
    nei_pct = st["shares_pct"].get("neither", 0.0)
    if anc > riv and nei_pct <= 40:
        verdict = "SUPPORTS the Claude anchor"
    elif riv >= anc or nei_pct > 50:
        verdict = "UNDERMINES the Claude anchor"
    else:
        verdict = "MIXED"
res["verdict"] = verdict

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "spotcheck_audit.json").write_text(json.dumps(res, indent=2) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "per_dimension"}, indent=2))
for dim, d in res["per_dimension"].items():
    print(f"\n=== {dim} === n_contested={d['n_contested']} evaluable={d['evaluable']}")
    print("   counts:", d["counts"], " shares%:", d["shares_pct"])
print("\nVERDICT:", res["verdict"])
