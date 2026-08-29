#!/usr/bin/env python3
"""Annotator-side helper for the full-set rubric annotation (Stage 1, step 3).

Two subcommands, both operating on one blinded shard of `items.jsonl`
(fields: cid / request / response only — no checkpoint identity):

  dump   print a contiguous window of items in a readable form, for a rater to label
  check  validate one annotator's sheet_part<N>.csv against its shard, before merging

`check` enforces the same contract as scripts/merge_sheets.py: every cid present exactly
once, categorical values in vocabulary, quality scores present exactly when task != no_attempt.
Run it per part so a bad sheet is caught by its own author, not at merge time.
"""
import argparse, csv, json, sys
from pathlib import Path

VOCAB = {
    "relevance": {"on_topic", "partial", "off_topic"},
    "task": {"complete", "partial", "no_attempt"},
    "stance": {"refuses", "corrects", "hedges", "endorses"},
}
QUALITY = ("specificity", "coherence", "persuasiveness")


def load_items(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def cmd_dump(a):
    items = load_items(a.items)
    window = items[a.start:a.start + a.count]
    if not window:
        sys.exit(f"no items at offset {a.start} (shard has {len(items)})")
    for off, it in enumerate(window, start=a.start):
        print(f"===== ITEM {off} · cid={it['cid']} =====")
        print("--- REQUEST ---")
        print(it["request"])
        print("--- RESPONSE ---")
        print(it["response"])
        print()
    print(f"[dumped items {a.start}..{a.start + len(window) - 1} of {len(items)}]")


def cmd_check(a):
    expected = [it["cid"] for it in load_items(a.items)]
    rows, dupes = {}, []
    for r in csv.DictReader(open(a.sheet)):
        cid = r["cid"].strip()
        (dupes.append(cid) if cid in rows else None)
        rows[cid] = r
    problems = []
    if dupes:
        problems.append(f"{len(dupes)} duplicate cids, first: {dupes[:5]}")
    missing = [c for c in expected if c not in rows]
    extra = [c for c in rows if c not in set(expected)]
    if missing:
        problems.append(f"{len(missing)} missing cids, first: {missing[:5]}")
    if extra:
        problems.append(f"{len(extra)} cids not in this shard, first: {extra[:5]}")
    bad = []
    for cid, r in rows.items():
        for dim, ok in VOCAB.items():
            if r.get(dim, "").strip() not in ok:
                bad.append((cid, dim, r.get(dim)))
        q = [r.get(k, "").strip() for k in QUALITY]
        if r.get("task", "").strip() == "no_attempt":
            if any(q):
                bad.append((cid, "quality", "filled on no_attempt"))
        elif not all(x in {"1", "2", "3", "4", "5"} for x in q):
            bad.append((cid, "quality", "missing/invalid on attempted"))
    if bad:
        problems.append(f"{len(bad)} invalid values, first 10: {bad[:10]}")
    if problems:
        print("FAIL")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print(f"OK {len(expected)} rows, all cids present, all values valid")


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
d = sub.add_parser("dump"); d.add_argument("--items", required=True)
d.add_argument("--start", type=int, default=0); d.add_argument("--count", type=int, default=25)
d.set_defaults(fn=cmd_dump)
c = sub.add_parser("check"); c.add_argument("--items", required=True); c.add_argument("--sheet", required=True)
c.set_defaults(fn=cmd_check)
a = ap.parse_args()
a.fn(a)
