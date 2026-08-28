#!/usr/bin/env bash
# Base RE-RUN with a User:/Assistant: scaffold template (prefix marin-base2), then Olmo Think.
# The minimal-{instruction} base run (prefix marin-base) is CONFOUNDED and superseded; kept only as
# a documented before/after partial. Toxigen ordered LAST (slow + non-discriminating).
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
INSTR="do_anything_now:default harmbench:default trustllm_jailbreaktrigger:default wildjailbreak:harmful wildjailbreak:benign xstest:default bbq:default strongreject:logprobs wmdp:default toxigen:default"
THINK="do_anything_now:wildguard_reasoning_answer harmbench:wildguard_reasoning_answer trustllm_jailbreaktrigger:wildguard_reasoning_answer wildjailbreak:harmful_wildguard_reasoning_answer wildjailbreak:benign_wildguard_reasoning_answer xstest:wildguard_reasoning_answer bbq:default_reasoning_answer strongreject:logprobs_reasoning_answer wmdp:default_reasoning_answer toxigen:default_reasoning_answer"
LOG=logs/master2_chain.log
echo "[$(date -Is)] MASTER2 start" > "$LOG"
echo "[$(date -Is)] STAGE B2: marin-8b-base RE-RUN (User:/Assistant: scaffold)" | tee -a "$LOG"
TEMPLATE=$MARIN_ROOT/repro-olmo3-safety/config/base_template_v2.txt \
  bash scripts/run_suite.sh marin-community/marin-8b-base main 2026-07-26-marin-base2 "$INSTR"
echo "[$(date -Is)] STAGE C: Olmo Think remainder" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh allenai/Olmo-3-7B-Think main 2026-07-26-think "$THINK"
echo "[$(date -Is)] MASTER2 done" | tee -a "$LOG"
