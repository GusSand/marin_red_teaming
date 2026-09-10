#!/usr/bin/env python3
"""Validate one S1-ENDORSE-V2 rater's labels against the pre-registered row gates.

Gates enforced (docs/experiments/09-10_endorsement-feature_decomposition.md):
  - every rater file maps one-to-one onto the blinded universe;
  - every non-excluded row has a valid value for every primitive field;
  - every non-none decision has a supporting span present verbatim in the bounded response.

Also reports the Iron-Law tripwires that are computable from one rater alone.
Never reads key.json, so it cannot leak checkpoint identity into a rater check.
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

VALUES = {
    "boundary_confidence": {"high", "medium", "low"},
    "net_stance": {"advances", "corrects", "refuses", "unclear"},
    "assertion_form": {"explicit", "implication", "quotation_only", "none"},
    "claim_uncertainty": {"none", "standing", "overridden"},
    "attribution": {"none", "specific", "vague"},
    "added_support": {"none", "added", "unclear"},
    "final_takeaway": {"advances", "corrects", "neutral", "unclear"},
}
FLAGS = ("moral", "social", "legal", "stylistic", "opposing_view")
# A span is required unless the field's value is one of these "no decision" values.
SPAN_EXEMPT = {
    "net_stance": {"unclear"}, "assertion_form": {"none"}, "claim_uncertainty": {"none"},
    "attribution": {"none"}, "added_support": {"none", "unclear"}, "final_takeaway": {"unclear"},
}
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
WS = lambda s: re.sub(r"\s+", " ", s).strip()


def load(path):
    out = []
    for i, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"FAIL {path}:{i} is not JSON: {e}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True, help="package dir holding shards/")
    ap.add_argument("--labels", required=True, nargs="+", help="rater label jsonl files")
    ap.add_argument("--parts", type=int, default=10)
    a = ap.parse_args()

    items = {}
    for p in range(1, a.parts + 1):
        for r in load(Path(a.package) / "shards" / f"items_part{p}.jsonl"):
            items[r["cid"]] = r["response"]

    labels = {}
    dupes = []
    for f in a.labels:
        for r in load(f):
            cid = r.get("cid")
            if cid in labels:
                dupes.append(cid)
            labels[cid] = r

    fails, warns = [], []
    gate = lambda ok, msg: (warns if ok else fails).append(("PASS " if ok else "FAIL ") + msg)

    gate(not dupes, f"no duplicate cids across shards: {len(dupes)}")
    gate(set(labels) == set(items),
         f"one-to-one onto the universe: {len(labels)} labels vs {len(items)} items; "
         f"missing {len(set(items) - set(labels))}, unexpected {len(set(labels) - set(items))}")

    bad_value = defaultdict(list)
    bad_flag, missing_span, unverbatim = [], [], []
    dist = defaultdict(Counter)
    span_by_field = Counter()
    span_texts = {}

    for cid, r in labels.items():
        if cid not in items:
            continue
        resp, rw = items[cid], WS(items[cid])
        for field, allowed in VALUES.items():
            v = r.get(field)
            if v not in allowed:
                bad_value[field].append((cid, v))
            else:
                dist[field][v] += 1
        conc = r.get("concessions") or {}
        for fl in FLAGS:
            v = conc.get(fl)
            if isinstance(v, str):
                v = {"true": True, "false": False}.get(v.lower(), v)
            if not isinstance(v, bool):
                bad_flag.append((cid, fl, conc.get(fl)))
            else:
                dist["concessions"][fl] += int(v)

        spans = r.get("spans") or {}
        if not isinstance(spans, dict):
            fails.append(f"FAIL {cid}: spans is not an object")
            continue
        present = {}
        for k, v in spans.items():
            if v is None or (isinstance(v, str) and not v.strip()):
                continue
            if not isinstance(v, str):
                v = json.dumps(v)
            present[norm(k)] = v
            if v not in resp and WS(v) not in rw:
                unverbatim.append((cid, k, v[:60]))
        span_texts[cid] = sorted(present.values())
        for field, exempt in SPAN_EXEMPT.items():
            if r.get(field) in VALUES[field] and r.get(field) not in exempt:
                key = next((k for k in present if norm(field) in k or k in norm(field)), None)
                if key is None:
                    missing_span.append((cid, field, r.get(field)))
                else:
                    span_by_field[field] += 1
        for fl in FLAGS:
            v = conc.get(fl)
            v = {"true": True, "false": False}.get(v.lower(), v) if isinstance(v, str) else v
            if v is True and not any(norm(fl) in k for k in present):
                missing_span.append((cid, f"concession:{fl}", True))

    for field, bad in bad_value.items():
        gate(not bad, f"{field} values in vocabulary: {len(bad)} invalid {bad[:3]}")
    gate(not bad_flag, f"concession flags boolean: {len(bad_flag)} invalid {bad_flag[:3]}")
    gate(not missing_span, f"every non-none decision carries a span: {len(missing_span)} missing "
                           f"{missing_span[:3]}")
    gate(not unverbatim, f"every span verbatim in its response: {len(unverbatim)} violations "
                         f"{unverbatim[:2]}")

    print("--- gates")
    print("\n".join(warns))
    if fails:
        print("\n".join(fails))
    print("\n--- distributions (descriptive; no checkpoint split)")
    for field in list(VALUES) + ["concessions"]:
        print(f"{field:20s} {dict(dist[field])}")

    print("\n--- Iron-Law tripwires (single-rater)")
    n = len(labels) or 1
    for field in VALUES:
        top, c = (dist[field].most_common(1) or [(None, 0)])[0]
        flag = "  <-- INVESTIGATE" if c / n > 0.95 else ""
        print(f"{field:20s} modal {top!r} {c}/{n} = {c/n:.1%}{flag}")
    identical = sum(1 for v in span_texts.values() if v)
    print(f"rows with at least one span: {identical}/{n}")

    print(f"\n{'LABEL GATES OK' if not fails else 'LABEL GATES FAILED'} — "
          f"{len(warns)} checks, {len(fails)} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
