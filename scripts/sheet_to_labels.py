#!/usr/bin/env python3
"""Convert a returned flat rater sheet into the S1-ENDORSE-V2 label JSONL, and back.

The flat CSV is a fallback return path for rater interfaces that cannot emit `.jsonl`. The validator
and the analysis consume JSONL only, so everything funnels through here.

--selftest runs labels -> sheet -> labels on a real label file and asserts the canonical form survives
the round trip. That is the check that matters: it proves the sheet schema can carry every value the
codebook allows, on real data rather than on an example.
"""
import argparse, csv, json, re, sys
from pathlib import Path

FLAGS = ("moral", "social", "legal", "stylistic", "opposing_view")
FIELDS = ("boundary_confidence", "net_stance", "assertion_form", "claim_uncertainty",
          "attribution", "added_support", "final_takeaway")
SPAN_FIELDS = ("net_stance", "assertion_form", "claim_uncertainty", "attribution",
               "added_support", "final_takeaway")
COLS = (["cid"] + list(FIELDS[:4]) + [f"conc_{f}" for f in FLAGS] + list(FIELDS[4:])
        + [f"span_{f}" for f in ("net_stance", "assertion_form", "claim_uncertainty")]
        + [f"span_{f}" for f in FLAGS]
        + [f"span_{f}" for f in ("attribution", "added_support", "final_takeaway")] + ["notes"])
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower())
truthy = lambda v: v is True or (isinstance(v, str) and v.strip().lower() in ("true", "1", "yes", "y"))


def canonical(rec):
    """The comparable form of a label row: primitive values plus canonically-keyed spans.

    Rater span keys are free-form ("concession_moral", "moral_span", "spanMoral"), so a round trip
    cannot preserve key spelling. It must preserve every value, keyed canonically.
    """
    spans = {}
    for k, v in (rec.get("spans") or {}).items():
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        n = norm(k)
        # A concession flag wins first: its names ("moral", "concession_moral", "spanMoral") never
        # collide with a primitive field name, whereas a loose primitive match would swallow them.
        flag = next((f for f in FLAGS if norm(f) in n), None)
        field = next((x for x in SPAN_FIELDS if norm(x) in n or n in norm(x)), None)
        target = flag or field
        if target:
            spans[target] = v
    conc = rec.get("concessions") or {}
    return {"cid": rec["cid"],
            **{f: rec.get(f) for f in FIELDS},
            "concessions": {f: bool(truthy(conc.get(f))) for f in FLAGS},
            "spans": spans}


def labels_to_sheet(rows, path):
    with Path(path).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            c = canonical(r)
            out = [c["cid"]] + [c[f] or "" for f in FIELDS[:4]]
            out += ["true" if c["concessions"][f] else "false" for f in FLAGS]
            out += [c[f] or "" for f in FIELDS[4:]]
            out += [c["spans"].get(f, "") for f in
                    ("net_stance", "assertion_form", "claim_uncertainty")]
            out += [c["spans"].get(f, "") for f in FLAGS]
            out += [c["spans"].get(f, "") for f in ("attribution", "added_support", "final_takeaway")]
            w.writerow(out + [""])


def sheet_to_labels(path):
    rows, bad = [], []
    with Path(path).open(newline="") as f:
        rd = csv.DictReader(f)
        missing = [c for c in COLS if c not in (rd.fieldnames or [])]
        if missing:
            raise SystemExit(f"REFUSING: sheet is missing columns {missing}\n"
                             f"expected header, verbatim:\n{','.join(COLS)}")
        for i, r in enumerate(rd, 2):
            cid = (r.get("cid") or "").strip()
            if not cid:
                bad.append(f"line {i}: blank cid")
                continue
            spans = {}
            for f in SPAN_FIELDS:
                v = (r.get(f"span_{f}") or "").strip()
                spans[f] = v or None
            for f in FLAGS:
                v = (r.get(f"span_{f}") or "").strip()
                spans[f] = v or None
            rows.append({"cid": cid,
                         **{f: (r.get(f) or "").strip() or None for f in FIELDS},
                         "concessions": {f: truthy(r.get(f"conc_{f}")) for f in FLAGS},
                         "spans": spans})
    if bad:
        raise SystemExit("REFUSING:\n" + "\n".join(bad))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet")
    ap.add_argument("--out")
    ap.add_argument("--selftest", metavar="LABELS_JSONL",
                    help="round-trip a real label file through the sheet schema")
    a = ap.parse_args()

    if a.selftest:
        src = [json.loads(l) for l in Path(a.selftest).read_text().splitlines() if l.strip()]
        tmp = Path(a.selftest).with_suffix(".selftest.csv")
        labels_to_sheet(src, tmp)
        back = sheet_to_labels(tmp)
        tmp.unlink()
        if len(src) != len(back):
            raise SystemExit(f"SELFTEST FAILED: {len(src)} in, {len(back)} out")
        diffs = []
        for x, y in zip(sorted(src, key=lambda r: r["cid"]), sorted(back, key=lambda r: r["cid"])):
            cx, cy = canonical(x), canonical(y)
            if cx != cy:
                for k in cx:
                    if cx[k] != cy.get(k):
                        diffs.append((x["cid"], k, cx[k], cy.get(k)))
        if diffs:
            print(f"SELFTEST FAILED: {len(diffs)} field differences after round trip")
            for d in diffs[:5]:
                print("  ", d)
            return 1
        print(f"SELFTEST OK — {len(src)} rows survive labels -> sheet -> labels unchanged "
              f"in canonical form ({len(COLS)} columns)")
        return 0

    if not (a.sheet and a.out):
        raise SystemExit("need --sheet and --out, or --selftest")
    rows = sheet_to_labels(a.sheet)
    Path(a.out).write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    print(f"wrote {len(rows)} rows to {a.out}")
    print("now validate it: python3 scripts/check_endorsement_labels.py --package <pkg> "
          f"--labels {a.out} --shard-items <pkg>/shards/items_part<N>.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
