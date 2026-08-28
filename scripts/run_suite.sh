#!/usr/bin/env bash
# Generic suite runner: run a list of "folder:config" rows x 3 seeds on one model.
# Sequential (single GPU). Each row via run_row.sh (own provenance + no-overwrite).
# Usage:
#   scripts/run_suite.sh <model_repo> <revision> <label_prefix> "<folder:config> <folder:config> ..."
# Example (Olmo Instruct Gate 4+5):
#   scripts/run_suite.sh allenai/Olmo-3-7B-Instruct main 2026-07-26-instruct \
#     "wildjailbreak:harmful wildjailbreak:benign trustllm_jailbreaktrigger:default bbq:default strongreject:logprobs toxigen:default wmdp:default"
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
MODEL="${1:?model}"; REV="${2:?revision}"; PREFIX="${3:?label prefix}"; CONFIGS="${4:?space-separated folder:config list}"
DRIVERLOG="logs/${PREFIX}_suite_driver.log"
echo "[$(date -Is)] suite start model=$MODEL prefix=$PREFIX" > "$DRIVERLOG"

for spec in $CONFIGS; do
  folder="${spec%%:*}"; cfg="${spec##*:}"
  # short bench label = folder with underscores collapsed + config if not 'default'
  blabel="$folder"; [ "$cfg" != "default" ] && blabel="${folder}-${cfg}"
  blabel="$(echo "$blabel" | tr '_' '-')"
  for seed in 0 1 2; do
    rn=$((seed+1))
    name="${PREFIX}-${blabel}-r${rn}"
    if [ -f "repro-olmo3-safety/runs/${name}/metrics.json" ]; then
      echo "[$(date -Is)] SKIP ${name} (exists)" | tee -a "$DRIVERLOG"; continue
    fi
    echo "[$(date -Is)] RUN ${name} task=${spec} seed=${seed}" | tee -a "$DRIVERLOG"
    bash scripts/run_row.sh "$MODEL" "$REV" "$spec" "$name" "$seed" > "logs/${name}.outer.log" 2>&1
    echo "[$(date -Is)] END ${name} exit=$?" | tee -a "$DRIVERLOG"
  done
done
echo "[$(date -Is)] suite DONE prefix=$PREFIX" | tee -a "$DRIVERLOG"
