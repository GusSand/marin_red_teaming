#!/usr/bin/env bash
# Runs AFTER Olmo-Think (master3 done). 1) Llama-Guard vs WildGuard grade audit; 2) WMDP base-cap diagnostic.
set -uo pipefail
cd /home/paperspace/marin
source repro-olmo3-safety/.venv-safety-eval/bin/activate
export CUDA_VISIBLE_DEVICES=0
echo "[$(date -Is)] POSTTRAIN start" > logs/posttrain.log
echo "[$(date -Is)] STAGE P1: Llama-Guard-3 vs WildGuard grade audit" | tee -a logs/posttrain.log
python scripts/grade_audit_llamaguard.py >> logs/grade_audit_llamaguard.log 2>&1
echo "[$(date -Is)] STAGE P2: WMDP base-capability diagnostic" | tee -a logs/posttrain.log
bash scripts/run_base_capability.sh
echo "[$(date -Is)] POSTTRAIN done" | tee -a logs/posttrain.log
