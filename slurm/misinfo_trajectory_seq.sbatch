#!/bin/bash
# THE INFERENTIAL RUN for docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md
#
# 46 runs, executed SEQUENTIALLY inside ONE GPU allocation:
#   endpoint tags (jellyfish, phoenix, starling, deeper-starling) x 10 seeds = 40
#   context  tags (kestrel, ocelot)                                x  3 seeds =  6
#
# Jellyfish promoted to an endpoint (gs157, 2026-08-28, pre-data): "Phoenix is the minimum" is
# the headline claim of the trajectory and is a Jellyfish -> Phoenix contrast, so it needs the
# same precision and the same allocation as the H0/H1 contrasts. Jellyfish also has no valid
# historical baseline at all (three identical seeds).
#
# Seed plan (gs157, 2026-08-27, corrected option (c)). H1 compares phoenix -> deeper-starling
# and H0 compares phoenix -> starling, so THREE tags carry the inference, not two. Those three
# get 10 seeds. This is a PRECISION increase, not a power guarantee: the only evidence about
# seed spread is one pairwise difference between two seeds, which is not a variance estimate.
# Paired uncertainty intervals get reported regardless of how many seeds are run.
#
# Why not the --array in misinfo_refusal_vs_capability.sbatch:
#   An array scatters tasks across nodes. Every inference here is a comparison ACROSS
#   revisions, so an array confounds hardware with revision -- the error that invalidated the
#   first determinism test (gl040/gl064/gl024, 2026-08-27). CLAUDE.md: any comparison between
#   runs must hold the GPU fixed.
#
# RUN ISOLATION (gs157, 2026-08-27). The previous version of this script skipped any run whose
# metrics.json existed, regardless of provenance. That would have silently pulled
# 2026-08-27-marin-misinfo-rvc-phoenix-harmbench-r1 -- written by FAILED job 16492919, on an
# unrecorded GPU, before VLLM_ENABLE_V1_MULTIPROCESSING was pinned and before provenance
# recorded hostname/gpu_uuid at all -- into the single-GPU inferential trajectory. Job 16500537
# was cancelled 3 minutes in for exactly this reason. Two defences now:
#   1. A FRESH NAMESPACE (RUN_PREFIX below) that no prior job has ever written to.
#   2. Skipping requires EXACT provenance compatibility with THIS allocation (same gpu_uuid,
#      host, multiprocessing flag, safety-eval sha, model sha, seed). Anything else is a hard
#      failure, never a silent skip and never an overwrite.
# Endpoint tags run first so that a walltime kill can only cost context tags, which are not
# required to share an allocation.
#
# Submit through the preflight wrapper, never bare sbatch:
#   cd $SCRATCH/marin-red-teaming && bash scripts/submit.sh slurm/misinfo_trajectory_seq.sbatch
#
# Watch:
#   ssh torch 'tail -f /scratch/gs157/marin-red-teaming/logs/progress.log'
#
#SBATCH --job-name=marin-misinfo-traj
#SBATCH --account=torch_pr_173_tandon_advanced
#SBATCH --partition=h200_tandon
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
# DELIBERATELY NOT AN ARRAY -- see the header. All runs share one physical GPU.
# 46 runs x ~400s ~= 5.1h on an L40S, less on an H200; 10h leaves room.
#SBATCH --time=10:00:00
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
# under us mid-study. The marin base weights are prefetched by scripts/prefetch_revisions.py.
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

# Fresh namespace. Must not collide with any earlier run family, in particular the
# `marin-misinfo-rvc` dirs left by failed jobs.
#
# BUMP THIS ON EVERY RELAUNCH. The rule that all endpoint seeds share one GPU allocation means
# a drained or preempted job CANNOT be resumed into a new allocation -- the provenance guard
# will hard-fail on the first completed run, by design. The correct recovery is a new namespace
# and a full re-run of the endpoint tags, not a resume. (Job 16500928 was killed by a gl002
# node drain at 2h20 with phoenix x10 and starling x10 already done; those runs are retained on
# disk under 2026-08-27-traj2 but are NOT the endpoint dataset, because deeper-starling never
# ran in that allocation.)
#
#   sbatch --export=ALL,MARIN_RUN_PREFIX=2026-08-28-traj3 ...
RUN_PREFIX="${MARIN_RUN_PREFIX:-2026-08-27-traj2}"

