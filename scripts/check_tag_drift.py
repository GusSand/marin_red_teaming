#!/usr/bin/env python3
"""Compare the HF cache's resolved tag SHAs against the reconstructed baseline.

Why this exists: the 2026-09-09 rsync --delete incident destroyed the workspace HF cache and the
original docs/resolved_revisions.json. The baseline was reconstructed from surviving job logs
(docs/resolved_revisions_reconstructed.json) -- those SHAs are the weights every recorded result
was actually produced on. A re-download that resolves a tag to a DIFFERENT commit means the tag
moved on the Hub, and every comparison against a recorded run is then invalid while looking
identical in every provenance file.

Run on Torch, where the cache lives:
    HF_HOME=$SCRATCH/marin-red-teaming/hf_cache python3 scripts/check_tag_drift.py
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / "docs" / "resolved_revisions_reconstructed.json").read_text())
hub = Path(os.environ.get("HF_HOME", "/scratch/gs157/marin-red-teaming/hf_cache")) / "hub"
repo = hub / "models--marin-community--marin-8b-base"

if not repo.is_dir():
    sys.exit(f"FAIL: no cached repo at {repo}")

problems, checked = [], 0
for tag, want in base["tags"].items():
    ref = repo / "refs" / tag
    if not ref.exists():
        problems.append(f"{tag}: no ref file (not downloaded yet)")
        continue
    have = ref.read_text().strip()
    checked += 1
    if have != want:
        problems.append(f"TAG DRIFT {tag}: cache resolves {have}, recorded runs used {want}")
    if not (repo / "snapshots" / want).is_dir():
        problems.append(f"{tag}: snapshot dir for the recorded SHA {want[:12]} is absent")

# The cooldown revisions have no refs; they are addressed by SHA, so presence is the only check.
for label, sha in base["cooldown_revisions"].items():
    if not (repo / "snapshots" / sha).is_dir():
        problems.append(f"{label}: snapshot {sha[:12]} not present")
    else:
        checked += 1

for p in problems:
    print(p)
if any(p.startswith("TAG DRIFT") for p in problems):
    sys.exit("\nTAG DRIFT DETECTED. Do not run anything comparative until this is resolved.")
if problems:
    sys.exit(f"\n{len(problems)} item(s) still missing; re-download incomplete.")
print(f"TAG DRIFT CHECK OK — {checked} revisions match the SHAs the recorded results were produced on")
