#!/usr/bin/env bash
# Gate 3: four clean rows x 3 runs each on Olmo-3-7B-Instruct (final, revision main).
# HarmBench seed 0 already done (Gate 2, run r1). Runs the remaining 11 sequentially.
# Each run_row.sh call writes its own provenance/metrics and refuses to overwrite.
set -uo pipefail
cd /home/paperspace/marin
MODEL=allenai/Olmo-3-7B-Instruct
DRIVERLOG=logs/gate3_driver.log
echo "[$(date -Is)] Gate 3 start" > "$DRIVERLOG"

# task_folder:config  runname_bench   (seeds 0,1,2 -> r1,r2,r3)
declare -A BENCH=(
  [harmbench]="harmbench:default"
  [xstest]="xstest:default"
  [dan]="do_anything_now:default"
  [wildguardtest]="wildguardtest:default"
)
run_one () {
  local bench="$1" seed="$2" rn="$3"
  local name="2026-07-26-instruct-${bench}-r${rn}"
  if [ -f "repro-olmo3-safety/runs/${name}/metrics.json" ]; then
    echo "[$(date -Is)] SKIP ${name} (exists)" | tee -a "$DRIVERLOG"; return 0
  fi
  echo "[$(date -Is)] RUN ${name}  task=${BENCH[$bench]} seed=${seed}" | tee -a "$DRIVERLOG"
  bash scripts/run_row.sh "$MODEL" main "${BENCH[$bench]}" "$name" "$seed" \
    > "logs/${name}.outer.log" 2>&1
  echo "[$(date -Is)] END ${name} exit=$?" | tee -a "$DRIVERLOG"
}

# harmbench: r1 (seed0) already done in Gate 2; do r2,r3
run_one harmbench 1 2
run_one harmbench 2 3
for bench in xstest dan wildguardtest; do
  run_one "$bench" 0 1
  run_one "$bench" 1 2
  run_one "$bench" 2 3
done
echo "[$(date -Is)] Gate 3 ALL DONE" | tee -a "$DRIVERLOG"
