#!/usr/bin/env bash
# Marin-first master chain (single GPU, sequential):
#   A. marin-8b-instruct full suite (hf chat template)   <- priority deliverable
#   B. marin-8b-base   full suite (minimal {instruction} template; base has no chat template)
#   C. remaining Olmo-3-7B-Think rows (skip-logic protects the DAN/HarmBench already done)
# WildGuard-Test excluded everywhere (gated dataset allenai/wildguardmix, pending accept).
# Base results are INTERPRET-WITH-CARE: base has no refusal training; completions eyeballed post-hoc.
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
INSTR="do_anything_now:default harmbench:default trustllm_jailbreaktrigger:default wildjailbreak:harmful wildjailbreak:benign xstest:default bbq:default strongreject:logprobs toxigen:default wmdp:default"
THINK="do_anything_now:wildguard_reasoning_answer harmbench:wildguard_reasoning_answer trustllm_jailbreaktrigger:wildguard_reasoning_answer wildjailbreak:harmful_wildguard_reasoning_answer wildjailbreak:benign_wildguard_reasoning_answer xstest:wildguard_reasoning_answer bbq:default_reasoning_answer strongreject:logprobs_reasoning_answer toxigen:default_reasoning_answer wmdp:default_reasoning_answer"
LOG=logs/master_chain.log
echo "[$(date -Is)] MASTER start" > "$LOG"

echo "[$(date -Is)] STAGE A: marin-8b-instruct" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh marin-community/marin-8b-instruct main 2026-07-26-marin-instruct "$INSTR"

echo "[$(date -Is)] STAGE B: marin-8b-base (minimal template)" | tee -a "$LOG"
TEMPLATE=$MARIN_ROOT/repro-olmo3-safety/config/base_template.txt \
  bash scripts/run_suite.sh marin-community/marin-8b-base main 2026-07-26-marin-base "$INSTR"

echo "[$(date -Is)] STAGE C: remaining Olmo Think" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh allenai/Olmo-3-7B-Think main 2026-07-26-think "$THINK"

echo "[$(date -Is)] MASTER done" | tee -a "$LOG"
