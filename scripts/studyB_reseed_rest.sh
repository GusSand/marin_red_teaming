#!/usr/bin/env bash
# Study B reseed REMAINDER: DPO + final only (SFT's 6 rows already completed). Seed-fixed.
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
unset TEMPLATE
DL=logs/2026-07-29-studyB-reseed_driver.log
source repro-olmo3-safety/.venv-safety-eval/bin/activate
echo "[$(date -Is)] Study B reseed REMAINDER start (DPO, final)" >> "$DL"
run_ckpt () {  # $1=repo-suffix  $2=prefix  $3=cache-dirname
  echo "[$(date -Is)] === $1: download ($(df -h / | awk 'NR==2{print $4}') free) ===" | tee -a "$DL"
  if ! huggingface-cli download "allenai/$1" >> "$DL" 2>&1; then
    echo "[$(date -Is)] DOWNLOAD FAILED $1 — skip+flag" | tee -a "$DL"; return; fi
  bash scripts/run_suite.sh "allenai/$1" main "$2" "do_anything_now:default harmbench:default" >> "$DL" 2>&1
  eval rm -rf "$HOME/.cache/huggingface/hub/$3"
  echo "[$(date -Is)] === $1 done, weights deleted ===" | tee -a "$DL"
}
run_ckpt Olmo-3-7B-Instruct-DPO 2026-07-29-olmo-dpo-reseed   models--allenai--Olmo-3-7B-Instruct-DPO
run_ckpt Olmo-3-7B-Instruct     2026-07-29-olmo-final-reseed models--allenai--Olmo-3-7B-Instruct
echo "[$(date -Is)] Study B reseed DONE" | tee -a "$DL"
