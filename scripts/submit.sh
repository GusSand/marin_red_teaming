#!/bin/bash
# Preflight-gated sbatch wrapper — the only sanctioned way to submit GPU jobs on Torch.
# Ported from safety-decay/scripts/submit.sh, 2026-08-27.
#
# Usage (on Torch):
#   bash scripts/submit.sh slurm/<file>.sbatch [extra sbatch args]
#
# sbatch options must precede the script file. Args placed AFTER the file go to the
# script itself, silently: in safety-decay that cost job 15581324, where
# `sbatch file --array=10` re-ran 0-9 instead. This wrapper enforces the order.
set -euo pipefail

WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
ROOT="$WORK/repro-olmo3-safety"
PY="$ROOT/.venv-safety-eval/bin/python"
export HF_HOME="$WORK/hf_cache"   # workspace owns its cache; do NOT inherit a global HF_HOME
# safety-eval imports an OpenAI client at module load even for local judges.
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"

mkdir -p "$WORK/logs"   # Slurm will not create --output dirs; logs/ is gitignored

if [[ $# -lt 1 ]]; then
    echo "usage: bash scripts/submit.sh slurm/<file>.sbatch [extra sbatch args]" >&2
    exit 2
fi
[[ -f "$WORK/$1" || -f "$1" ]] || { echo "no such sbatch file: $1" >&2; exit 2; }

CHECK="$WORK/scripts/dry_run_check.py"
STATE_CHECK="$WORK/scripts/check_project_state.py"

echo "=== project state: $STATE_CHECK ==="
python3 "$STATE_CHECK" --require-in-progress

echo "=== preflight: $CHECK ==="
if [[ ! -x "$PY" ]]; then
    echo "PREFLIGHT FAILED - no venv at $PY. Run scripts/setup_safety_eval.sh first." >&2
    exit 1
fi
cd "$ROOT/safety-eval"
if ! "$PY" "$CHECK"; then
    echo "PREFLIGHT FAILED — nothing submitted." >&2
    exit 1
fi

cd "$WORK"
FILE="$1"; shift
sbatch "$@" "$FILE"
