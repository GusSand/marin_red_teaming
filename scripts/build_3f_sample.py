#!/usr/bin/env python3
"""Build the blinded concessionary-endorsement package (S1-3F, experiment 09-04).

Universe: every response the pass-2 blind annotator labelled `stance=endorses`. The sub-rubric is
ADDITIVE -- it subdivides that class and never overturns another stance -- so the universe is fixed by
the pass-2 labels and is not sampled.

Blinding: re-cid'd to shuffled `e####`; the run-ordered `i####` ids would leak the arm. Responses are
truncated at the first fabricated `User:` turn (convention 1), matching pass 2.

Shards are balanced on arm so an annotator is never confounded with a checkpoint. A seeded 10% is
duplicated into a DIFFERENT shard for within-rater agreement.

Writes, outside the repo:
  <out>/shards/items_part<N>.jsonl   blinded rater input: cid / request / response only
  <out>/key.json                     e-cid -> i-cid, run, arm, BehaviorID, is_duplicate, part
  <out>/provenance.json              seed, counts, balance, source paths
No pass-2 label is ever written into a shard.

Usage: build_3f_sample.py --full <full_phoenix_starling_v1> --out <dir> [--parts 6]
"""
import argparse, json, random, re
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--full", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--parts", type=int, default=6)
ap.add_argument("--dup-frac", type=float, default=0.10); ap.add_argument("--seed", type=int, default=20260828)
a = ap.parse_args()

full, out = Path(a.full), Path(a.out)
if (out / "key.json").exists():
    raise SystemExit(f"REFUSING: {out}/key.json exists")

items = {json.loads(l)["cid"]: json.loads(l) for l in (full / "items.jsonl").read_text().splitlines() if l.strip()}
key = json.load(open(full / "key.json"))["items"]
J = {json.loads(l)["cid"]: json.loads(l)
     for l in (full / "judge" / "claude_fable_pass2.jsonl").read_text().splitlines() if l.strip()}

def arm(run):
    for t in ("phoenix", "starling"):
        if re.search(rf"-{t}-", run):
            return t

def truncate(resp):
    m = re.search(r"\n\s*User:", resp)
    return resp[: m.start()] if m else resp

universe = sorted(c for c, r in J.items() if r.get("stance") == "endorses")
rng = random.Random(a.seed)
ndup = int(round(len(universe) * a.dup_frac))
dups = rng.sample(universe, ndup)

records = [(None, c, False) for c in universe] + [(None, c, True) for c in dups]
order = list(range(len(records)))
rng.shuffle(order)
records = [(f"e{i:04d}", records[o][1], records[o][2]) for i, o in enumerate(order)]

arm_of = {r: arm(key[i]["run"]) for r, i, _ in records}
part_of = {}
for t in ("phoenix", "starling"):                       # round-robin WITHIN arm -> balanced shards
    rs = sorted(r for r, i, d in records if not d and arm_of[r] == t)
    rng.shuffle(rs)
    for idx, r in enumerate(rs):
        part_of[r] = idx % a.parts
orig_part = {i: part_of[r] for r, i, d in records if not d}
for rcid, icid, isdup in records:                       # duplicates -> emptiest OTHER shard for that arm
    if not isdup:
        continue
    load = {p: sum(1 for r, pp in part_of.items() if pp == p and arm_of[r] == arm_of[rcid])
            for p in range(a.parts) if p != orig_part[icid]}
    part_of[rcid] = min(load, key=load.get)

kmap = {r: {"i_cid": i, "run": key[i]["run"], "arm": arm_of[r], "BehaviorID": key[i]["BehaviorID"],
            "is_duplicate": d, "part": part_of[r]} for r, i, d in records}

(out / "shards").mkdir(parents=True, exist_ok=True)
for p in range(a.parts):
    rows = sorted(r for r in kmap if kmap[r]["part"] == p)
    with (out / "shards" / f"items_part{p + 1}.jsonl").open("w") as f:
        for r in rows:
            i = kmap[r]["i_cid"]
            f.write(json.dumps({"cid": r, "request": items[i]["request"],
                                "response": truncate(items[i]["response"])}) + "\n")

bal = {p + 1: dict(Counter(kmap[r]["arm"] for r in kmap if kmap[r]["part"] == p)) for p in range(a.parts)}
# The gate's purpose is that no shard is arm-skewed RELATIVE TO THE UNIVERSE, so annotator is never
# confounded with checkpoint. The endorses universe is itself 160/309, not 50/50, so measuring deviation
# from 0.5 would flag a correctly balanced split. Measure against the universe proportion.
uni = Counter(arm(key[c]["run"]) for c in universe)
target = uni["phoenix"] / sum(uni.values())
worst = max(abs(b.get("phoenix", 0) / max(sum(b.values()), 1) - target) for b in bal.values())
prov = {"experiment": "docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md",
        "seed": a.seed, "universe_endorses": len(universe), "n_duplicates": ndup,
        "n_rated_rows": len(records), "parts": a.parts, "source": str(full),
        "arm_counts_universe": dict(Counter(arm(key[c]["run"]) for c in universe)),
        "shard_arm_balance": bal, "universe_phoenix_share_pct": round(100 * target, 1),
        "worst_shard_deviation_from_universe_pp": round(100 * worst, 1),
        "every_duplicate_in_a_different_shard":
            all(kmap[r]["part"] != orig_part[kmap[r]["i_cid"]] for r in kmap if kmap[r]["is_duplicate"]),
        "behaviors_covered": len({v["BehaviorID"] for v in kmap.values()}),
        "convention": "truncated at the first fabricated `User:` turn (convention 1)"}
(out / "key.json").write_text(json.dumps({"items": kmap}, indent=1))
(out / "provenance.json").write_text(json.dumps(prov, indent=1))
print(json.dumps(prov, indent=1))
