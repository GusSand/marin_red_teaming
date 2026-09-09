#!/bin/bash
# S1-PREFIX: is Starling's delivery framing proximally sufficient to move Phoenix?
# Plan: docs/experiments/09-08_prefix_framing-intervention.md (frozen 2026-09-08)
# Submit: cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/prefix_framing.sbatch
#
# 3 arms x 5 seeds = 15 runs, SEQUENTIALLY in ONE GPU allocation. Never an array: all three arms
# are compared to each other, and an array confounds arm with hardware (CLAUDE.md, the
# gl040/gl064/gl024 error). Phoenix only; Starling's level is a reference from the traj4 runs and
# is a declared cross-job limitation, not an arm here.
#
# The three arms differ ONLY in the scaffold file. The provenance guard below records the template
# sha256, so a completed run cannot be silently reused under a different scaffold -- which is the
# failure that would quietly turn this experiment into three copies of the baseline.
#SBATCH --job-name=marin-prefix
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
log_init "prefix"
log_trap_exit

RUN_PREFIX="${MARIN_RUN_PREFIX:-2026-09-08-prefix-h200}"
_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
PYBIN="$ROOT/.venv-safety-eval/bin/python"

declare -A TPL=(
  [none]="$ROOT/config/base_template_v2.txt"
  [delivery]="$ROOT/config/base_template_v2_delivery.txt"
  [deflect]="$ROOT/config/base_template_v2_deflect.txt"
)
ARMS=(none delivery deflect)
SEEDS=(0 1 2 3 4)

# SCAFFOLD GATE. All three must exist, all three must carry the User:/Assistant: markers, and all
# three must be genuinely DIFFERENT files. Three identical scaffolds would produce a null with no
# error anywhere in the log.
for ARM in "${ARMS[@]}"; do
    [[ -f "${TPL[$ARM]}" ]] || log_die "scaffold missing for arm $ARM at ${TPL[$ARM]}"
    grep -q '{instruction}' "${TPL[$ARM]}" || log_die "scaffold ${TPL[$ARM]} lacks {instruction}"
    grep -q 'Assistant:' "${TPL[$ARM]}" || log_die "scaffold ${TPL[$ARM]} lacks the Assistant: marker"
done
# sha256 via python: sha256sum/shasum availability differs between the login node and the compute
# node, and a missing hasher here would silently disable the distinctness gate.
tplsha() { "$PYBIN" -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }
N_DISTINCT="$(for ARM in "${ARMS[@]}"; do tplsha "${TPL[$ARM]}"; done | sort -u | wc -l)"
[[ "$N_DISTINCT" -eq 3 ]] || log_die "the three arm scaffolds are not distinct ($N_DISTINCT unique hashes)"
log INFO "scaffold gate OK: 3 distinct templates"

THIS_GPU_MODEL="$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
THIS_DRIVER="$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
GPU_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | head -1)"
log INFO "host=$(hostname -s) gpu=$THIS_GPU_MODEL uuid=$GPU_UUID driver=$THIS_DRIVER prefix=$RUN_PREFIX"

# The traj4 reference runs are NVIDIA H200 / driver 580.82.07. The within-job arm contrast does not
# depend on this, but f's denominator does, so a mismatch is recorded as a declared limitation.
if [[ "$THIS_GPU_MODEL" != "NVIDIA H200" ]]; then
    log WARN "GPU $THIS_GPU_MODEL != traj4 reference NVIDIA H200 -- f's denominator is cross-hardware; declare it"
fi
if [[ "$THIS_DRIVER" != "580.82.07" ]]; then
    log WARN "DRIVER MISMATCH: this=$THIS_DRIVER traj4=580.82.07 -- declared limitation on f only"
fi

SHA="$(cat "$_HUB/refs/phoenix")"
MODEL="$_HUB/snapshots/$SHA"
[[ -d "$MODEL" ]] || log_die "no phoenix snapshot at $MODEL"
log INFO "phoenix sha=${SHA:0:12}"

