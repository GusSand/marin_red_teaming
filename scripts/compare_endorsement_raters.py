#!/usr/bin/env python3
"""S1-ENDORSE-V2: cross-rater agreement, and the 100-row blinded audit set.

Plan: docs/experiments/09-10_endorsement-feature_decomposition.md (frozen 2026-09-10).

Agreement: field-level raw agreement, Cohen's kappa where defined, full confusion tables, and for the
five concession flags positive and negative agreement as well, because prevalence may be low.

Audit set: 100 rows, built AFTER both rater files are complete and BEFORE any checkpoint difference is
interpreted. Filled with cross-rater disagreements first; if they exceed 100 they are sampled with seed
20260910 stratified by checkpoint and primitive field; any remainder is filled with checkpoint- and
stance-stratified agreements. The emitted audit file carries no checkpoint and no rater label.

Reads key.json for stratification only. Never prints a checkpoint-split label count.
"""
import argparse, json, random
from collections import Counter, defaultdict
from pathlib import Path

FIELDS = ("boundary_confidence", "net_stance", "assertion_form", "claim_uncertainty",
          "attribution", "added_support", "final_takeaway")
FLAGS = ("moral", "social", "legal", "stylistic", "opposing_view")
AUDIT_N = 100
SEED = 20260910
truthy = lambda v: v is True or (isinstance(v, str) and v.lower() == "true")


def load(paths):
    out = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                out[r["cid"]] = r
    return out


