#!/bin/bash
# LABEL COMPLETION for the 08-27 trajectory study: re-judge the 18 non-empty responses that
# WildGuard left unlabelled, with the identical pinned judge. Not a rerun. Originals untouched;
# results go to rejudge.json sidecars. gs157, 2026-08-28.
#SBATCH --job-name=marin-rejudge
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"; export MARIN_RT_ROOT="$WORK"
ROOT="$WORK/repro-olmo3-safety"
export HF_HOME="$WORK/hf_cache" HF_HUB_CACHE="$WORK/hf_cache/hub" HUGGINGFACE_HUB_CACHE="$WORK/hf_cache/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"
export VLLM_ENABLE_V1_MULTIPROCESSING=0
source "$WORK/scripts/log_lib.sh"; log_init "rejudge"; log_trap_exit
log INFO "host=$(hostname -s) gpu=$(nvidia-smi --query-gpu=name,uuid --format=csv,noheader | head -1)"
log_phase "rejudge"
cd "$ROOT/safety-eval"
SAFETY_EVAL_DIR="$ROOT/safety-eval" "$ROOT/.venv-safety-eval/bin/python" "$WORK/scripts/rejudge_missing.py" \
  --labels "${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}" --prefix 2026-08-28-traj4-h200 \
  2>&1 | grep -vE "^\s*$|it/s\]|Processed prompts" | while read -r l; do log INFO "$l"; done
