#!/bin/bash
# Stage 1, step 2: fetch the two judge candidates into the workspace HF cache from a CPU node.
# Login-node background downloads die at session end (2026-08-28), so this runs as a batch job.
# Resumable: huggingface_hub keeps *.incomplete blobs. Submit: bash scripts/submit.sh slurm/download_judges.sbatch
#SBATCH --job-name=marin-dl-judges
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export HF_HOME="$WORK/hf_cache"
PY="$WORK/repro-olmo3-safety/.venv-safety-eval/bin/python"
curl -s -o /dev/null -w "network check: HTTP %{http_code}\n" --max-time 20 https://huggingface.co || { echo "no network from $(hostname); abort"; exit 2; }
for M in Qwen/Qwen2.5-72B-Instruct allenai/OLMo-2-0325-32B-Instruct; do
  echo "== $M  $(date)"
  "$PY" -c "from huggingface_hub import snapshot_download; p=snapshot_download('$M', allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','*.py','*.model'], max_workers=8); print('DONE', p)"
  du -sh "$HF_HOME/hub/models--${M//\//--}"
done
echo "all done $(date)"
