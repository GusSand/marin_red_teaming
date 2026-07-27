#!/usr/bin/env bash
# Master3 (wildguardmix now accepted -> WildGuard-Test unblocked everywhere).
# Order: quick WildGuard-Test catch-ups on already-done models first, then base2 (user priority),
# then Olmo Think, then Olmo-instruct WildGuard-Test (needs 14G re-download, so last).
# base2 = User:/Assistant: scaffold. All suites now INCLUDE wildguardtest. skip-logic protects done runs.
set -uo pipefail
cd /home/paperspace/marin
INSTR="do_anything_now:default harmbench:default trustllm_jailbreaktrigger:default wildjailbreak:harmful wildjailbreak:benign xstest:default wildguardtest:default bbq:default strongreject:logprobs wmdp:default toxigen:default"
THINK="do_anything_now:wildguard_reasoning_answer harmbench:wildguard_reasoning_answer trustllm_jailbreaktrigger:wildguard_reasoning_answer wildjailbreak:harmful_wildguard_reasoning_answer wildjailbreak:benign_wildguard_reasoning_answer xstest:wildguard_reasoning_answer wildguardtest:wildguard_reasoning_answer bbq:default_reasoning_answer strongreject:logprobs_reasoning_answer wmdp:default_reasoning_answer toxigen:default_reasoning_answer"
LOG=logs/master3_chain.log
echo "[$(date -Is)] MASTER3 start" > "$LOG"

echo "[$(date -Is)] STAGE 1: Marin-instruct WildGuard-Test catch-up (cached)" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh marin-community/marin-8b-instruct main 2026-07-26-marin-instruct "wildguardtest:default"

echo "[$(date -Is)] STAGE 2: marin-8b-base RE-RUN full (scaffold) incl WildGuard-Test" | tee -a "$LOG"
TEMPLATE=/home/paperspace/marin/repro-olmo3-safety/config/base_template_v2.txt \
  bash scripts/run_suite.sh marin-community/marin-8b-base main 2026-07-26-marin-base2 "$INSTR"

echo "[$(date -Is)] STAGE 3: Olmo Think full incl WildGuard-Test" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh allenai/Olmo-3-7B-Think main 2026-07-26-think "$THINK"

echo "[$(date -Is)] STAGE 4: Olmo-instruct WildGuard-Test catch-up (re-downloads Olmo-3-7B-Instruct)" | tee -a "$LOG"
TEMPLATE=hf bash scripts/run_suite.sh allenai/Olmo-3-7B-Instruct main 2026-07-26-instruct "wildguardtest:default"

echo "[$(date -Is)] MASTER3 done" | tee -a "$LOG"
