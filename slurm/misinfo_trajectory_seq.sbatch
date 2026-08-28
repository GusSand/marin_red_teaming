#!/bin/bash
# THE INFERENTIAL RUN for docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md
#
# 18 runs = 6 revisions x 3 seeds, executed SEQUENTIALLY on ONE GPU.
#
# Why not the --array in misinfo_refusal_vs_capability.sbatch:
#   A Slurm array scatters tasks across nodes. The whole content of this experiment is a
#   comparison ACROSS revisions, so an array confounds hardware with revision -- the exact
#   error that invalidated the first determinism test (gl040/gl064/gl024, 2026-08-27). The
#   standing rule in CLAUDE.md is "any comparison between runs must hold the GPU fixed".
#   Determinism runs took ~400s each, so 18 sequential runs is ~2.1h. Pinning is cheap.
#   Logged as a documented pre-data deviation (execution topology only: same models, seeds,
#   prompts, scaffold, judge and metric).
#
# Prerequisite: all four port-gate checks passed 2026-08-27. See the experiment doc.
#
# Submit through the preflight wrapper, never bare sbatch:
#   cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/misinfo_trajectory_seq.sbatch
#
# Watch:
#   ssh torch 'tail -f /scratch/gs157/marin-red-teaming/logs/progress.log'
#
#SBATCH --job-name=marin-misinfo-traj
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=l40s_public
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
# DELIBERATELY NOT AN ARRAY -- see the header. All 18 runs share one physical GPU.
#SBATCH --time=12:00:00
# NOTE: logs/ is gitignored, so a fresh rsync of tracked files does not create it and
# Slurm will fail to launch with no log to explain why. submit.sh mkdir -p's it.
#SBATCH --output=logs/%x_%j.out

set -euo pipefail

WORK="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
export MARIN_RT_ROOT="$WORK"
ROOT="$WORK/repro-olmo3-safety"
export HF_HOME="$WORK/hf_cache"   # workspace owns its cache; do NOT inherit a global HF_HOME
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key-not-used}"
# WildGuard (allenai/wildguard) is a gated repo and there is no HF token on Torch. It was
# already downloaded by the safety-decay project and copied into this workspace's hf_cache,
# so run fully offline: no network, no token, and a guarantee the judge weights never change
# under us mid-study. The marin base model is public and prefetched by prefetch_revisions.py.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
# Pin every HF cache var, not just HF_HOME. vLLM resolved a repo-id against a DIFFERENT cache
# (the global /scratch/gs157/.huggingface) even with HF_HOME set, and that cache has no
# WildGuard -- so generation succeeded and the judge died on a missing tokenizer (job 16492304).
export HF_HUB_CACHE="$HF_HOME/hub"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
# vLLM's documented first step for reproducible offline V1 inference. Gate check 3 validated
# same-seed reproduction and different-seed divergence on Torch WITH this set; do not drop it.
export VLLM_ENABLE_V1_MULTIPROCESSING=0

source "$WORK/scripts/log_lib.sh"
log_init "misinfo-traj"
log_trap_exit

# CRITICAL: base models have no chat template. Without this scaffold the model echoes the
# prompt back and WildGuard scores the echo as compliance -- the exact confound that made the
# first base numbers invalid (docs/experiments/07-28..., report SUMMARY Part 4).
export TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "base scaffold missing at $TEMPLATE"

_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"

# Revision order is the pretraining trajectory order. Seeds 0/1/2 match the 07-28 runs exactly
# (r1=0, r2=1, r3=2). Do not renumber: historical comparisons are keyed to those.
TAGS=(kestrel ocelot jellyfish phoenix starling deeper-starling)
SEEDS=(0 1 2)

log INFO "host=$(hostname -s) gpu_uuid=$(nvidia-smi --query-gpu=uuid --format=csv,noheader | tr '\n' ' ')"
log INFO "driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
log INFO "gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tr '\n' ' ')"
log INFO "VLLM_ENABLE_V1_MULTIPROCESSING=$VLLM_ENABLE_V1_MULTIPROCESSING"
log INFO "template=$TEMPLATE"
log INFO "plan: 6 tags x 3 seeds = 18 runs, SEQUENTIALLY on this one GPU"

# Fail before burning any GPU time if a revision is missing, rather than 4 tags in.
for TAG in "${TAGS[@]}"; do
    [[ -f "$_HUB/refs/$TAG" ]] || log_die "no cached revision for $TAG; run scripts/prefetch_revisions.py on the login node first"
done
log INFO "all 6 revisions present in the workspace cache"

