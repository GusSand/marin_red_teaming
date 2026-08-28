#!/usr/bin/env bash
# Shared logging for every script in this repo. Source it, do not execute it.
#
#   source "$(dirname "${BASH_SOURCE[0]}")/log_lib.sh"
#   log_init "phoenix-r1"        # names this stream
#   log INFO "starting generation"
#   log_phase "generation"       # marks a phase boundary, times the previous one
#   log_die "model download failed"
#
# Every line goes to stdout AND appends to $MARIN_ROOT/logs/progress.log, which is the
# one file to tail to see what the whole project is doing:
#
#   ssh torch 'tail -f /scratch/gs157/marin-red-teaming/logs/progress.log'
#
# Format: 2026-08-27T19:15:02-04:00 | 16488625_9 | phoenix-r1 | INFO  | +00:04:11 | message
# The +HH:MM:SS column is elapsed since log_init, so a stalled job is obvious at a glance.

MARIN_ROOT="${MARIN_RT_ROOT:-${SCRATCH:-/scratch/gs157}/marin-red-teaming}"
LOG_PROGRESS="${LOG_PROGRESS:-$MARIN_ROOT/logs/progress.log}"
_LOG_STREAM="${_LOG_STREAM:-$(basename "${0:-shell}" .sh)}"
_LOG_T0=$(date +%s)
_LOG_PHASE=""
_LOG_PHASE_T0=$_LOG_T0

log_init() {
    _LOG_STREAM="${1:-$_LOG_STREAM}"
    _LOG_T0=$(date +%s); _LOG_PHASE_T0=$_LOG_T0
    mkdir -p "$(dirname "$LOG_PROGRESS")"
    log INFO "=== start (host=$(hostname -s) pid=$$) ==="
}

_log_elapsed() {
    local d=$(( $(date +%s) - _LOG_T0 ))
    printf '+%02d:%02d:%02d' $((d/3600)) $((d%3600/60)) $((d%60))
}

log() {
    local level="$1"; shift
    local jid="${SLURM_JOB_ID:-local}"
    [[ -n "${SLURM_ARRAY_JOB_ID:-}" ]] && jid="${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
    local line
    line="$(date -Is) | ${jid} | ${_LOG_STREAM} | $(printf '%-5s' "$level") | $(_log_elapsed) | $*"
    echo "$line"
    # Never let a logging failure kill a job.
    mkdir -p "$(dirname "$LOG_PROGRESS")" 2>/dev/null || true
    echo "$line" >> "$LOG_PROGRESS" 2>/dev/null || true
}

# Close the previous phase with its duration, then open a new one.
log_phase() {
    local now; now=$(date +%s)
    if [[ -n "$_LOG_PHASE" ]]; then
        log INFO "phase done: $_LOG_PHASE ($((now - _LOG_PHASE_T0))s)"
    fi
    _LOG_PHASE="$1"; _LOG_PHASE_T0=$now
    log INFO "phase start: $_LOG_PHASE"
}

log_die() { log FATAL "$*"; exit 1; }

# Log the exit status of the script whatever happens. Call once, after log_init.
# This is what makes a crashed or cancelled job visible in progress.log instead of
# just vanishing from squeue.
# A job killed by SIGTERM (node drain, preemption, scancel) previously logged "end OK", because
# the signal killed the child and the trap ran with $?=0. Job 16500928 was drained off gl002 and
# its log claimed success. Catch the signals explicitly so the log never disagrees with sacct.
log_trap_exit() {
    trap '_LOG_SIGNALLED=1' TERM INT
    trap '_rc=$?;
          if [[ -n "${_LOG_SIGNALLED:-}" && $_rc -eq 0 ]]; then _rc=143; fi;
          if [[ -n "${_LOG_HB_PID:-}" ]]; then kill "$_LOG_HB_PID" 2>/dev/null || true; fi;
          if [[ -n "$_LOG_PHASE" ]]; then log INFO "phase done: $_LOG_PHASE ($(( $(date +%s) - _LOG_PHASE_T0 ))s)"; fi;
          if [[ $_rc -eq 0 ]]; then log INFO  "=== end OK (total $(_log_elapsed)) ===";
          else                       log ERROR "=== end FAILED rc=$_rc (total $(_log_elapsed)) ==="; fi;
          exit $_rc' EXIT
}

# Background heartbeat: proves the job is alive and shows what it is producing.
# A vLLM engine crash previously left array tasks in RUNNING for 14 minutes with no
# output at all (job 16488625); a heartbeat makes that visible in one tail.
#   log_heartbeat_start <interval_seconds> [file_to_watch]
log_heartbeat_start() {
    local interval="${1:-120}" watch="${2:-}"
    (
        while true; do
            sleep "$interval"
            local extra=""
            if command -v nvidia-smi >/dev/null 2>&1; then
                extra="gpu=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader | tr '\n' ';')"
            fi
            if [[ -n "$watch" && -f "$watch" ]]; then
                extra="$extra out=$(du -h "$watch" 2>/dev/null | cut -f1)"
            elif [[ -n "$watch" ]]; then
                extra="$extra out=absent"
            fi
            log HB "alive $extra"
        done
    ) &
    _LOG_HB_PID=$!
    log INFO "heartbeat every ${interval}s (pid $_LOG_HB_PID)"
}

log_heartbeat_stop() {
    [[ -n "${_LOG_HB_PID:-}" ]] && kill "$_LOG_HB_PID" 2>/dev/null || true
}
