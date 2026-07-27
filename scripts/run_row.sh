#!/usr/bin/env bash
# Run ONE safety-eval generation row and capture full provenance.
# Gates 2-5. Never overwrites: refuses if the run dir already has metrics.json.
#
# Usage:
#   scripts/run_row.sh <model_repo> <revision> <task_spec> <run_name> [seed]
# Example (Gate 2):
#   scripts/run_row.sh allenai/Olmo-3-7B-Instruct main harmbench:default 2026-07-26-instruct-harmbench-r1 0
#
# task_spec = "<folder>:<config_yaml>" (e.g. harmbench:default, harmbench:wildguard_reasoning_answer)
# Chat template: we pass None so safety-eval uses the model's own tokenizer.apply_chat_template
#   (correct for Olmo 3 Instruct AND Think, which ship their own chat/thinking templates).
set -euo pipefail

MODEL="${1:?model repo}"; REV="${2:?revision}"; TASK="${3:?task_spec folder:config}"; NAME="${4:?run_name}"; SEED="${5:-0}"

ROOT=/home/paperspace/marin/repro-olmo3-safety
VENV="$ROOT/.venv-safety-eval"
SE="$ROOT/safety-eval"
RUNDIR="$ROOT/runs/$NAME"
LOG="/home/paperspace/marin/logs/${NAME}.log"

if [[ -f "$RUNDIR/metrics.json" ]]; then
  echo "REFUSING: $RUNDIR/metrics.json already exists (no silent overwrite). Pick a new run_name." >&2
  exit 3
fi
mkdir -p "$RUNDIR"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

SE_SHA="$(git -C "$SE" rev-parse HEAD)"
CMD=(python "$SE/evaluation/eval.py" generators
  --use_vllm
  --model_name_or_path "$MODEL"
  --hf_revision "$REV"
  --model_input_template_path_or_name "${TEMPLATE:-hf}"
  --tasks "$TASK"
  --report_output_path "$RUNDIR/metrics.json"
  --save_individual_results_path "$RUNDIR/all.json")

# provenance BEFORE running
{ echo "MODEL=$MODEL"; echo "REVISION=$REV"; echo "TASK=$TASK"; echo "SEED=$SEED"; printf '%q ' "${CMD[@]}"; echo; } > "$RUNDIR/command.txt"
python - "$RUNDIR/provenance.json" "$MODEL" "$REV" "$TASK" "$SEED" "$SE_SHA" <<'PY'
import json,sys,subprocess
out,model,rev,task,seed,se_sha=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6]
prov={"model":model,"revision":rev,"task":task,"seed":int(seed),"safety_eval_sha":se_sha}
try:
    import torch,transformers,vllm
    prov.update(torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__,vllm=vllm.__version__)
    prov["gpu"]=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
except Exception as e:
    prov["env_error"]=str(e)
prov["nvidia_smi"]=subprocess.run(["nvidia-smi","--query-gpu=name,driver_version","--format=csv,noheader"],capture_output=True,text=True).stdout.strip()
json.dump(prov,open(out,"w"),indent=2)
print("wrote",out)
PY

echo "[$(date -Is)] running: ${CMD[*]}" | tee -a "$LOG"
# Placeholder only: safety-eval constructs AsyncOpenAI() at import time. Our rows never
# call OpenAI (all WildGuard / roberta / string-parse); a real call would fail loudly.
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-unused-placeholder}"
export CUDA_VISIBLE_DEVICES=0 VLLM_WORKER_MULTIPROC_METHOD=spawn
# Revision is pinned via eval.py's --hf_revision (wired into CMD above).
PYTHONHASHSEED="$SEED" "${CMD[@]}" >> "$LOG" 2>&1
echo "[$(date -Is)] done -> $RUNDIR/metrics.json" | tee -a "$LOG"
cat "$RUNDIR/metrics.json"