def kappa(pairs):
    """Cohen's kappa. None when either rater is degenerate (one value everywhere)."""
    n = len(pairs)
    if not n:
        return None
    a, b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    if len(a) < 2 or len(b) < 2:
        return None
    po = sum(1 for x, y in pairs if x == y) / n
    pe = sum(a[k] * b.get(k, 0) for k in a) / (n * n)
    return None if abs(1 - pe) < 1e-12 else (po - pe) / (1 - pe)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", required=True)
    ap.add_argument("--rater-a", nargs="+", required=True)
    ap.add_argument("--rater-b", nargs="+", required=True)
    ap.add_argument("--name-a", default="A")
    ap.add_argument("--name-b", default="B")
    ap.add_argument("--items", help="package dir, needed only to emit the audit set")
    ap.add_argument("--audit-out")
    ap.add_argument("--out")
    a = ap.parse_args()

    key = json.loads(Path(a.key).read_text())["items"]
    A, B = load(a.rater_a), load(a.rater_b)
    cids = sorted(set(A) & set(B))
    print(f"rater {a.name_a}: {len(A)} rows · rater {a.name_b}: {len(B)} rows · overlap {len(cids)}")
    if len(cids) != len(A) or len(cids) != len(B):
        print(f"WARNING: non-identical universes; only the {len(cids)} shared rows are compared")

    report = {"n": len(cids), "fields": {}, "flags": {}, "raters": [a.name_a, a.name_b]}
    disagree = defaultdict(set)   # field -> cids
    print(f"\n{'field':22s} {'raw':>7s} {'kappa':>8s}   confusion (top disagreements)")
    for f in FIELDS:
        pairs = [(A[c].get(f), B[c].get(f)) for c in cids]
        raw = sum(1 for x, y in pairs if x == y) / len(pairs) if pairs else 0.0
        k = kappa(pairs)
        conf = Counter(pairs)
        for c, (x, y) in zip(cids, pairs):
            if x != y:
                disagree[f].add(c)
        off = sorted(((n, xy) for xy, n in conf.items() if xy[0] != xy[1]), reverse=True)[:2]
        report["fields"][f] = {"raw_agreement": raw, "kappa": k, "n_disagree": len(disagree[f]),
                               "confusion": {f"{x}|{y}": n for (x, y), n in sorted(conf.items(),
                                                                                  key=lambda t: str(t[0]))}}
        ks = f"{k:8.3f}" if k is not None else "     n/a"
        print(f"{f:22s} {raw:7.3f} {ks}   " + ", ".join(f"{x}->{y} {n}" for n, (x, y) in off))

    print(f"\n{'concession flag':22s} {'raw':>7s} {'kappa':>8s} {'pos-agr':>8s} {'neg-agr':>8s} {'prev':>6s}")
    for fl in FLAGS:
        pairs = [(truthy((A[c].get('concessions') or {}).get(fl)),
                  truthy((B[c].get('concessions') or {}).get(fl))) for c in cids]
        both = sum(1 for x, y in pairs if x and y)
        neither = sum(1 for x, y in pairs if not x and not y)
        na = sum(x for x, _ in pairs)
        nb = sum(y for _, y in pairs)
        raw = (both + neither) / len(pairs) if pairs else 0.0
        # Positive/negative agreement: 2*both / (marginal_a + marginal_b), the standard form.
        pos = 2 * both / (na + nb) if (na + nb) else None
        neg = 2 * neither / ((len(pairs) - na) + (len(pairs) - nb)) if pairs else None
        for c, (x, y) in zip(cids, pairs):
            if x != y:
                disagree[f"concession:{fl}"].add(c)
        report["flags"][fl] = {"raw_agreement": raw, "kappa": kappa(pairs), "positive_agreement": pos,
                               "negative_agreement": neg, "prevalence_a": na / len(pairs),
                               "prevalence_b": nb / len(pairs),
                               "n_disagree": len(disagree[f"concession:{fl}"])}
        k = report["flags"][fl]["kappa"]
        ks = f"{k:8.3f}" if k is not None else "     n/a"
        print(f"{fl:22s} {raw:7.3f} {ks} {(pos or 0):8.3f} {(neg or 0):8.3f} "
              f"{(na + nb) / (2 * len(pairs)):6.1%}")

    # ---- Iron-Law tripwires that need both raters
    print("\n--- Iron-Law tripwires (cross-rater)")
    for f in FIELDS:
        if abs(report["fields"][f]["raw_agreement"] - 1.0) < 1e-12 and \
                len({A[c].get(f) for c in cids}) > 1:
            print(f"  INVESTIGATE: exact 1.00 agreement on non-degenerate field {f}")
    same_span = sum(1 for c in cids
                    if sorted(v for v in (A[c].get("spans") or {}).values() if v)
                    == sorted(v for v in (B[c].get("spans") or {}).values() if v)
                    and (A[c].get("spans") or {}))
    rate = same_span / len(cids) if cids else 0
    print(f"  identical span sets: {same_span}/{len(cids)} = {rate:.1%}"
          + ("   <-- INVESTIGATE (>95%)" if rate > 0.95 else ""))

    any_dis = sorted(set().union(*disagree.values())) if disagree else []
    print(f"\nrows with at least one field disagreement: {len(any_dis)}/{len(cids)}")
    report["n_rows_any_disagreement"] = len(any_dis)

    # ---- audit set
    rng = random.Random(SEED)
    if len(any_dis) > AUDIT_N:
        strata = defaultdict(list)
        for c in any_dis:
            first = next((f for f in list(FIELDS) + [f"concession:{x}" for x in FLAGS]
                          if c in disagree[f]), "none")
            strata[(key[c]["arm"], first)].append(c)
        for v in strata.values():
            rng.shuffle(v)
        picked, order = [], sorted(strata)
        while len(picked) < AUDIT_N:
            drew = False
            for s in order:
                if strata[s] and len(picked) < AUDIT_N:
                    picked.append(strata[s].pop())
                    drew = True
            if not drew:
                break
        note = f"sampled {AUDIT_N} of {len(any_dis)} disagreements, stratified by checkpoint x field"
    else:
        picked = list(any_dis)
        agree_pool = defaultdict(list)
        for c in cids:
            if c not in set(any_dis):
                agree_pool[(key[c]["arm"], A[c].get("net_stance"))].append(c)
        for v in agree_pool.values():
            rng.shuffle(v)
        order = sorted(agree_pool)
        while len(picked) < AUDIT_N:
            drew = False
            for s in order:
                if agree_pool[s] and len(picked) < AUDIT_N:
                    picked.append(agree_pool[s].pop())
                    drew = True
            if not drew:
                break
        note = (f"all {len(any_dis)} disagreements plus {len(picked) - len(any_dis)} "
                f"checkpoint- and stance-stratified agreements")
    rng.shuffle(picked)
    print(f"audit set: {len(picked)} rows — {note}")
    report["audit"] = {"n": len(picked), "note": note, "seed": SEED, "cids": picked}

    if a.audit_out:
        if not a.items:
            raise SystemExit("--audit-out needs --items (the package dir)")
        text = {}
        for p in sorted((Path(a.items) / "shards").glob("items_part*.jsonl")):
            for line in p.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    text[r["cid"]] = r
        with Path(a.audit_out).open("w") as f:
            for c in picked:
                f.write(json.dumps({"cid": c, "request": text[c]["request"],
                                    "response": text[c]["response"]}) + "\n")
        print(f"wrote blinded audit items to {a.audit_out} (no checkpoint, no rater labels)")

    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1, default=float))
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
