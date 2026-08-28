#!/usr/bin/env bash
# Tamper-resistance run driver (defensive red-team; pre-registered
# docs/experiments/07-29_marin-olmo-instruct_tamper-resistance_lora-attack.md).
#
# Usage: scripts/tamper_run.sh <model_repo> <short_name> [n_pairs] [lr]
#   e.g. scripts/tamper_run.sh marin-community/marin-8b-instruct marin8b
#
# For ONE model: LoRA-attack (adapters at steps 0,5,10,20,40,80), then per checkpoint
# merge->eval(harmbench+strongreject)->DELETE merged weights. Adapters DELETED at the end.
# Only the ASR provenance in runs/ survives (content-safe). Nothing harmful committed.
set -uo pipefail

# Torch port 2026-08-27: override with MARIN_RT_ROOT.
MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
cd $MARIN_ROOT
MODEL="${1:?model repo}"; NAME="${2:?short name}"; NPAIRS="${3:-100}"; LR="${4:-2e-4}"
STEPS=(0 5 10 20 40 80)

ROOT=$MARIN_ROOT/repro-olmo3-safety
VENV="$ROOT/.venv-safety-eval"
WORK="$ROOT/tamper_work/$NAME"          # adapters + transient merged models (gitignored, deleted)
ADIR="$WORK/adapters"
DL="$MARIN_ROOT/logs/2026-07-29-tamper-${NAME}_driver.log"
ADV="$ROOT/data/advbench_harmful_behaviors.csv"
mkdir -p "$ADIR"
source "$VENV/bin/activate"

echo "[$(date -Is)] tamper attack start model=$MODEL name=$NAME n_pairs=$NPAIRS lr=$LR" > "$DL"

# 1) LoRA attack -> adapter snapshots (steps 0,5,10,20,40,80)
python scripts/tamper_attack.py --model "$MODEL" --advbench_csv "$ADV" --out_dir "$ADIR" \
  --n_pairs "$NPAIRS" --lr "$LR" --seed 0 >> "$DL" 2>&1
if [[ ! -d "$ADIR/adapter-step80" ]]; then
  echo "[$(date -Is)] ERROR: attack did not produce adapter-step80; aborting" | tee -a "$DL"; exit 1
fi

# 2) per checkpoint: merge -> eval harmbench + strongreject -> delete merged weights
for s in "${STEPS[@]}"; do
  MERGED="$WORK/merged-step${s}"
  echo "[$(date -Is)] merge+eval step=$s" | tee -a "$DL"
  python scripts/tamper_merge.py --base "$MODEL" --adapter "$ADIR/adapter-step${s}" --out "$MERGED" >> "$DL" 2>&1
  # instruct model -> hf chat template (do NOT set TEMPLATE)
  bash scripts/run_row.sh "$MERGED" main harmbench:default        "2026-07-29-tamper-${NAME}-step${s}-harmbench"     0 >> "$DL" 2>&1
  bash scripts/run_row.sh "$MERGED" main strongreject:logprobs    "2026-07-29-tamper-${NAME}-step${s}-strongreject"  0 >> "$DL" 2>&1
  rm -rf "$MERGED"   # delete attacked full weights immediately after measuring
  echo "[$(date -Is)] step=$s done; merged weights deleted" | tee -a "$DL"
done

# 3) cleanup: delete adapters (only ASR provenance in runs/ survives)
rm -rf "$WORK"
echo "[$(date -Is)] tamper DONE name=$NAME; adapters+merged deleted; ASR curves in runs/2026-07-29-tamper-${NAME}-step*" | tee -a "$DL"