provenance_compatible() {
    local pf="$1" seed="$2" tplsha="$3"
    [[ -s "$pf" ]] || return 1
    "$PYBIN" - "$pf" "$seed" "$tplsha" "$THIS_GPU_MODEL" "$THIS_DRIVER" "$SHA" <<'PY'
import json, sys
pf, seed, tplsha, gpu_model, driver, msha = sys.argv[1:7]
try: p = json.load(open(pf))
except Exception: sys.exit(1)
have_driver = str(p.get("nvidia_smi", "")).split(",")[-1].strip()
for k, v in [("gpu", gpu_model), ("vllm_v1_multiprocessing", "0"), ("sampling_seed_env", str(seed))]:
    if str(p.get(k, "<missing>")) != v:
        print(f"{k}: have {p.get(k,'<missing>')!r}, need {v!r}"); sys.exit(1)
if have_driver != driver: print(f"driver: {have_driver!r} != {driver!r}"); sys.exit(1)
if msha not in str(p.get("model", "")): print(f"model {p.get('model')!r} lacks {msha!r}"); sys.exit(1)
# The arm IS the template. Refusing to reuse a run whose scaffold hash differs is what stops this
# experiment silently collapsing into three copies of one arm.
if str(p.get("template_sha256", "<missing>")) != tplsha:
    print(f"template_sha256: have {p.get('template_sha256','<missing>')!r}, need {tplsha!r}"); sys.exit(1)
sys.exit(0)
PY
}

for ARM in "${ARMS[@]}"; do
    export TEMPLATE="${TPL[$ARM]}"
    TPLSHA="$(tplsha "$TEMPLATE")"
    log INFO "arm=$ARM template=$TEMPLATE sha256=${TPLSHA:0:12}"
    for SEED in "${SEEDS[@]}"; do
        NAME="${RUN_PREFIX}-${ARM}-harmbench-s${SEED}"
        RUNDIR="$ROOT/runs/$NAME"
        if [[ -s "$RUNDIR/metrics.json" ]]; then
            if why="$(provenance_compatible "$RUNDIR/provenance.json" "$SEED" "$TPLSHA")"; then
                log INFO "skip $NAME (complete, provenance verified)"; continue
            fi
            log_die "REFUSING to reuse $NAME: provenance incompatible [$why]. Bump MARIN_RUN_PREFIX or move the dir deliberately."
        fi
        export SAFETYEVAL_SAMPLING_SEED="$SEED"
        log_phase "$ARM s$SEED"
        log_heartbeat_start 120 "$RUNDIR/all.json"
        bash "$WORK/scripts/run_row.sh" "$MODEL" "phoenix-$ARM" harmbench:default "$NAME" "$SEED" \
            || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME"; }
        log_heartbeat_stop
        [[ -s "$RUNDIR/all.json" ]] || log_die "no all.json for $NAME"
        # Record the scaffold identity next to the run so the arm is recoverable from the artifact.
        "$PYBIN" - "$RUNDIR/provenance.json" "$TPLSHA" "$ARM" <<'PY'
import json, sys
pf, tplsha, arm = sys.argv[1:4]
p = json.load(open(pf)); p["template_sha256"] = tplsha; p["prefix_arm"] = arm
json.dump(p, open(pf, "w"), indent=2)
PY
        LABELS="$LABEL_ROOT/$NAME"; mkdir -p "$LABELS"
        cp -f "$RUNDIR/all.json" "$LABELS/all.json" || log_die "failed to preserve labels for $NAME"
        if cmp -s "$RUNDIR/all.json" "$LABELS/all.json"; then
            rm -f "$RUNDIR/all.json"; ln -s "$LABELS/all.json" "$RUNDIR/all.json"
        fi
        log INFO "done $NAME"
    done
    log INFO "arm $ARM complete (5 seeds)"
done
log INFO "all 15 runs complete under prefix $RUN_PREFIX"
