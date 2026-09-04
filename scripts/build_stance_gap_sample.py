#!/usr/bin/env python3
"""Build the blinded restatement-prevalence sample (S1-STANCE-GAP, experiment 09-04).

Stratified random sample of the 1,080, by ARM ONLY -- never by any pass-2 label, which would bias the
prevalence estimate toward whichever classes the artefact hides in. Items are re-cid'd to shuffled
`r####` because the full-set `i####` ids are run-ordered and would leak the arm to the rater, the defect
that confounded pass 1.

Responses are truncated at the first fabricated `User:` turn (convention 1), matching the pass-2
annotation this is auditing.

Shards are balanced on arm so an annotator is never confounded with a checkpoint. A seeded 10% of items
is duplicated into a different shard for within-rater agreement.

Writes, all OUTSIDE the repo:
  <out>/shards/items_part<N>.jsonl   blinded rater input: cid / request / response only
  <out>/key.json                     r-cid -> i-cid, run, arm, BehaviorID, is_duplicate
  <out>/provenance.json              seed, counts, balance check, source paths
Never writes any pass-2 label into the shards.

Usage:
  build_stance_gap_sample.py --full <full_phoenix_starling_v1> --out <dir> [--n 240] [--parts 4]
"""
import argparse, json, random, re
from collections import Counter
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--full", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=240); ap.add_argument("--parts", type=int, default=4)
ap.add_argument("--dup-frac", type=float, default=0.10); ap.add_argument("--seed", type=int, default=20260828)
a = ap.parse_args()

full, out = Path(a.full), Path(a.out)
if (out / "key.json").exists():
    raise SystemExit(f"REFUSING: {out}/key.json exists")

items = {json.loads(l)["cid"]: json.loads(l) for l in (full / "items.jsonl").read_text().splitlines() if l.strip()}
key = json.load(open(full / "key.json"))["items"]

def arm(run):
    for t in ("phoenix", "starling"):
        if re.search(rf"-{t}-", run):
            return t
    return None

def truncate(resp):
    """Convention 1: judge only the text before the first fabricated `User:` turn."""
    m = re.search(r"\n\s*User:", resp)
    return resp[: m.start()] if m else resp

pool = {t: sorted(c for c, k in key.items() if arm(k["run"]) == t) for t in ("phoenix", "starling")}
rng = random.Random(a.seed)
per = a.n // 2
picked = []
for t in ("phoenix", "starling"):
    if len(pool[t]) < per:
        raise SystemExit(f"{t} pool has {len(pool[t])} < {per}")
    picked += rng.sample(pool[t], per)
rng.shuffle(picked)

ndup = int(round(a.n * a.dup_frac))
dups = rng.sample(picked, ndup)

# assign r-cids over the real items, then append duplicates with their own r-cids
records, kmap = [], {}
for i, icid in enumerate(picked):
    rcid = f"r{i:04d}"
    records.append((rcid, icid, False))
for j, icid in enumerate(dups):
    records.append((f"r{a.n + j:04d}", icid, True))
rng.shuffle(records)

# Assign parts round-robin WITHIN each arm, so every shard is arm-balanced. A global round-robin over a
# shuffled list leaves shards up to ~10pp imbalanced, which breaches the pre-registered +/-5pp gate and
# would partially reconfound annotator with checkpoint -- the pass-1 defect.
part_of, arm_of = {}, {r: arm(key[i]["run"]) for r, i, _ in records}
for t in ("phoenix", "starling"):
    rs = sorted(r for r, i, d in records if not d and arm_of[r] == t)
    rng.shuffle(rs)
    for idx, r in enumerate(rs):
        part_of[r] = idx % a.parts
orig_part = {i: part_of[r] for r, i, d in records if not d}
# each duplicate goes to the emptiest part for its arm that is not its original's part
for rcid, icid, isdup in records:
    if not isdup:
        continue
    load = {p: sum(1 for r, pp in part_of.items() if pp == p and arm_of[r] == arm_of[rcid])
            for p in range(a.parts) if p != orig_part[icid]}
    part_of[rcid] = min(load, key=load.get)

shards = {p: [] for p in range(a.parts)}
for rcid, icid, isdup in records:
    shards[part_of[rcid]].append((rcid, icid, isdup))
    kmap[rcid] = {"i_cid": icid, "run": key[icid]["run"], "arm": arm(key[icid]["run"]),
                  "BehaviorID": key[icid]["BehaviorID"], "is_duplicate": isdup,
                  "part": part_of[rcid]}

(out / "shards").mkdir(parents=True, exist_ok=True)
for p, rows in shards.items():
    with (out / "shards" / f"items_part{p + 1}.jsonl").open("w") as f:
        for rcid, icid, _ in sorted(rows):
            f.write(json.dumps({"cid": rcid, "request": items[icid]["request"],
                                "response": truncate(items[icid]["response"])}) + "\n")

bal = {p + 1: dict(Counter(kmap[r]["arm"] for r, _, _ in rows)) for p, rows in shards.items()}
overall = Counter(v["arm"] for v in kmap.values())
worst = max(abs(b.get("phoenix", 0) / max(sum(b.values()), 1) - 0.5) for b in bal.values())
dup_ok = all(kmap[r]["part"] != orig_part[kmap[r]["i_cid"]] for r in kmap if kmap[r]["is_duplicate"])

prov = {"experiment": "docs/experiments/09-04_stance-gap_restatement-prevalence.md",
        "seed": a.seed, "n_sampled": a.n, "n_duplicates": ndup, "parts": a.parts,
        "source": str(full), "arm_counts": dict(overall), "shard_arm_balance": bal,
        "worst_shard_arm_imbalance_pp": round(100 * worst, 1),
        "every_duplicate_in_a_different_shard": dup_ok,
        "unique_source_items": len(set(v["i_cid"] for v in kmap.values())),
        "behaviors_covered": len({v["BehaviorID"] for v in kmap.values()}),
        "convention": "responses truncated at the first fabricated `User:` turn (convention 1)"}
(out / "key.json").write_text(json.dumps({"items": kmap}, indent=1))
(out / "provenance.json").write_text(json.dumps(prov, indent=1))
print(json.dumps(prov, indent=1))
