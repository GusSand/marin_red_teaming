#!/bin/bash
# S1-CKPT: localize the Phoenix->Starling change across three public cooldown revisions.
# Plan: docs/experiments/09-08_cooldown_localization.md (frozen 2026-09-08)
# Submit: cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/cooldown_localization.sbatch
#
# 3 revisions x 10 seeds = 30 runs, ~2.4h, SEQUENTIALLY in ONE GPU allocation. Never an array:
# every inference here is a comparison ACROSS revisions, and an array confounds hardware with
# revision (CLAUDE.md, the gl040/gl064/gl024 error). Exceeds the 1h50 cap, so it is resumed by
# resubmitting; the provenance guard below is what makes resume safe.
#
# THESE REVISIONS HAVE NO TAG. The trajectory harness resolves tags via $_HUB/refs/<tag>; these
# are reachable only by commit SHA, so the usual guard against loading the wrong weights is
# absent. Every shard was hashed against its recorded LFS oid by
# scripts/prefetch_cooldown_revisions.py before this job may run, and that report is re-checked
# here at startup.
#SBATCH --job-name=marin-cooldown
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:50:00
#SBATCH --output=logs/%x_%j.out
set -euo pipefail

WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export MARIN_RT_ROOT="$WORK"
ROOT="$WORK/repro-olmo3-safety"
export HF_HOME="$WORK/hf_cache"
export HF_HUB_CACHE="$HF_HOME/hub" HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"
export VLLM_ENABLE_V1_MULTIPROCESSING=0

source "$WORK/scripts/log_lib.sh"
log_init "cooldown"
log_trap_exit

RUN_PREFIX="${MARIN_RUN_PREFIX:-2026-09-08-cooldown-h200}"
export TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "base scaffold missing at $TEMPLATE"

_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
PYBIN="$ROOT/.venv-safety-eval/bin/python"
VERIFY="$WORK/outputs/cooldown_download_verification.json"

# Pinned revisions, 25% / 50% / 75% of the cooldown. Full SHAs, never prefixes.
declare -A REVS=(
  [cooldown-1340000]=de183cad08bae55f8a07d346442efe20469d2144
  [cooldown-1360000]=83e7d73c64bbec3be13b6f62650e9495b3590c12
  [cooldown-1380000]=34b1c23173e12f88f0a1999c57f68d5b8d7f7adb
)
ORDER=(cooldown-1340000 cooldown-1360000 cooldown-1380000)
SEEDS=(0 1 2 3 4 5 6 7 8 9)

THIS_GPU_MODEL="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
THIS_DRIVER="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
log INFO "host=$(hostname -s) gpu=$THIS_GPU_MODEL driver=$THIS_DRIVER prefix=$RUN_PREFIX"

# COMPARABILITY GATE. The contrast is against the traj4 endpoint runs, whose provenance records
# NVIDIA H200 / driver 580.82.07. A mismatch is a declared limitation, never silently absorbed.
ENDPOINT_GPU="NVIDIA H200"; ENDPOINT_DRIVER="580.82.07"
[[ "$THIS_GPU_MODEL" == "$ENDPOINT_GPU" ]] || log_die "GPU $THIS_GPU_MODEL != endpoint $ENDPOINT_GPU; the cross-revision comparison would be confounded"
if [[ "$THIS_DRIVER" != "$ENDPOINT_DRIVER" ]]; then
    log WARN "DRIVER MISMATCH: this=$THIS_DRIVER endpoints=$ENDPOINT_DRIVER -- record as a declared limitation on the comparison"
fi

# WEIGHT GATE. Refuse to run unless every shard of every revision was verified against its
# recorded LFS oid. Resolving by SHA outside refs/ removes the normal protection, and the
# failure that matters is silently measuring an endpoint twice.
[[ -s "$VERIFY" ]] || log_die "missing $VERIFY; run scripts/prefetch_cooldown_revisions.py first"
"$PYBIN" - "$VERIFY" "${REVS[cooldown-1340000]}" "${REVS[cooldown-1360000]}" "${REVS[cooldown-1380000]}" <<'PY' || log_die "weight verification gate FAILED"
import json, sys
rep = json.load(open(sys.argv[1])); want = set(sys.argv[2:5])
assert rep.get("all_revisions_verified") is True, "all_revisions_verified is not True"
have = set(rep["revisions"])
assert want <= have, f"verification report is missing {sorted(want - have)}"
for r in want:
    v = rep["revisions"][r]
    assert v["all_shards_verified"] is True, f"{r}: shards not verified"
    assert len(v["shards"]) == 4, f"{r}: expected 4 shards, got {len(v['shards'])}"
