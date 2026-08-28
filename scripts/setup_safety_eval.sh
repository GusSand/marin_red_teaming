#!/usr/bin/env bash
# Gate 1: isolated environment for allenai/safety-eval @ 060cc903.
# Builds a dedicated venv so we do NOT disturb the base env (torch 2.10 / transformers 5.0).
# safety-eval pins vllm==0.11.0 and torch>=2.8,<2.9.
# Usage: bash scripts/setup_safety_eval.sh
set -euo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"

REPO=$MARIN_ROOT/repro-olmo3-safety/safety-eval
VENV=$MARIN_ROOT/repro-olmo3-safety/.venv-safety-eval
LOG=$MARIN_ROOT/logs/gate1_setup.log

# Torch: /tmp is a 2GB tmpfs on the login node, and pip extracts the 888MB torch wheel
# there -> "OSError: [Errno 28] No space left on device" partway through. Keep pip's temp
# and cache on scratch. (Hit 2026-08-27 during the port.)
export TMPDIR="${TMPDIR:-$MARIN_ROOT/tmp}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$MARIN_ROOT/pip_cache}"
mkdir -p "$TMPDIR" "$PIP_CACHE_DIR" "$(dirname "$LOG")"
echo "[$(date -Is)] TMPDIR=$TMPDIR PIP_CACHE_DIR=$PIP_CACHE_DIR"

echo "[$(date -Is)] creating venv at $VENV"
# Torch is HETEROGENEOUS: the login node's /usr/bin/python3 is 3.12, the l40s compute
# nodes' is 3.9. A stock venv symlinks bin/python3 -> /usr/bin/python3, so the same venv
# runs 3.12 on login and 3.9 on a compute node, where none of the installed packages are
# importable ("No module named 'torch'"). Build with the VERSIONED interpreter and repoint
# the symlink at an absolute versioned path so it resolves identically on every node.
# (Hit 2026-08-27, job 16488571.)
# /usr/bin/python3.12 exists on compute nodes but ships NO dev headers, so Triton cannot
# compile its runtime shim and vLLM dies at engine init (job 16488625). Default to the
# standalone CPython in this workspace, which does have include/python3.12/Python.h.
PY312="${PY312:-$MARIN_ROOT/pythons/cpython-3.12.14-linux-x86_64-gnu/bin/python3.12}"
if [[ ! -x "$PY312" ]]; then
  echo "FATAL: no interpreter at $PY312. It must be a python3.12 WITH dev headers;" >&2
  echo "       /usr/bin/python3.12 has none and will fail at vLLM engine init." >&2
  exit 1
fi
"$PY312" -c "import sysconfig,os,sys; p=sysconfig.get_paths()['include']; sys.exit(0 if os.path.exists(os.path.join(p,'Python.h')) else 1)" \
  || { echo "FATAL: $PY312 has no Python.h; Triton will fail to compile at runtime." >&2; exit 1; }
"$PY312" -m venv "$VENV"
ln -sfn "$PY312" "$VENV/bin/python3"
ln -sfn python3 "$VENV/bin/python"
ln -sfn python3 "$VENV/bin/python3.12"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel setuptools

cd "$REPO"
echo "[$(date -Is)] pip install -e . + requirements + vllm==0.11.0"
pip install -e .
pip install -r requirements.txt
pip install "vllm==0.11.0"

# PIN (2026-08-27, Torch port): requirements.txt leaves transformers unpinned, so a fresh
# resolve pulls 5.x. The 07-28/07-29 runs this project compares against were produced on
# transformers 4.57.1 (see any runs/*/provenance.json). A major-version jump changes tokenizer
# and generation behaviour, which is exactly the protocol drift that moved HarmBench 21 points
# between harness vintages. Restoring the recorded protocol, not tuning to hit a number.
pip install "transformers==4.57.1"

echo "[$(date -Is)] provenance:"
python - <<'PY'
import torch, transformers, sys
print("python", sys.version.split()[0])
print("torch", torch.__version__, "cuda", torch.version.cuda, "avail", torch.cuda.is_available())
print("transformers", transformers.__version__)
try:
    import vllm; print("vllm", vllm.__version__)
except Exception as e:
    print("vllm import FAILED:", e)
PY
echo "[$(date -Is)] setup done"
