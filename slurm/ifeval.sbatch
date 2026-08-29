#!/bin/bash
# Stage 1, step 1: IFEval on four Marin base tags, sequentially on ONE GPU, then the official scorer.
# Spec: docs/experiments/08-28_phoenix-starling_distribution-decomposition.md
# Submit: cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/ifeval.sbatch
#SBATCH --job-name=marin-ifeval
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
export NLTK_DATA="$HOME/nltk_data"

source "$WORK/scripts/log_lib.sh"
log_init "ifeval"
log_trap_exit

IFE="$WORK/ifeval/instruction_following_eval"
INPUT="$IFE/data/input_data.jsonl"
[[ -f "$INPUT" ]] || log_die "IFEval input missing at $INPUT"
TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "scaffold missing"
OUTROOT="$WORK/runs/ifeval/${MARIN_RUN_PREFIX:-2026-08-29-ifeval-h200}"
_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
log INFO "ifeval sha=$(git -C $WORK/ifeval/gr rev-parse HEAD) gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"

for TAG in jellyfish phoenix starling deeper-starling; do
    SHA="$(cat "$_HUB/refs/$TAG")"; MODEL="$_HUB/snapshots/$SHA"
    [[ -d "$MODEL" ]] || log_die "no snapshot for $TAG"
    OUT="$OUTROOT/$TAG"
    if [[ -f "$OUT/eval_truncated/eval_results_strict.jsonl" ]]; then log INFO "skip $TAG (done)"; continue; fi
    log_phase "generate $TAG"
    log_heartbeat_start 120 "$OUT/responses_raw.jsonl"
    cd "$ROOT/safety-eval"
    "$PY" "$WORK/scripts/ifeval_generate.py" --model "$MODEL" --template "$TEMPLATE" --input "$INPUT" --out "$OUT" --tag "$TAG" \
        2>&1 | grep -v "^INFO\|^WARNING" | tail -5 | while read -r l; do log INFO "$l"; done
    log_heartbeat_stop
    [[ -s "$OUT/responses_raw.jsonl" ]] || log_die "no responses for $TAG"
    log_phase "score $TAG"
    cd "$WORK/ifeval/gr"
    for V in truncated raw; do
        mkdir -p "$OUT/eval_$V"
        "$PY" -m instruction_following_eval.evaluation_main --input_data="$INPUT" \
            --input_response_data="$OUT/responses_$V.jsonl" --output_dir="$OUT/eval_$V" > "$OUT/eval_$V/stdout.txt" 2>&1 \
            || log_die "scorer failed for $TAG/$V (see $OUT/eval_$V/stdout.txt)"
        # scorer prints strict then loose; each block has prompt-level and instruction-level lines
        log RESULT "$TAG [$V] strict/loose: $(grep -o 'prompt-level: [0-9.]*' "$OUT/eval_$V/stdout.txt" | tr '\n' ' ')"
    done
done
log INFO "all four tags done; results under $OUTROOT"