# the three must be genuinely different weights, not one snapshot aliased three ways
first = {r: sorted(v["shards"].items())[0][1]["sha256"] for r, v in rep["revisions"].items() if r in want}
assert len(set(first.values())) == 3, f"revisions share a shard hash: {first}"
print("weight gate OK: 12 shards verified, 3 distinct revisions")
PY
log INFO "weight verification gate passed"

provenance_compatible() {
    local pf="$1" seed="$2" msha="$3"
    [[ -s "$pf" ]] || return 1
    "$PYBIN" - "$pf" "$seed" "$msha" "$THIS_GPU_MODEL" "$THIS_DRIVER" <<'PY'
import json, sys
pf, seed, msha, gpu_model, driver = sys.argv[1:6]
try: p = json.load(open(pf))
except Exception: sys.exit(1)
have_driver = str(p.get("nvidia_smi", "")).split(",")[-1].strip()
for k, v in [("gpu", gpu_model), ("vllm_v1_multiprocessing", "0"), ("sampling_seed_env", str(seed)),
             ("safety_eval_sha", "060cc903d64703214c549b5c3a30ea8ceef2e588")]:
    if str(p.get(k, "<missing>")) != v:
        print(f"{k}: have {p.get(k,'<missing>')!r}, need {v!r}"); sys.exit(1)
if have_driver != driver: print(f"driver: {have_driver!r} != {driver!r}"); sys.exit(1)
if msha not in str(p.get("model", "")): print(f"model {p.get('model')!r} lacks {msha!r}"); sys.exit(1)
sys.exit(0)
PY
}

for LABEL in "${ORDER[@]}"; do
    SHA="${REVS[$LABEL]}"
    MODEL_PATH="$_HUB/snapshots/$SHA"
    [[ -d "$MODEL_PATH" ]] || log_die "no snapshot dir for $LABEL at $MODEL_PATH"
    for SEED in "${SEEDS[@]}"; do
        NAME="${RUN_PREFIX}-${LABEL}-harmbench-s${SEED}"
        RUNDIR="$ROOT/runs/$NAME"
        if [[ -s "$RUNDIR/metrics.json" ]]; then
            if why="$(provenance_compatible "$RUNDIR/provenance.json" "$SEED" "$SHA")"; then
                log INFO "skip $NAME (complete, provenance verified)"; continue
            fi
            log_die "REFUSING to reuse $NAME: provenance incompatible [$why]. Bump MARIN_RUN_PREFIX or move the dir deliberately."
        fi
        export SAFETYEVAL_SAMPLING_SEED="$SEED"
        log_phase "$LABEL s$SEED"
        log INFO "revision=$LABEL sha=${SHA:0:12} seed=$SEED model=$MODEL_PATH"
        log_heartbeat_start 120 "$RUNDIR/all.json"
        bash "$WORK/scripts/run_row.sh" "$MODEL_PATH" "$LABEL" harmbench:default "$NAME" "$SEED" \
            || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME"; }
        log_heartbeat_stop
        [[ -s "$RUNDIR/all.json" ]] || log_die "no all.json for $NAME"
        LABELS="$LABEL_ROOT/$NAME"; mkdir -p "$LABELS"
        cp -f "$RUNDIR/all.json" "$LABELS/all.json" || log_die "failed to preserve labels for $NAME"
        if cmp -s "$RUNDIR/all.json" "$LABELS/all.json"; then
            rm -f "$RUNDIR/all.json"; ln -s "$LABELS/all.json" "$RUNDIR/all.json"
        fi
        log INFO "done $NAME"
    done
    log INFO "revision $LABEL complete (10 seeds)"
done
log INFO "all 30 runs complete under prefix $RUN_PREFIX"
