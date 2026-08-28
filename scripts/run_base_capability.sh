#!/usr/bin/env bash
# Base-capability WMDP diagnostic across Marin-8b-base pretraining revisions (logprob-MC).
# Download -> eval -> delete each revision's cache (~16G) to stay within disk. Skip-logic on results.json.
# Runs AFTER Olmo-Think (shares the A100). Outputs: repro-olmo3-safety/runs/wmdp-base-<tag>/wmdp_results.json
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
source repro-olmo3-safety/.venv-safety-eval/bin/activate
export CUDA_VISIBLE_DEVICES=0
LOG=logs/base_capability_wmdp.log
echo "[$(date -Is)] base-capability WMDP diagnostic start" > "$LOG"
REPO_CACHE=~/.cache/huggingface/hub/models--marin-community--marin-8b-base

for tag in kestrel ocelot jellyfish phoenix starling deeper-starling; do
  out=repro-olmo3-safety/runs/wmdp-base-$tag
  if [ -f "$out/wmdp_results.json" ]; then echo "[$(date -Is)] SKIP $tag (done)" | tee -a "$LOG"; continue; fi
  echo "[$(date -Is)] RUN wmdp $tag" | tee -a "$LOG"
  python scripts/base_capability_wmdp.py marin-community/marin-8b-base "$tag" "$out" >> "$LOG" 2>&1
  echo "[$(date -Is)] END $tag exit=$?" | tee -a "$LOG"
  # free disk before next revision (different weights per tag)
  rm -rf "$REPO_CACHE" 2>/dev/null
done
echo "[$(date -Is)] base-capability WMDP diagnostic DONE" | tee -a "$LOG"
