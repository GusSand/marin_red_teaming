#!/usr/bin/env bash
# Push this repo to the Torch workspace. THE ONLY SANCTIONED WAY TO SYNC.
#
# WHY THIS FILE EXISTS (incident 2026-09-08, ~23:43 EDT). An ad-hoc
#   rsync -az --delete --exclude '.git' --exclude 'logs' --exclude '.venv*' ./ torch:$WORK/
# destroyed every workspace directory that is not in the repo, because --delete removes
# everything at the destination that the source does not have, and the whole point of the
# workspace is that it holds large artifacts the repo deliberately does not track:
#   - hf_cache/hub/          ~100GB of model weights, including the GATED WildGuard judge
#   - pythons/               the standalone CPython the venv's bin/python symlinks to
#   - repro-olmo3-safety/safety-eval/   the vendored checkout (its .git survived; the tree did not)
#   - runs/twins_v2/         raw generations for a closed experiment
# The venv survived only because of an unrelated exclude, and it was still broken, because its
# interpreter lived in the deleted pythons/.
#
# RULE: never pass --delete to a workspace sync. Stale remote files are harmless; deleted
# weights are hours of download and, for a gated repo, a hard block on a human.
set -euo pipefail

REMOTE="${MARIN_RT_REMOTE:-torch}"
WORK="${MARIN_RT_ROOT:-/scratch/gs157/marin-red-teaming}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for arg in "$@"; do
    case "$arg" in
        --delete|--delete-*|--force-delete)
            echo "REFUSING: $arg is never valid for a workspace sync. See the header of $0." >&2
            exit 2
            ;;
    esac
done

cd "$HERE"
echo "sync $HERE -> $REMOTE:$WORK (no --delete)"
rsync -az --no-perms --omit-dir-times \
    --exclude '.git/' \
    --exclude '.DS_Store' \
    --exclude 'logs/' \
    --exclude '.venv*' \
    --exclude 'hf_cache/' \
    --exclude 'pythons/' \
    --exclude 'runs/' \
    --exclude 'repro-olmo3-safety/safety-eval/' \
    --exclude 'repro-olmo3-safety/runs/' \
    --exclude 'outputs/' \
    "$@" \
    ./ "$REMOTE:$WORK/"
echo "sync OK"
