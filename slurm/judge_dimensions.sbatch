#!/bin/bash
# Stage 1, step 2+3: run ONE judge candidate (env JUDGE=qwen72|olmo32) on the calibration items and the
# full phoenix/starling item set, with the locked rubric. Both candidates run on both sets; the calibration
# result selects the judge, and only the selected judge's full-set output is primary (the other is a
# sensitivity check, declared before either was read).
# Submit: bash scripts/submit.sh slurm/judge_dimensions.sbatch --export=ALL,JUDGE=qwen72
#SBATCH --job-name=marin-judge
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=01:50:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export MARIN_RT_ROOT="$WORK"
PY="$WORK/repro-olmo3-safety/.venv-safety-eval/bin/python"
export HF_HOME="$WORK/hf_cache" HF_HUB_CACHE="$WORK/hf_cache/hub" HUGGINGFACE_HUB_CACHE="$WORK/hf_cache/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_ENABLE_V1_MULTIPROCESSING=0
J="${JUDGE:?JUDGE=qwen72|olmo32}"
case "$J" in
  qwen72) REPO=models--Qwen--Qwen2.5-72B-Instruct; QUANT="--quant fp8";;
  olmo32) REPO=models--allenai--OLMo-2-0325-32B-Instruct; QUANT="";;
  *) echo "unknown JUDGE $J"; exit 2;;
esac
SNAP="$(ls -d $HF_HOME/hub/$REPO/snapshots/* | head -1)"
source "$WORK/scripts/log_lib.sh"; log_init "judge-$J"; log_trap_exit
LAB="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
log INFO "judge=$J snap=$SNAP rubric_sha=$(cat $WORK/config/judge_rubric_v1/*.txt $WORK/config/judge_rubric_v1/*.md | sha256sum | cut -c1-12) gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader|head -1)"
for SET in calibration_v1 full_phoenix_starling_v1; do
  [[ -f "$LAB/$SET/items.jsonl" ]] || log_die "missing $LAB/$SET/items.jsonl"
  if [[ -f "$LAB/$SET/judge/$J.jsonl" ]]; then log INFO "skip $SET (exists)"; continue; fi
  log_phase "$J on $SET"
  log_heartbeat_start 120 "$LAB/$SET/judge/$J.jsonl"
  cd "$WORK/repro-olmo3-safety/safety-eval"
  "$PY" "$WORK/scripts/judge_dimensions.py" --judge "$SNAP" --name "$J" --items "$LAB/$SET/items.jsonl" --out "$LAB/$SET/judge" $QUANT 2>&1 | grep "^\[judge\]" | while read -r l; do log RESULT "$l"; done
  log_heartbeat_stop
  [[ -s "$LAB/$SET/judge/$J.jsonl" ]] || log_die "no output for $SET"
done
log INFO "judge $J done"
