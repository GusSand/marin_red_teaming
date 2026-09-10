#!/bin/bash
# S1-ENDORSE-V2 Part A: build the blinded 1,080-row package. No outcomes are analyzed.
# Submit: bash scripts/submit.sh slurm/endorsement_feature_package.sbatch
#SBATCH --job-name=endorse-pkg
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail
WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
LAB="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
source "$WORK/scripts/log_lib.sh"; log_init "endorse-pkg"; log_trap_exit
python3 "$WORK/scripts/build_endorsement_feature_package.py" \
  --full "$LAB/full_phoenix_starling_v1" \
  --out "$LAB/endorsement_feature_v1" \
  --codebook "$WORK/config/endorsement_feature_codebook_v1.md"
log INFO "package built at $LAB/endorsement_feature_v1"
