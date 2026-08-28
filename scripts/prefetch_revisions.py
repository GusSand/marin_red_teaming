#!/usr/bin/env python3
"""Pre-download the six marin base revisions into the workspace HF cache, ONCE, and record
the resolved commit for each. Run on the login node (it needs network); the jobs then run
fully offline (HF_HUB_OFFLINE=1), which is what freezes the weights for the study.

    HF_HOME=$SCRATCH/marin-red-teaming/hf_cache python scripts/prefetch_revisions.py

This pulls SIX 8B revisions, on the order of 100GB. That is too much to run unattended on a
login node (cluster etiquette: login nodes are for editing and submission). Either run it
detached and watch it, or submit it as a CPU-only job. It needs network, so it cannot run on a
compute node if those are air-gapped -- check before assuming. Downloads are resumable, and
a plain HF download can stall silently with no timeout, so hf_transfer is enabled below.

Why this exists:
- The jobs are offline so a gated judge (WildGuard) needs no token and cannot silently change
  under the study. But an offline job also cannot fetch the public marin weights, so they must
  be here first.
- The 07-28 runs recorded `"revision": "phoenix"` -- the tag STRING, not the commit. If a tag
  moved on the Hub between then and now, the rerun would evaluate different weights and every
  provenance file would still look identical (review finding B3). Recording the resolved SHA
  per tag, once, makes tag drift detectable: compare this file against the originals.

Writes `docs/resolved_revisions.json`: {tag: {"sha": ..., "path": ...}}.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")  # plain downloader stalled at 3.3/16GB

from huggingface_hub import HfApi, snapshot_download

REPO = "marin-community/marin-8b-base"
TAGS = ["kestrel", "ocelot", "jellyfish", "phoenix", "starling", "deeper-starling"]

ROOT = Path(os.environ.get("MARIN_RT_ROOT",
            Path(os.environ.get("SCRATCH", "/scratch/gs157")) / "marin-red-teaming"))
OUT = ROOT / "docs" / "resolved_revisions.json"

api = HfApi()
resolved = {}
for tag in TAGS:
    sha = api.model_info(REPO, revision=tag).sha
    path = snapshot_download(REPO, revision=tag, max_workers=8)  # into HF_HOME
    resolved[tag] = {"sha": sha, "path": path}
    print(f"{tag:16} {sha}  {path}", flush=True)

# The six tags MUST resolve to six different commits. If two collapse, the trajectory silently
# compares a checkpoint against itself and the whole study is meaningless -- and it would look
# like a clean result, not an error.
shas = {tag: v["sha"] for tag, v in resolved.items()}
dupes = {}
for tag, sha in shas.items():
    dupes.setdefault(sha, []).append(tag)
collided = {sha: tags for sha, tags in dupes.items() if len(tags) > 1}
if collided:
    print("\nFATAL: revisions collapse to the same commit:")
    for sha, tags in collided.items():
        print(f"  {sha[:12]} <- {', '.join(tags)}")
    sys.exit(3)
print(f"\nall {len(shas)} revisions resolve to distinct commits")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(resolved, indent=2))
print(f"\nwrote {OUT}")

# Cross-check against the original runs' provenance, if present. A tag whose SHA is not what
# the 07-28 run evaluated is a silent-weights change and must stop the reproduction.
orig_dir = ROOT / "repro-olmo3-safety" / "runs"
drift = []
for tag in TAGS:
    for r in (1, 2, 3):
        prov = orig_dir / f"2026-07-29-marin-misinfo-base-{tag}-harmbench-r{r}" / "provenance.json"
        if prov.exists():
            rev = json.loads(prov.read_text()).get("revision")
            # originals recorded the tag string, so we can only confirm the tag name matches;
            # the SHA is the new information. Flag if a future provenance starts recording SHAs.
            if rev and rev != tag and rev != resolved[tag]["sha"]:
                drift.append(f"{tag}: original provenance says {rev!r}, resolved to {resolved[tag]['sha'][:12]}")
            break
if drift:
    print("\nWARNING: possible tag drift:")
    for d in drift:
        print("  " + d)
    sys.exit(2)
print("no tag-drift signal (originals recorded tag strings; SHAs now pinned for future runs)")
