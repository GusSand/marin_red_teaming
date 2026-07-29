#!/usr/bin/env bash
# One-off orchestration (32B scope-cut, Option 1): after the in-flight bbq r1 finishes,
# run the remainder on LOCAL marin-32b-base:
#   strongreject:logprobs x3 seeds, wmdp x3 seeds, toxigen x1 seed (scope-cut giant).
# BBQ kept at 1 seed (bbq r1, already running). Documented deviation from 3-seed pre-reg.
set -uo pipefail
cd /home/paperspace/marin
export TEMPLATE=/home/paperspace/marin/repro-olmo3-safety/config/base_template_v2.txt
DRIVERLOG=logs/2026-07-28-marin-32b-base-remainder_driver.log
BBQ1=repro-olmo3-safety/runs/2026-07-28-marin-32b-base-bbq-r1/metrics.json

echo "[$(date -Is)] remainder launcher start; waiting for bbq r1 metrics" > "$DRIVERLOG"
# Wait (up to 4h) for the orphaned bbq r1 to finish writing metrics.json
for _ in $(seq 1 1440); do
  [ -f "$BBQ1" ] && break
  sleep 10
done
if [ ! -f "$BBQ1" ]; then
  echo "[$(date -Is)] ERROR: bbq r1 metrics never appeared; aborting remainder" | tee -a "$DRIVERLOG"
  exit 1
fi
echo "[$(date -Is)] bbq r1 done; launching strongreject x3 + wmdp x3" | tee -a "$DRIVERLOG"

# StrongREJECT (3 seeds) + WMDP (3 seeds) via the standard suite runner
bash scripts/run_suite.sh marin-community/marin-32b-base main 2026-07-28-marin-32b-base \
  "strongreject:logprobs wmdp:default" >> "$DRIVERLOG" 2>&1

# Toxigen: 1 seed only (scope cut). run_row directly, seed 0.
echo "[$(date -Is)] launching toxigen r1 (single seed)" | tee -a "$DRIVERLOG"
bash scripts/run_row.sh marin-community/marin-32b-base main toxigen:default \
  2026-07-28-marin-32b-base-toxigen-r1 0 >> "$DRIVERLOG" 2>&1

echo "[$(date -Is)] remainder DONE (bbq x1, strongreject x3, wmdp x3, toxigen x1)" | tee -a "$DRIVERLOG"
