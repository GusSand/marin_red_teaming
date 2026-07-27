#!/usr/bin/env bash
# Gate 1: isolated environment for allenai/safety-eval @ 060cc903.
# Builds a dedicated venv so we do NOT disturb the base env (torch 2.10 / transformers 5.0).
# safety-eval pins vllm==0.11.0 and torch>=2.8,<2.9.
# Usage: bash scripts/setup_safety_eval.sh
set -euo pipefail

REPO=/home/paperspace/marin/repro-olmo3-safety/safety-eval
VENV=/home/paperspace/marin/repro-olmo3-safety/.venv-safety-eval
LOG=/home/paperspace/marin/logs/gate1_setup.log

echo "[$(date -Is)] creating venv at $VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel setuptools

cd "$REPO"
echo "[$(date -Is)] pip install -e . + requirements + vllm==0.11.0"
pip install -e .
pip install -r requirements.txt
pip install "vllm==0.11.0"

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
