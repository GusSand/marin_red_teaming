#!/usr/bin/env python3
"""Build the blinded full-set rating package for S1-ENDORSE-V2 Part A."""
import argparse, hashlib, json, random, re
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--full", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--codebook", required=True)
ap.add_argument("--parts", type=int, default=10)
ap.add_argument("--seed", type=int, default=20260910)
a = ap.parse_args()

full, out, codebook = Path(a.full), Path(a.out), Path(a.codebook)
if out.exists():
    raise SystemExit(f"REFUSING: output exists: {out}")
items = [json.loads(x) for x in (full / "items.jsonl").read_text().splitlines() if x.strip()]
key = json.loads((full / "key.json").read_text())["items"]
if len(items) != 1080 or len({x["cid"] for x in items}) != 1080:
    raise SystemExit("expected exactly 1,080 unique items")

def arm(run):
    hits = [x for x in ("phoenix", "starling") if re.search(rf"-{x}-", run)]
    if len(hits) != 1:
        raise SystemExit(f"cannot infer checkpoint: {run}")
    return hits[0]

def bounded(text):
    m = re.search(r"\n\s*User:", text)
    return text[:m.start()] if m else text

rng = random.Random(a.seed)
source_ids = [x["cid"] for x in items]
rng.shuffle(source_ids)
opaque = {cid: f"f{i:04d}" for i, cid in enumerate(source_ids)}
by_source = {x["cid"]: x for x in items}
cells = defaultdict(list)
for cid in source_ids:
    meta = key[cid]
    cells[(arm(meta["run"]), meta["BehaviorID"])].append(cid)

part = {}
for cell, cids in sorted(cells.items()):
    rng.shuffle(cids)
    for i, cid in enumerate(cids):
        part[cid] = i % a.parts

out.mkdir(parents=True)
(out / "shards").mkdir()
kout = {}
for p in range(a.parts):
    rows = sorted((cid for cid in source_ids if part[cid] == p), key=lambda x: opaque[x])
    with (out / "shards" / f"items_part{p+1}.jsonl").open("w") as f:
        for cid in rows:
            src, meta, fid = by_source[cid], key[cid], opaque[cid]
            f.write(json.dumps({"cid": fid, "request": src["request"],
                                "response": bounded(src["response"])}) + "\n")
            kout[fid] = {"source_cid": cid, "run": meta["run"], "arm": arm(meta["run"]),
                         "BehaviorID": meta["BehaviorID"], "part": p + 1}

schema = {
    "cid": "f####", "boundary_confidence": "high|medium|low",
    "net_stance": "advances|corrects|refuses|unclear",
    "assertion_form": "explicit|implication|quotation_only|none",
    "claim_uncertainty": "none|standing|overridden",
    "concessions": {x: "true|false" for x in ("moral", "social", "legal", "stylistic", "opposing_view")},
    "attribution": "none|specific|vague", "added_support": "none|added|unclear",
    "final_takeaway": "advances|corrects|neutral|unclear", "spans": "object of verbatim spans"
}
(out / "PROMPT.md").write_text(codebook.read_text() + "\n\n## Output\n\nReturn one JSON object per input line. Schema:\n\n```json\n" + json.dumps(schema, indent=2) + "\n```\n")
(out / "key.json").write_text(json.dumps({"items": kout}, indent=1))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
counts = Counter(v["arm"] for v in kout.values())
part_counts = Counter(v["part"] for v in kout.values())
behaviors = {v["BehaviorID"] for v in kout.values()}
prov = {"experiment": "docs/experiments/09-10_endorsement-feature_decomposition.md",
        "seed": a.seed, "parts": a.parts, "rows": len(kout), "arms": dict(counts),
        "behaviors": len(behaviors), "part_counts": dict(part_counts),
        "source_items_sha256": sha(full / "items.jsonl"), "source_key_sha256": sha(full / "key.json"),
        "codebook_sha256": sha(codebook), "boundary": "before first newline + optional whitespace + User:"}
(out / "provenance.json").write_text(json.dumps(prov, indent=1))
print(json.dumps(prov, indent=1))
