#!/bin/bash
# GATE CHECK 3, done properly: is generation reproducible at fixed seed on FIXED hardware,
# with vLLM's documented reproducibility mode enabled?
#
# The first attempt was invalid: three array tasks landed on three different GPUs, and
# VLLM_ENABLE_V1_MULTIPROCESSING was unset. This version fixes both.
#   - one job, one GPU, five runs SEQUENTIALLY: seed 0 x3, then seed 1 x2
#   - VLLM_ENABLE_V1_MULTIPROCESSING=0 (vLLM's documented first step for reproducible V1)
#   - provenance records hostname, GPU UUID, driver and engine flags
# Compared afterwards at three levels, because token-exact equality is the harshest possible
# test and says nothing on its own about labels or the reported rate:
#   scripts/compare_determinism.py <rundir> ...
# Spec: docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md
#
# Submit from the remote workspace, through the preflight wrapper, never bare sbatch:
#   cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/misinfo_refusal_vs_capability.sbatch
#
# Array is 18 = 6 revisions x 3 seeds. Run the PHOENIX rows first as the port gate
# (--array=9,10,11) and only launch the rest once the PROTOCOL/INVARIANT gate passes
# (docs/experiments/08-27_...md). The old 49% +/- 3pp level gate was withdrawn as a
# pre-data deviation: the historical target is itself a noisy 3-run mean.
#
# Watch progress across every task with a single tail:
#   ssh torch 'tail -f /scratch/gs157/marin-red-teaming/logs/progress.log'
#SBATCH --job-name=marin-determinism
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=l40s_public
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
# DELIBERATELY NOT AN ARRAY. All runs must execute sequentially on ONE GPU: vLLM only claims
# reproducibility on identical hardware, and the previous attempt compared across three nodes.
#SBATCH --time=08:00:00
# NOTE: logs/ is gitignored, so a fresh rsync of tracked files does not create it and
# Slurm will fail to launch with no log to explain why. submit.sh mkdir -p's it.
#SBATCH --output=logs/%x_%A_%a.out

set -euo pipefail

WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export MARIN_RT_ROOT="$WORK"
ROOT="$WORK/repro-olmo3-safety"
export HF_HOME="$WORK/hf_cache"   # workspace owns its cache; do NOT inherit a global HF_HOME
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"
# WildGuard (allenai/wildguard) is a gated repo and there is no HF token on Torch. It was
# already downloaded by the safety-decay project and copied into this workspace's hf_cache,
# so run fully offline: no network, no token, and a guarantee the judge weights never change
# under us mid-study. The marin base model is public and also cached after the first pull.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
# Pin every HF cache var, not just HF_HOME. vLLM resolved a repo-id against a DIFFERENT cache
# (the global /scratch/gs157/.huggingface) even with HF_HOME set, and that cache has no
# WildGuard -- so generation succeeded and the judge died on a missing tokenizer (job 16492304).
export HF_HUB_CACHE="$HF_HOME/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"

# Revision order is fixed: index/3 selects the tag, index%3 selects the seed.
# Gate check 3 (spec: "same-seed reproduction plus different-seed divergence on Torch").
# Fixed on phoenix; only the seed varies.
TAG=phoenix
# seed 0 three times, then seed 1 twice -- sequentially, same GPU.
RUNS=("0:a" "0:b" "0:c" "1:a" "1:b")
# (seed/rep are set per-iteration in the loop below)

source "$WORK/scripts/log_lib.sh"
log_init "determinism"
log_trap_exit

# The seed must reach vLLM's sampler. PYTHONHASHSEED does NOT do this; the patch does.
# vLLM's documented first step for reproducible offline V1 inference. Absent this, the engine
# runs multiprocessing and reproducibility is explicitly not guaranteed.
export VLLM_ENABLE_V1_MULTIPROCESSING=0

# CRITICAL: base models have no chat template. Without this scaffold the model echoes the
# prompt back and WildGuard scores the echo as compliance -- the exact confound that made the
# first base numbers invalid (see docs/experiments/07-28..., report SUMMARY Part 4).
# run_row.sh reads TEMPLATE and passes it as --model_input_template_path_or_name; the default
# is "hf", which for a base model means NO scaffold at all.
export TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "base scaffold missing at $TEMPLATE"

# Resolve the revision to a concrete on-disk snapshot and pass THAT (see the main sbatch).
_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
_REF="$_HUB/refs/$TAG"
[[ -f "$_REF" ]] || log_die "no cached revision for $TAG under $_HUB"
RESOLVED_SHA="$(cat "$_REF")"; export RESOLVED_SHA
MODEL_PATH="$_HUB/snapshots/$RESOLVED_SHA"
[[ -d "$MODEL_PATH" ]] || log_die "ref $TAG -> $RESOLVED_SHA but no snapshot dir"

log INFO "host=$(hostname -s) gpu_uuid=$(nvidia-smi --query-gpu=uuid --format=csv,noheader | tr '\n' ' ')"
log INFO "driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
log INFO "VLLM_ENABLE_V1_MULTIPROCESSING=$VLLM_ENABLE_V1_MULTIPROCESSING"
log INFO "model=$MODEL_PATH (sha ${RESOLVED_SHA:0:12})"
log INFO "plan: seed 0 x3 then seed 1 x2, SEQUENTIALLY on this one GPU"

LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"

for spec in "${RUNS[@]}"; do
    SEED="${spec%%:*}"; REP="${spec##*:}"
    NAME="2026-08-27-determinism-${TAG}-s${SEED}${REP}"
    RUNDIR="$ROOT/runs/$NAME"
    export SAFETYEVAL_SAMPLING_SEED="$SEED"

    if [[ -f "$RUNDIR/metrics.json" ]]; then
        log INFO "skip $NAME (already complete)"
        continue
    fi

    log_phase "run s${SEED}${REP}"
    log_heartbeat_start 120 "$RUNDIR/all.json"
    bash "$WORK/scripts/run_row.sh" \
        "$MODEL_PATH" \
        "$TAG" \
        harmbench:default \
        "$NAME" \
        "$SEED" || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME"; }
    log_heartbeat_stop

    [[ -s "$RUNDIR/all.json" ]] || log_die "no all.json for $NAME"
    LABELS="$LABEL_ROOT/$NAME"
    mkdir -p "$LABELS" && cp -f "$RUNDIR/all.json" "$LABELS/all.json"
    log INFO "labels kept at $LABELS/all.json"

    "$ROOT/.venv-safety-eval/bin/python" - "$RUNDIR/metrics.json" "s${SEED}${REP}" <<'PYEOF' 2>&1 | while read -r l; do log RESULT "$l"; done
import json, sys
m = json.load(open(sys.argv[1]))["harmbench:default"]
r = m["inverted_semantic_category_asr_lower"]["misinformation_disinformation"]
print(f"{sys.argv[2]}: misinfo ASR = {100*(1-r):.2f}%  ({(1-r)*54:.0f}/54 items)")
PYEOF
done

log INFO "all runs complete on ONE gpu; compare with scripts/compare_determinism.py"