for TAG in "${TAGS[@]}"; do
  for SEED in "${SEEDS[@]}"; do
    NAME="2026-08-27-marin-misinfo-rvc-${TAG}-harmbench-r$((SEED + 1))"
    RUNDIR="$ROOT/runs/$NAME"

    # Idempotent: a resubmit after a walltime kill resumes instead of redoing finished work.
    if [[ -s "$RUNDIR/metrics.json" ]]; then
        log INFO "skip $NAME (already complete)"
        continue
    fi

    # The seed must reach vLLM's sampler. PYTHONHASHSEED does NOT do this; the patch does.
    export SAFETYEVAL_SAMPLING_SEED="$SEED"

    # Resolve the revision to a concrete on-disk snapshot and pass THAT. Passing a repo id makes
    # vLLM and the harness do their own cache lookups, which is how the wrong cache got used.
    # An absolute path also bakes the exact commit into the run, which is what protocol
    # identity actually requires.
    RESOLVED_SHA="$(cat "$_HUB/refs/$TAG")"; export RESOLVED_SHA
    MODEL_PATH="$_HUB/snapshots/$RESOLVED_SHA"
    [[ -d "$MODEL_PATH" ]] || log_die "ref $TAG -> $RESOLVED_SHA but no snapshot dir at $MODEL_PATH"

    log_phase "$TAG r$((SEED + 1))"
    log INFO "tag=$TAG seed=$SEED model=$MODEL_PATH (sha ${RESOLVED_SHA:0:12})"

    # A crashed vLLM engine previously left a task in RUNNING with no output for 14 minutes
    # (job 16488625). The heartbeat makes that state visible.
    log_heartbeat_start 120 "$RUNDIR/all.json"
    bash "$WORK/scripts/run_row.sh" \
        "$MODEL_PATH" \
        "$TAG" \
        harmbench:default \
        "$NAME" \
        "$SEED" || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME (see $WORK/logs/$NAME.log)"; }
    log_heartbeat_stop

    [[ -s "$RUNDIR/all.json" ]]     || log_die "no all.json produced for $NAME (per-instance labels are the point of this rerun)"
    [[ -s "$RUNDIR/metrics.json" ]] || log_die "no metrics.json produced for $NAME"

    # Copied FIRST, before any other post-processing can fail. run_row.sh refuses to re-run when
    # metrics.json exists, so a crash between metrics.json and this copy would leave the run
    # unresubmittable without hand-deleting the run dir -- and the whole reason this experiment
    # exists is that the 07-28 all.json files were lost. Idempotent, so a retry is safe.
    LABELS="$LABEL_ROOT/$NAME"
    mkdir -p "$LABELS" || log_die "cannot create $LABELS"
    cp -f "$RUNDIR/all.json" "$LABELS/all.json" || log_die "failed to preserve labels to $LABELS"
    log INFO "labels kept at $LABELS/all.json ($(du -h "$LABELS/all.json" | cut -f1))"

    # The repo copy is gitignored but still inside the tree; an accidental `git add -f` or a
    # tarball of the repo would ship untruncated harmful completions. The canonical copy is the
    # one outside the repo, so drop the in-tree one once it is safely preserved.
    if [[ -s "$LABELS/all.json" ]] && cmp -s "$RUNDIR/all.json" "$LABELS/all.json"; then
        rm -f "$RUNDIR/all.json"
        ln -s "$LABELS/all.json" "$RUNDIR/all.json"   # keep the path working for analysis
        log INFO "in-tree all.json replaced by a symlink to the out-of-tree copy"
    fi

    # Scratch is not backed up and IS flushed (CLAUDE.md). These labels are irreplaceable
    # without a full re-run, so mirror them to $ARCHIVE, which is backed up.
    if [[ -n "${ARCHIVE:-}" && -d "${ARCHIVE:-}" ]]; then
        mkdir -p "$ARCHIVE/marin-misinfo-labels/$NAME" \
          && cp -fL "$RUNDIR/all.json" "$ARCHIVE/marin-misinfo-labels/$NAME/all.json" \
          && log INFO "labels mirrored to \$ARCHIVE (backed up)" \
          || log WARN "could not mirror labels to \$ARCHIVE; scratch copy is the only one"
    else
        log WARN "\$ARCHIVE unset; labels exist only on flushed scratch"
    fi

    # Headline number straight out of the run, so progress.log carries the result and you do
    # not have to open metrics.json to know where the trajectory is going.
    "$ROOT/.venv-safety-eval/bin/python" - "$RUNDIR/metrics.json" "$TAG r$((SEED + 1))" <<'PY' 2>&1 | while read -r l; do log RESULT "$l"; done
import json, sys
m = json.load(open(sys.argv[1]))["harmbench:default"]
misinfo = m["inverted_semantic_category_asr_lower"]["misinformation_disinformation"]
print(f"{sys.argv[2]}: misinfo ASR = {100 * (1 - misinfo):.2f}%  ({(1 - misinfo) * 54:.0f}/54)  micro = {100 * (1 - m['inverted_micro_asr_lower']):.2f}%")
PY
  done
done

log INFO "all 18 runs complete on ONE gpu ($(hostname -s)); analyse with scripts/ (see experiment doc)"
