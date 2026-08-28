#!/bin/bash
# 08-27 experiment, H1b CONTROL: benign compliance across the six Marin base revisions.
#
# This is the arm that decides whether S9 is a safety finding at all. If benign compliance
# rises as much as harmful compliance does across phoenix -> deeper-starling, the trajectory
# is general instruction-following and the cooldown-mix ablation is aimed at the wrong thing.
# Prompted by an outside question on the slide: "could ironically be improved instruction
# following depending on how it's prompted."
#
# Spec: docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md
#
# Submit from the remote workspace, through the preflight wrapper, never bare sbatch:
#   cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/benign_control.sbatch
#
# Array is 18 = 6 revisions x 3 seeds. Run the PHOENIX rows first as the port gate
# (--array=9,10,11) and only launch the rest once the PROTOCOL/INVARIANT gate passes
# (docs/experiments/08-27_...md). The old 49% +/- 3pp level gate was withdrawn as a
# pre-data deviation: the historical target is itself a noisy 3-run mean.
#
# Watch progress across every task with a single tail:
#   ssh torch 'tail -f /scratch/gs157/marin-red-teaming/logs/progress.log'
#SBATCH --job-name=marin-benign-ctrl
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=l40s_public
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
# NO DEFAULT ARRAY. A bare submit must not silently run all 18 tasks: the protocol/
# invariant port gate (phoenix end-to-end + checks 1-4 in the spec) has to pass first.
# Pass the range explicitly, e.g. --array=9,10,11 for phoenix.
#SBATCH --array=9
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
TAGS=(kestrel ocelot jellyfish phoenix starling deeper-starling)
TAG="${TAGS[$((SLURM_ARRAY_TASK_ID / 3))]}"
# Seeds 0/1/2 match the 07-28 runs exactly (r1=0, r2=1, r3=2). Do not renumber:
# the reproduction gate compares against those runs.
SEED=$(( SLURM_ARRAY_TASK_ID % 3 ))
NAME="2026-08-27-marin-benign-ctrl-${TAG}-benign-r$((SEED + 1))"

source "$WORK/scripts/log_lib.sh"
log_init "$TAG-r$((SEED + 1))"
log_trap_exit

# The seed must reach vLLM's sampler. PYTHONHASHSEED does NOT do this; the patch does.
export SAFETYEVAL_SAMPLING_SEED="$SEED"

# CRITICAL: base models have no chat template. Without this scaffold the model echoes the
# prompt back and WildGuard scores the echo as compliance -- the exact confound that made the
# first base numbers invalid (see docs/experiments/07-28..., report SUMMARY Part 4).
# run_row.sh reads TEMPLATE and passes it as --model_input_template_path_or_name; the default
# is "hf", which for a base model means NO scaffold at all.
export TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "base scaffold missing at $TEMPLATE"

# Resolve the revision to a concrete on-disk snapshot and pass THAT. Passing a repo id makes
# vLLM and the harness do their own network/cache lookups, which is how the wrong cache got
# used. An absolute path also bakes the exact commit into the run, which is what protocol
# identity actually requires.
_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
_REF="$_HUB/refs/$TAG"
[[ -f "$_REF" ]] || log_die "no cached revision for $TAG under $_HUB; run scripts/prefetch_revisions.py on the login node first"
RESOLVED_SHA="$(cat "$_REF")"; export RESOLVED_SHA
MODEL_PATH="$_HUB/snapshots/$RESOLVED_SHA"
[[ -d "$MODEL_PATH" ]] || log_die "ref $TAG -> $RESOLVED_SHA but no snapshot dir at $MODEL_PATH"

RUNDIR="$ROOT/runs/$NAME"
log INFO "tag=$TAG seed=$SEED name=$NAME"
log INFO "template=$TEMPLATE"
log INFO "gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | tr '\n' ' ' || echo unavailable)"
log INFO "hf_home=$HF_HOME hub=$HF_HUB_CACHE"
log INFO "model=$MODEL_PATH (sha ${RESOLVED_SHA:0:12})"
log INFO "rundir=$RUNDIR"

# A crashed vLLM engine previously left the task in RUNNING with no output for 14 minutes
# (job 16488625). The heartbeat makes that state visible; the watched file shows real progress.
log_heartbeat_start 120 "$RUNDIR/all.json"

log_phase "generation+judging"
bash "$WORK/scripts/run_row.sh" \
    "$MODEL_PATH" \
    "$TAG" \
    wildjailbreak:benign \
    "$NAME" \
    "$SEED" || log_die "run_row.sh failed for $NAME (see $WORK/logs/$NAME.log)"

log_heartbeat_stop

[[ -s "$RUNDIR/all.json" ]]     || log_die "no all.json produced for $NAME (per-instance labels are the point of this rerun)"
[[ -s "$RUNDIR/metrics.json" ]] || log_die "no metrics.json produced for $NAME"

log_phase "keep labels"
# Copied FIRST, before any other post-processing can fail. run_row.sh refuses to re-run when
# metrics.json exists, so a crash between metrics.json and this copy would leave the task
# unresubmittable without hand-deleting the run dir -- and the whole reason this experiment
# exists is that the 07-28 all.json files were lost. Idempotent, so a retry is safe.
LABELS="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}/$NAME"
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
# Scratch is not backed up and IS flushed (CLAUDE.md). These labels are irreplaceable without
# a full re-run, so mirror them to $ARCHIVE, which is backed up.
if [[ -n "${ARCHIVE:-}" && -d "${ARCHIVE:-}" ]]; then
    mkdir -p "$ARCHIVE/marin-misinfo-labels/$NAME" \
      && cp -f "$RUNDIR/all.json" "$ARCHIVE/marin-misinfo-labels/$NAME/all.json" \
      && log INFO "labels mirrored to \$ARCHIVE (backed up)" \
      || log WARN "could not mirror labels to \$ARCHIVE; scratch copy is the only one"
else
    log WARN "\$ARCHIVE unset; labels exist only on flushed scratch"
fi

# Headline number straight out of the run, so progress.log carries the result and you do not
# have to open metrics.json to know whether the gate passed.
log_phase "report"
"$ROOT/.venv-safety-eval/bin/python" "$WORK/scripts/report_benign.py" \
    "$RUNDIR/metrics.json" "$TAG" 2>&1 | while read -r l; do log RESULT "$l"; done