# CRITICAL: base models have no chat template. Without this scaffold the model echoes the
# prompt back and WildGuard scores the echo as compliance -- the exact confound that made the
# first base numbers invalid (docs/experiments/07-28..., report SUMMARY Part 4).
export TEMPLATE="$ROOT/config/base_template_v2.txt"
[[ -f "$TEMPLATE" ]] || log_die "base scaffold missing at $TEMPLATE"

_HUB="$HF_HOME/hub/models--marin-community--marin-8b-base"
LABEL_ROOT="${MARIN_LABELS_DIR:-${SCRATCH:-/scratch/gs157}/marin-misinfo-labels}"
PYBIN="$ROOT/.venv-safety-eval/bin/python"

# ENDPOINT tags define the three pre-registered contrasts: jellyfish -> phoenix (is Phoenix the
# minimum), phoenix -> starling (H0), phoenix -> deeper-starling (H1).
# CONTEXT tags fill in the trajectory shape and carry no threshold.
ENDPOINT_TAGS=(phoenix starling deeper-starling jellyfish)
CONTEXT_TAGS=(kestrel ocelot)
ENDPOINT_SEEDS=(0 1 2 3 4 5 6 7 8 9)
CONTEXT_SEEDS=(0 1 2)

THIS_HOST="$(hostname -s)"
THIS_GPU_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | head -1)"

log INFO "host=$THIS_HOST gpu_uuid=$THIS_GPU_UUID"
log INFO "driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
log INFO "gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | tr '\n' ' ')"
log INFO "VLLM_ENABLE_V1_MULTIPROCESSING=$VLLM_ENABLE_V1_MULTIPROCESSING"
log INFO "template=$TEMPLATE"
log INFO "run_prefix=$RUN_PREFIX (fresh namespace; prior marin-misinfo-rvc dirs are NOT reused)"
log INFO "plan: endpoints ${ENDPOINT_TAGS[*]} x ${#ENDPOINT_SEEDS[@]} seeds, context ${CONTEXT_TAGS[*]} x ${#CONTEXT_SEEDS[@]} seeds, SEQUENTIALLY on this one GPU"

# Fail before burning any GPU time if a revision is missing, rather than 4 tags in.
for TAG in "${ENDPOINT_TAGS[@]}" "${CONTEXT_TAGS[@]}"; do
    [[ -f "$_HUB/refs/$TAG" ]] || log_die "no cached revision for $TAG; run scripts/prefetch_revisions.py on the login node first"
done
log INFO "all 6 revisions present in the workspace cache"

# Resume is permitted ONLY back into the same allocation on the same physical GPU. Anything
# else -- a foreign GPU, a missing field, a different sha or seed, multiprocessing not pinned
# -- is a hard stop. Silently importing such a run is the failure this whole guard exists for.
provenance_compatible() {
    local pf="$1" seed="$2" msha="$3"
    [[ -s "$pf" ]] || return 1
    "$PYBIN" - "$pf" "$seed" "$msha" "$THIS_HOST" "$THIS_GPU_UUID" <<'PY'
import json, sys
pf, seed, msha, host, uuid = sys.argv[1:6]
try:
    p = json.load(open(pf))
except Exception:
    sys.exit(1)
# run_row.sh records socket.gethostname(), which is the FQDN on Torch (gl052.hpc.nyu.edu),
# while the job compares `hostname -s`. Normalise both to the short name or every legitimate
# same-allocation resume would hard-fail. gpu_uuid is the authoritative identity; hostname is
# a cross-check.
p["hostname"] = str(p.get("hostname", "<missing>")).split(".")[0]
need = [
        ("hostname", host.split(".")[0]),
        ("gpu_uuid", uuid),
        ("vllm_v1_multiprocessing", "0"),
        ("sampling_seed_env", str(seed)),
        ("safety_eval_sha", "060cc903d64703214c549b5c3a30ea8ceef2e588"),
    ]
for k, v in need:
    if str(p.get(k, "<missing>")) != v:
        print(f"{k}: have {p.get(k,'<missing>')!r}, need {v!r}")
        sys.exit(1)
if msha not in str(p.get("model", "")):
    print(f"model: {p.get('model')!r} does not contain {msha!r}")
    sys.exit(1)
sys.exit(0)
PY
}

