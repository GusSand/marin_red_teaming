#!/bin/bash
# Stage 1, step 4: wrapper sensitivity. One SEED per job (env WRAP_SEED), 4 wrappers x {phoenix, starling}
# = 8 sequential runs on ONE GPU, under the 2h watchdog cap. Three submissions, WRAP_SEED=0,1,2.
# Spec: docs/experiments/08-28_phoenix-starling_distribution-decomposition.md (step 4)
# Submit: bash scripts/submit.sh slurm/wrapper_sensitivity.sbatch --export=ALL,WRAP_SEED=0
#SBATCH --job-name=marin-wrap
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:50:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail

WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export MARIN_RT_ROOT="$WORK"
ROOT="$WORK/repro-olmo3-safety"
export HF_HOME="$WORK/hf_cache" HF_HUB_CACHE="$WORK/hf_cache/hub" HUGGINGFACE_HUB_CACHE="$WORK/hf_cache/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"
export VLLM_ENABLE_V1_MULTIPROCESSING=0

SEED="${WRAP_SEED:?set WRAP_SEED=0|1|2}"
RUN_PREFIX="${MARIN_RUN_PREFIX:-2026-08-29-wrap-h200}"
source "$WORK/scripts/log_lib.sh"
log_init "wrap-s$SEED"
log_trap_exit

_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
log INFO "seed=$SEED gpu=$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1) host=$(hostname -s)"
export SAFETYEVAL_SAMPLING_SEED="$SEED"

for W in w0_raw w1_scaffold w2_explicit w3_fewshot_benign; do
  export TEMPLATE="$WORK/config/wrappers/$W.txt"
  [[ -f "$TEMPLATE" ]] || log_die "missing wrapper $TEMPLATE"
  for TAG in phoenix starling; do
    SHA="$(cat "$_HUB/refs/$TAG")"; MODEL="$_HUB/snapshots/$SHA"
    [[ -d "$MODEL" ]] || log_die "no snapshot for $TAG"
    NAME="${RUN_PREFIX}-${TAG}-${W}-harmbench-s${SEED}"
    RUNDIR="$ROOT/runs/$NAME"
    if [[ -s "$LABEL_ROOT/$NAME/all.json" ]]; then log INFO "skip $NAME (labels exist)"; continue; fi
    log_phase "$TAG $W s$SEED"
    log_heartbeat_start 120 "$RUNDIR/all.json"
    bash "$WORK/scripts/run_row.sh" "$MODEL" "$TAG" harmbench:default "$NAME" "$SEED" \
        || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME"; }
    log_heartbeat_stop
    [[ -s "$RUNDIR/all.json" ]] || log_die "no all.json for $NAME"
    mkdir -p "$LABEL_ROOT/$NAME" && cp -f "$RUNDIR/all.json" "$LABEL_ROOT/$NAME/all.json"
    cp -f "$TEMPLATE" "$LABEL_ROOT/$NAME/template.txt"
    if cmp -s "$RUNDIR/all.json" "$LABEL_ROOT/$NAME/all.json"; then rm -f "$RUNDIR/all.json"; ln -s "$LABEL_ROOT/$NAME/all.json" "$RUNDIR/all.json"; fi
    "$ROOT/.venv-safety-eval/bin/python" - "$RUNDIR/metrics.json" "$TAG/$W/s$SEED" <<'PY' 2>&1 | while read -r l; do log RESULT "$l"; done
import json, sys
m = json.load(open(sys.argv[1]))["harmbench:default"]
r = m["inverted_semantic_category_asr_lower"]["misinformation_disinformation"]
print(f"{sys.argv[2]}: misinfo harmful = {100*(1-r):.1f}%  ({(1-r)*54:.0f}/54)")
PY
  done
done
log INFO "seed $SEED complete: 8 runs"
