#!/usr/bin/env bash
# Gate 1 smoke test: prove the safety-eval pipeline runs end-to-end WITHOUT big downloads.
# Uses toxigen:tiny (small tomh/toxigen_roberta classifier, ~500MB) on a cached 1B model.
# This is a PIPELINE proof, not a reproduction number — do not compare to any target.
set -euo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
ROOT=$MARIN_ROOT/repro-olmo3-safety
source "$ROOT/.venv-safety-eval/bin/activate"
OUT="$ROOT/runs/_smoke-toxigen-tiny-llama1b"
LOG=$MARIN_ROOT/logs/gate1_smoke.log
mkdir -p "$OUT"
# Placeholder only: safety-eval constructs AsyncOpenAI() at import time. None of our rows
# (WildGuard / toxigen_roberta / string-parse) call OpenAI; a real call would fail loudly.
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-unused-placeholder}"
export CUDA_VISIBLE_DEVICES=0 VLLM_WORKER_MULTIPROC_METHOD=spawn
echo "[$(date -Is)] smoke: toxigen:tiny on Llama-3.2-1B-Instruct" | tee "$LOG"
python "$ROOT/safety-eval/evaluation/eval.py" generators \
  --use_vllm \
  --model_name_or_path meta-llama/Llama-3.2-1B-Instruct \
  --model_input_template_path_or_name hf \
  --tasks toxigen:tiny \
  --report_output_path "$OUT/metrics.json" \
  --save_individual_results_path "$OUT/all.json" >> "$LOG" 2>&1
echo "[$(date -Is)] smoke done" | tee -a "$LOG"
echo "=== metrics.json ===" | tee -a "$LOG"; cat "$OUT/metrics.json" | tee -a "$LOG"
