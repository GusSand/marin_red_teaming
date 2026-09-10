#!/usr/bin/env python3
"""Verify the S1-ENDORSE-V2 Part A package against the pre-registered standing gates.

Reads the built package only. Written independently of build_endorsement_feature_package.py:
it recounts from the shards and key rather than trusting provenance.json.
Gates are quoted from docs/experiments/09-10_endorsement-feature_decomposition.md.
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("package")
ap.add_argument("--parts", type=int, default=10)
a = ap.parse_args()
pkg = Path(a.package)

fails, notes = [], []
def gate(ok, msg):
    (notes if ok else fails).append(("PASS" if ok else "FAIL") + " " + msg)

rows = []
for p in range(1, a.parts + 1):
    f = pkg / "shards" / f"items_part{p}.jsonl"
    for line in f.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            r["_part"] = p
            rows.append(r)
key = json.loads((pkg / "key.json").read_text())["items"]

# 1. exactly 1,080 unique source rows and opaque IDs
gate(len(rows) == 1080, f"1,080 shard rows: {len(rows)}")
fids = [r["cid"] for r in rows]
gate(len(set(fids)) == 1080, f"unique opaque ids: {len(set(fids))}")
gate(all(re.fullmatch(r"f\d{4}", x) for x in fids), "all ids match f####")
gate(len(key) == 1080, f"key rows: {len(key)}")
gate(set(fids) == set(key), "shard ids map one-to-one onto key")
gate(len({v["source_cid"] for v in key.values()}) == 1080,
     f"unique source cids: {len({v['source_cid'] for v in key.values()})}")

# 2. 540 rows per checkpoint, 54 behaviors, 10 seeds per checkpoint-behavior cell
arms = Counter(v["arm"] for v in key.values())
gate(dict(arms) == {"phoenix": 540, "starling": 540}, f"per-checkpoint rows: {dict(arms)}")
behaviors = {v["BehaviorID"] for v in key.values()}
gate(len(behaviors) == 54, f"behaviors: {len(behaviors)}")
cells = Counter((v["arm"], v["BehaviorID"]) for v in key.values())
bad = {k: n for k, n in cells.items() if n != 10}
gate(len(cells) == 108 and not bad, f"108 checkpoint-behavior cells of 10: {len(cells)} cells, off={len(bad)}")

# 3. no prior labels or arm metadata in rater inputs
allowed = {"cid", "request", "response", "_part"}
leak = sorted({k for r in rows for k in r} - allowed)
gate(not leak, f"rater rows carry only cid/request/response (extra: {leak})")
blob = "\n".join(f"{r['cid']} {r['request']} {r['response']}" for r in rows).lower()
# Checkpoint names only. Rubric words like "endorses" occur as ordinary English inside the
# generations themselves (1 hit, f0820), so matching them measures the corpus, not leakage.
for tok in ("phoenix", "starling", "checkpoint-"):
    gate(tok not in blob, f"checkpoint token absent from rater inputs: {tok!r}")
# Leakage would arrive as a serialized prior label, not as prose.
leaked = re.findall(r'"(?:stance|category|label|subtype|net_stance|arm|run)"\s*:', blob)
gate(not leaked, f"no serialized prior label in rater text: {len(leaked)} hits")
gate("run" not in {k for r in rows for k in r}, "no run field in rater inputs")

# 4. every shard stays within one row of its checkpoint-behavior balance target
part_of = {v_id: v["part"] for v_id, v in key.items()}
gate(all(r["_part"] == part_of[r["cid"]] for r in rows), "shard membership agrees with key")
pc = Counter(part_of.values())
gate(set(pc.values()) == {108}, f"shard sizes: {sorted(pc.items())}")
cell_part = defaultdict(Counter)
for fid, v in key.items():
    cell_part[(v["arm"], v["BehaviorID"])][v["part"]] += 1
worst = 0
for cell, c in cell_part.items():
    counts = [c.get(p, 0) for p in range(1, a.parts + 1)]
    worst = max(worst, max(counts) - min(counts))
gate(worst <= 1, f"max within-cell shard imbalance: {worst} (target <=1)")
arm_part = defaultdict(Counter)
for v in key.values():
    arm_part[v["part"]][v["arm"]] += 1
gate(all(c["phoenix"] == c["starling"] == 54 for c in arm_part.values()),
     f"each shard is 54/54 by checkpoint: {sorted((p, dict(c)) for p, c in arm_part.items())[:1]}...")

# 5. boundary rule applied
bad_bound = [r["cid"] for r in rows if re.search(r"\n\s*User:", r["response"])]
gate(not bad_bound, f"boundary applied, no post-boundary turns: {len(bad_bound)} violations")
empty = [r["cid"] for r in rows if not r["response"].strip()]
notes.append(f"INFO empty bounded responses: {len(empty)}")

# 6. prompt carries the codebook and the output schema
prompt = (pkg / "PROMPT.md").read_text()
gate("## Output" in prompt and "net_stance" in prompt, "PROMPT.md carries codebook + output schema")
for tok in ("phoenix", "starling"):
    gate(tok not in prompt.lower(), f"PROMPT.md does not name {tok}")

print("\n".join(notes))
print("\n".join(fails))
print(f"\n{'PACKAGE GATES OK' if not fails else 'PACKAGE GATES FAILED'} — {len(notes)} checks noted, {len(fails)} failures")
sys.exit(1 if fails else 0)