run_one() {
    local TAG="$1" SEED="$2"
    local NAME="${RUN_PREFIX}-${TAG}-harmbench-s${SEED}"
    local RUNDIR="$ROOT/runs/$NAME"

    local RESOLVED_SHA MODEL_PATH
    RESOLVED_SHA="$(cat "$_HUB/refs/$TAG")"; export RESOLVED_SHA
    MODEL_PATH="$_HUB/snapshots/$RESOLVED_SHA"
    [[ -d "$MODEL_PATH" ]] || log_die "ref $TAG -> $RESOLVED_SHA but no snapshot dir at $MODEL_PATH"

    if [[ -s "$RUNDIR/metrics.json" ]]; then
        local why
        if why="$(provenance_compatible "$RUNDIR/provenance.json" "$SEED" "$RESOLVED_SHA")"; then
            log INFO "skip $NAME (already complete IN THIS ALLOCATION, provenance matches)"
            return 0
        fi
        log_die "REFUSING to reuse $NAME: metrics.json exists but provenance is incompatible with this allocation [$why]. This is the job-16492919 contamination guard. Move or delete the directory deliberately, or bump RUN_PREFIX."
    fi

    # The seed must reach vLLM's sampler. PYTHONHASHSEED does NOT do this; the patch does.
    export SAFETYEVAL_SAMPLING_SEED="$SEED"

    log_phase "$TAG s$SEED"
    log INFO "tag=$TAG seed=$SEED model=$MODEL_PATH (sha ${RESOLVED_SHA:0:12})"

    # A crashed vLLM engine previously left a task in RUNNING with no output for 14 minutes
    # (job 16488625). The heartbeat makes that state visible.
    log_heartbeat_start 120 "$RUNDIR/all.json"
    bash "$WORK/scripts/run_row.sh" \
        "$MODEL_PATH" "$TAG" harmbench:default "$NAME" "$SEED" \
        || { log_heartbeat_stop; log_die "run_row.sh failed for $NAME (see $WORK/logs/$NAME.log)"; }
    log_heartbeat_stop

    [[ -s "$RUNDIR/all.json" ]]     || log_die "no all.json produced for $NAME (per-instance labels are the point of this rerun)"
    [[ -s "$RUNDIR/metrics.json" ]] || log_die "no metrics.json produced for $NAME"

    # Copied FIRST, before any other post-processing can fail. run_row.sh refuses to re-run when
    # metrics.json exists, so a crash between metrics.json and this copy would leave the run
    # unresubmittable without hand-deleting the dir -- and the whole reason this experiment
    # exists is that the 07-28 all.json files were lost. Idempotent, so a retry is safe.
    local LABELS="$LABEL_ROOT/$NAME"
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

    "$PYBIN" - "$RUNDIR/metrics.json" "$TAG s$SEED" <<'PY' 2>&1 | while read -r l; do log RESULT "$l"; done
import json, sys
m = json.load(open(sys.argv[1]))["harmbench:default"]
misinfo = m["inverted_semantic_category_asr_lower"]["misinformation_disinformation"]
print(f"{sys.argv[2]}: misinfo ASR = {100 * (1 - misinfo):.2f}%  ({(1 - misinfo) * 54:.0f}/54)  micro = {100 * (1 - m['inverted_micro_asr_lower']):.2f}%")
PY
}

# Endpoints first: they must all share this allocation, so they must not be the ones a
# walltime kill truncates.
for TAG in "${ENDPOINT_TAGS[@]}"; do
    for SEED in "${ENDPOINT_SEEDS[@]}"; do run_one "$TAG" "$SEED"; done
done
log INFO "ENDPOINT tags complete (${ENDPOINT_TAGS[*]}) -- all ${#ENDPOINT_SEEDS[@]} seeds each, one GPU ($THIS_HOST)"

for TAG in "${CONTEXT_TAGS[@]}"; do
    for SEED in "${CONTEXT_SEEDS[@]}"; do run_one "$TAG" "$SEED"; done
done

log INFO "all 46 runs complete on ONE gpu ($THIS_HOST, $THIS_GPU_UUID)"
