#!/usr/bin/env python3
"""Worst-case sensitivity of the pre-registered contrasts to rows the judge left unlabelled.

    python scripts/sensitivity_missing_labels.py --labels <dir> --prefix <prefix> [--out <json>]

For every (tag, seed) run, rows with response_harmfulness None AND a non-empty response are
the "missing" set (blank responses are excluded from the harmful-rate denominator by the spec
and are not imputed). Each contrast's mean paired difference is recomputed under the four
corner imputations (A-side all harmful/unharmful x B-side all harmful/unharmful; likewise
refusal/compliance) and the extreme values are reported as bounds. Counts only.
"""
import argparse, json
from pathlib import Path
import numpy as np

MISINFO = "misinformation_disinformation"
SEEDS = {"kestrel": 3, "ocelot": 3, "jellyfish": 10, "phoenix": 10, "starling": 10, "deeper-starling": 10}
CONTRASTS = [("H-min", "jellyfish", "phoenix", "harmful"), ("H0", "phoenix", "starling", "refusal"),
             ("H1-refusal", "phoenix", "deeper-starling", "refusal"), ("H1-hgnr", "phoenix", "deeper-starling", "hgnr"),
             ("harm-H0", "phoenix", "starling", "harmful"), ("harm-H1", "phoenix", "deeper-starling", "harmful")]


def load(labels, prefix, tag):
    runs = []
    for s in range(SEEDS[tag]):
        raw = json.load(open(Path(labels) / f"{prefix}-{tag}-harmbench-s{s}" / "all.json"))
        rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
        d = {}
        for r in rows:
            if r.get("SemanticCategory") != MISINFO:
                continue
            resp = str(r.get("response") or "").strip()
            d[r["BehaviorID"]] = {"h": r.get("response_harmfulness"), "f": r.get("response_refusal"), "empty": not resp,
                                  "missing": r.get("response_harmfulness") is None and bool(resp)}
        runs.append(d)
    return runs


def props(runs, ids, series, impute):
    """impute: None (as analysed: missing -> not harmful / compliance) or 'pos' / 'neg'."""
    out = np.zeros(len(ids))
    for j, i in enumerate(ids):
        num = den = 0.0
        for run in runs:
            r = run[i]
            h = r["h"] == "harmful"; f = r["f"] == "refusal"
            if r["missing"] and impute:
                h = impute == "pos"; f = impute == "pos"
            if series == "harmful":
                if r["empty"]: continue
                num += h; den += 1
            elif series == "refusal":
                num += f; den += 1
            elif series == "hgnr":
                if f: continue
                num += h; den += 1
        out[j] = num / den if den else np.nan
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--labels", required=True); ap.add_argument("--prefix", required=True)
    ap.add_argument("--out", default=None); a = ap.parse_args()
    tags = sorted(SEEDS); data = {t: load(a.labels, a.prefix, t) for t in tags}
    ids = sorted(data["phoenix"][0])
    miss = {t: sum(r[i]["missing"] for r in data[t] for i in ids) for t in tags}
    print("non-empty unlabelled rows in misinfo subset:", miss, "total", sum(miss.values()))
    report = {"missing_by_tag": miss, "contrasts": []}
    for name, A, B, series in CONTRASTS:
        base = float(np.nanmean(props(data[B], ids, series, None) - props(data[A], ids, series, None)))
        corners = {}
        for ia in (None, "pos", "neg"):
            for ib in (None, "pos", "neg"):
                corners[f"A={ia},B={ib}"] = float(np.nanmean(props(data[B], ids, series, ib) - props(data[A], ids, series, ia)))
        lo, hi = min(corners.values()), max(corners.values())
        print(f"{name:11} {series:8} {A}->{B}: as-analysed {100*base:+.2f}pp  worst-case range [{100*lo:+.2f}, {100*hi:+.2f}]  (width {100*(hi-lo):.2f}pp; missing A={miss[A]} B={miss[B]})")
        report["contrasts"].append({"contrast": name, "series": series, "A": A, "B": B, "as_analysed": base, "min": lo, "max": hi, "corners": corners})
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=2)); print("wrote", a.out)


if __name__ == "__main__":
    main()
