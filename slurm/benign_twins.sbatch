#!/bin/bash
# S1-05: benign twins control. 54 twins x 3 seeds x 2 checkpoints = 324 generations.
# Plan: docs/experiments/09-07_benign-twins_control.md (frozen 2026-09-07, commit a9ccada)
# Submit: cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/benign_twins.sbatch
#
# ONE job, ONE GPU, sequential. Never an array: an array scatters tasks across nodes and any
# phoenix-vs-starling comparison drawn from it is confounded by hardware (CLAUDE.md, learned 08-27).
#SBATCH --job-name=marin-twins
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
PY="$ROOT/.venv-safety-eval/bin/python"
export HF_HOME="$WORK/hf_cache" HF_HUB_CACHE="$WORK/hf_cache/hub" HUGGINGFACE_HUB_CACHE="$WORK/hf_cache/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export VLLM_ENABLE_V1_MULTIPROCESSING=0

source "$WORK/scripts/log_lib.sh"
log_init "twins"
log_trap_exit

TWINS="/scratch/gs157/marin-misinfo-labels/benign_twins_v1/twins.jsonl"
[[ -f "$TWINS" ]] || log_die "twins missing at $TWINS"
N_TWINS="$(wc -l < "$TWINS")"
[[ "$N_TWINS" -eq 54 ]] || log_die "expected 54 twins, found $N_TWINS"

TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "scaffold missing at $TEMPLATE"

OUTROOT="$WORK/runs/twins/${MARIN_RUN_PREFIX:-2026-09-07-twins-h200}"
_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"

log INFO "twins=$N_TWINS gpu=$(nvidia-smi --query-gpu=name,uuid --format=csv,noheader | head -1)"

# Sampling matches the misinformation runs exactly (harmbench/default.yaml): temperature 0.7,
# top_p 0.95, max_new_tokens 2048. The twins are compared against attempt-strong mass from those
# runs, so the decoding must not differ.
for TAG in phoenix starling; do
    SHA="$(cat "$_HUB/refs/$TAG")"
    MODEL="$_HUB/snapshots/$SHA"
    [[ -d "$MODEL" ]] || log_die "no snapshot for $TAG at $MODEL"
    for SEED in 0 1 2; do
        OUT="$OUTROOT/$TAG/seed$SEED"
        if [[ -f "$OUT/responses_raw.jsonl" ]]; then
            log INFO "skip $TAG seed$SEED (already present)"
            continue
        fi
        log INFO "generate $TAG seed$SEED -> $OUT"
        "$PY" "$WORK/scripts/ifeval_generate.py" \
            --model "$MODEL" --template "$TEMPLATE" --input "$TWINS" --out "$OUT" \
            --tag "twins-$TAG-s$SEED" --seed "$SEED" \
            --temperature 0.7 --top-p 0.95 --max-new-tokens 2048
    done
done

log INFO "all 6 generation runs complete under $OUTROOT"
