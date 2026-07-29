#!/usr/bin/env bash
# Study B (remote): Olmo post-training trajectory framing test.
# Waits for the 32B toxigen r1 to finish (frees the GPU), then runs 3 checkpoints:
#   Olmo-3-7B-Instruct-SFT, -DPO, -Instruct(final)  x  {do_anything_now, harmbench}  x 3 seeds.
# INSTRUCT models => hf chat template (do NOT set TEMPLATE). Does NOT shut down the box
# (shutdown is done manually after verifying Study B completed).
set -uo pipefail
cd /home/paperspace/marin
unset TEMPLATE   # ensure run_row uses the model's own chat template (hf), not a base scaffold
DL=logs/2026-07-29-olmo-posttraining-studyB_driver.log
TOX=repro-olmo3-safety/runs/2026-07-28-olmo-32b-base-toxigen-r1/metrics.json

echo "[$(date -Is)] Study B launcher: waiting for 32B toxigen r1 to finish (GPU free)" > "$DL"
for _ in $(seq 1 720); do [ -f "$TOX" ] && break; sleep 10; done
if [ ! -f "$TOX" ]; then
  echo "[$(date -Is)] ERROR: 32B toxigen r1 never finished; aborting Study B" | tee -a "$DL"; exit 1
fi
echo "[$(date -Is)] 32B suite complete; launching Study B (instruct/hf template)" | tee -a "$DL"

run_ckpt () {  # $1=repo suffix  $2=prefix
  echo "[$(date -Is)] Study B model=allenai/$1 prefix=$2" | tee -a "$DL"
  bash scripts/run_suite.sh "allenai/$1" main "$2" "do_anything_now:default harmbench:default" >> "$DL" 2>&1
}
run_ckpt Olmo-3-7B-Instruct-SFT 2026-07-29-olmo-sft
run_ckpt Olmo-3-7B-Instruct-DPO 2026-07-29-olmo-dpo
run_ckpt Olmo-3-7B-Instruct     2026-07-29-olmo-final

echo "[$(date -Is)] Study B DONE (SFT+DPO+final x DAN+HarmBench x3 seeds)" | tee -a "$DL"
