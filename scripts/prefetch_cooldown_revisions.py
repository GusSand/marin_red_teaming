#!/usr/bin/env python3
"""S1-CKPT: download the three pinned cooldown revisions and VERIFY EVERY SHARD.

Plan: docs/experiments/09-08_cooldown_localization.md (frozen 2026-09-08).

These revisions carry no animal tag, so the trajectory harness's `refs/<tag>` lookup cannot reach them.
They are fetched by explicit commit SHA, which means the usual guard against loading the wrong weights
is absent. So each downloaded safetensors shard is hashed and checked against the LFS object id recorded
in outputs/2026-09-07_cooldown-config-audit/checkpoint-evidence.json. A manifest check is NOT sufficient:
the failure that matters is silently measuring an endpoint twice.

Run on the login node (needs network); the jobs then run offline.
  HF_HOME=$SCRATCH/marin-red-teaming/hf_cache python scripts/prefetch_cooldown_revisions.py --evidence <json> --out <json>
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

REPO = "marin-community/marin-8b-base"
ENDPOINTS = {"phoenix": "5837472e", "starling": "66279e71"}

ap = argparse.ArgumentParser()
ap.add_argument("--evidence", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--verify-only", action="store_true")
a = ap.parse_args()

ev = json.load(open(a.evidence))["verified_cooldown_checkpoints"]
targets = {c["revision"]: {s["path"]: s["lfs"]["oid"] for s in c["shards"]} for c in ev}
titles = {c["revision"]: c["title"] for c in ev}

# gate: the three revisions must be distinct, and distinct from both endpoints
revs = sorted(targets)
assert len(set(revs)) == 3, f"expected 3 distinct revisions, got {revs}"
for r in revs:
    for name, pre in ENDPOINTS.items():
        assert not r.startswith(pre), f"revision {r} collides with endpoint {name}"

def sha256(p, buf=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()

from huggingface_hub import snapshot_download  # noqa: E402

report = {"repo": REPO, "revisions": {}}
ok_all = True
for rev in revs:
    print(f"\n=== {rev[:12]}  {titles[rev]} ===", flush=True)
    if not a.verify_only:
        snapshot_download(REPO, revision=rev, max_workers=4,
                          allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model"])
    from huggingface_hub import snapshot_download as _sd
    local = _sd(REPO, revision=rev, local_files_only=True,
                allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model"])
    shards = {}
    for path, oid in sorted(targets[rev].items()):
        f = Path(local) / path
        if not f.exists():
            shards[path] = {"present": False}; ok_all = False
            print(f"  MISSING {path}", flush=True); continue
        got = sha256(f)
        match = (got == oid)
        ok_all &= match
        shards[path] = {"present": True, "sha256": got, "expected_lfs_oid": oid, "match": match,
                        "bytes": f.stat().st_size}
        print(f"  {'OK  ' if match else 'FAIL'} {path}  {got[:16]}", flush=True)
    report["revisions"][rev] = {"title": titles[rev], "snapshot": local,
                                "all_shards_verified": all(s.get("match") for s in shards.values()),
                                "shards": shards}

report["all_revisions_verified"] = ok_all
report["distinct_from_endpoints"] = True
Path(a.out).write_text(json.dumps(report, indent=1) + "\n")
print(f"\nVERIFIED: {ok_all}  ->  {a.out}")
sys.exit(0 if ok_all else 4)
