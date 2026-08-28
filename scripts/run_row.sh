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

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"

MODEL="${1:?model repo}"; REV="${2:?revision}"; TASK="${3:?task_spec folder:config}"; NAME="${4:?run_name}"; SEED="${5:-0}"

ROOT=$MARIN_ROOT/repro-olmo3-safety

# --- offline model resolution (Torch, 2026-08-27) ---
# The jobs run HF_HUB_OFFLINE=1 (gated judge, no token). safety-eval's is_adapter_model()
# still tries to list repo files over the network for a repo-id, which fails offline. If the
# revision is already cached, resolve the concrete snapshot dir and pass that instead: it reads
# from disk, needs no network, and pins the exact commit into the path.
LOAD_MODEL="$MODEL"; PASS_REV=("--hf_revision" "$REV"); RESOLVED_SHA=""
if [[ "${HF_HUB_OFFLINE:-0}" == "1" && "$MODEL" != /* ]]; then
  _hub="${HF_HOME:-$MARIN_ROOT/hf_cache}/hub/models--${MODEL//\//--}"
  _ref="$_hub/refs/$REV"
  if [[ -f "$_ref" ]]; then
    RESOLVED_SHA="$(cat "$_ref")"
    _snap="$_hub/snapshots/$RESOLVED_SHA"
    if [[ -d "$_snap" ]]; then
      LOAD_MODEL="$_snap"
      PASS_REV=()   # revision is now baked into the path; do not also pass --hf_revision
      echo "[offline] $MODEL@$REV -> $_snap (sha ${RESOLVED_SHA:0:12})" >&2
    fi
  fi
  if [[ "$LOAD_MODEL" == "$MODEL" ]]; then
    echo "REFUSING: offline but no cached snapshot for $MODEL@$REV under $_hub. Run scripts/prefetch_revisions.py first." >&2
    exit 4
  fi
fi
VENV="$ROOT/.venv-safety-eval"
SE="$ROOT/safety-eval"
RUNDIR="$ROOT/runs/$NAME"
LOG="$MARIN_ROOT/logs/${NAME}.log"

if [[ -f "$RUNDIR/metrics.json" ]]; then
  echo "REFUSING: $RUNDIR/metrics.json already exists (no silent overwrite). Pick a new run_name." >&2
  exit 3
fi
mkdir -p "$RUNDIR"
# shellcheck disable=SC1091
source "$VENV/bin/activate"

export RESOLVED_SHA
SE_SHA="$(git -C "$SE" rev-parse HEAD)"
CMD=(python "$SE/evaluation/eval.py" generators
  --use_vllm
  --model_name_or_path "$LOAD_MODEL"
  "${PASS_REV[@]}"
  --model_input_template_path_or_name "${TEMPLATE:-hf}"
  ${HPARAM_OVERRIDES:+--hparam_overrides "$HPARAM_OVERRIDES"}
  --tasks "$TASK"
  --report_output_path "$RUNDIR/metrics.json"
  --save_individual_results_path "$RUNDIR/all.json")

# provenance BEFORE running
{ echo "MODEL=$MODEL"; echo "REVISION=$REV"; echo "TASK=$TASK"; echo "SEED=$SEED"; printf '%q ' "${CMD[@]}"; echo; } > "$RUNDIR/command.txt"
python - "$RUNDIR/provenance.json" "$MODEL" "$REV" "$TASK" "$SEED" "$SE_SHA" <<'PY'
import json,sys,subprocess
out,model,rev,task,seed,se_sha=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6]
prov={"model":model,"revision":rev,"task":task,"seed":int(seed),"safety_eval_sha":se_sha}
import os as _o
_sha=_o.environ.get("RESOLVED_SHA","")
if _sha: prov["resolved_sha"]=_sha
try:
    import torch,transformers,vllm
    prov.update(torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__,vllm=vllm.__version__)
    prov["gpu"]=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
except Exception as e:
    prov["env_error"]=str(e)
prov["nvidia_smi"]=subprocess.run(["nvidia-smi","--query-gpu=name,driver_version","--format=csv,noheader"],capture_output=True,text=True).stdout.strip()
# A reproducibility claim is only checkable against the exact hardware and engine it ran on.
# The 2026-08-27 determinism test was invalid because three "identical" runs landed on three
# different GPUs and nothing recorded that.
import socket as _s
prov["hostname"]=_s.gethostname()
prov["gpu_uuid"]=subprocess.run(["nvidia-smi","--query-gpu=uuid","--format=csv,noheader"],capture_output=True,text=True).stdout.strip()
prov["slurm_job"]=_o.environ.get("SLURM_JOB_ID","")
prov["vllm_v1_multiprocessing"]=_o.environ.get("VLLM_ENABLE_V1_MULTIPROCESSING","<unset>")
prov["sampling_seed_env"]=_o.environ.get("SAFETYEVAL_SAMPLING_SEED","<unset>")
json.dump(prov,open(out,"w"),indent=2)
print("wrote",out)
PY

echo "[$(date -Is)] running: ${CMD[*]}" | tee -a "$LOG"
# Placeholder only: safety-eval constructs AsyncOpenAI() at import time. Our rows never
# call OpenAI (all WildGuard / roberta / string-parse); a real call would fail loudly.
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-unused-placeholder}"
export CUDA_VISIBLE_DEVICES=0 VLLM_WORKER_MULTIPROC_METHOD=spawn
# Real per-run vLLM sampling seed (PYTHONHASHSEED does NOT control vLLM's sampler; see
# generation_utils.py PATCH 2026-07-29). This makes the 3 seeds independent samples at temp>0.
export SAFETYEVAL_SAMPLING_SEED="$SEED"
# Revision is pinned via eval.py's --hf_revision (wired into CMD above).
PYTHONHASHSEED="$SEED" "${CMD[@]}" >> "$LOG" 2>&1
echo "[$(date -Is)] done -> $RUNDIR/metrics.json" | tee -a "$LOG"
cat "$RUNDIR/metrics.json"
