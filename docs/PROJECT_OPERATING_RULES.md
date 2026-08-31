# Project operating rules

These rules turn the research logs into an executable project without weakening the existing research-integrity rules.

## State hierarchy

Read in this order at the start of every session:

1. `STATUS.md` — current phase, current task, blockers, and exit criteria. Authoritative.
2. Active table at the top of `BACKLOG.md` — ordered work, owner, next action, and evidence.
3. Active table at the top of `INBOX.md` — requests requiring Gus or another named person.
4. The current experiment specification and relevant decision-log entries.
5. Historical backlog, inbox, and research journal only when provenance or context is needed.

If these disagree, stop normal work and repair the state files before starting or submitting an experiment.

## Work-in-progress limit

- At most one active-table task may be `IN_PROGRESS`.
- A task must be `READY` before it becomes `IN_PROGRESS`.
- `BLOCKED` requires a named owner, an exact unblock condition, and an INBOX ID when a person must act.
- `PARKED` work cannot be started because compute is free or another task is inconvenient.
- Sidecars and robustness checks do not block the critical path unless `STATUS.md` explicitly makes them gates.

## Task contract

Every active task has:

- a stable ID;
- one outcome, phrased as a result rather than an activity;
- one owner;
- one next action;
- an evidence or specification path;
- one status from `READY`, `IN_PROGRESS`, `BLOCKED`, `PARKED`, or `DONE`.

Do not use percentages such as “80% done.” A task is done only when its evidence and required verification exist.

## Starting work

Before a task becomes `IN_PROGRESS`:

1. Confirm it is the current task in `STATUS.md`.
2. Confirm its prerequisites and unblock conditions.
3. For a new result, create or update the experiment file before viewing new outcome data.
4. Freeze success criteria, analysis, exclusions, and decision consequences.
5. Commit the clean pre-run state and record its SHA when compute will be used.

The `READY` to `IN_PROGRESS` change, the frozen experiment file, and the matching `STATUS.md` update form one
start transaction. Do not inspect new outcome data between freezing the plan and committing that transaction.

## Closing work

A result-producing task becomes `DONE` only when the same change set contains:

1. raw-result or aggregate evidence at a durable path;
2. independent verification, or an explicit `UNVERIFIED` label approved through INBOX;
3. a research-journal entry;
4. a decision-log entry when a choice was settled;
5. updated active backlog and `STATUS.md` pointers;
6. a descriptive commit.

Update the state last, after the evidence exists. Never mark done because a job finished successfully.

The evidence, verification status, journal and decision updates, task closure, and next-task promotion form one
close transaction. A null result or failed hypothesis closes in exactly the same way as a positive result.

## Inbox discipline

- The active table contains only requests that need a named person.
- Each request states what decision or artifact is needed and which task it blocks.
- Results, FYIs, corrections, and job logs do not belong in the active table.
- When resolved, remove the row from the active table in the same commit that applies the answer. Preserve the detailed correspondence below the historical marker.
- Optional credentials must be marked non-gating.

## Status-update discipline

- `STATUS.md` is short enough to read in under two minutes.
- Update it whenever the current task, phase, blocker, or accepted finding changes.
- Do not create new `RESUME HERE` entries in the research journal. Session handoffs belong in `STATUS.md`.
- Do not copy full results into `STATUS.md`; state the verdict and link the evidence.
- Run `python3 scripts/check_project_state.py` before committing and before submitting a GPU job.
- GPU submission additionally requires the current task to be `IN_PROGRESS`; `submit.sh` enforces this.
- A status page older than seven days blocks work until it is reconciled.

## Enforcement layers

1. `CLAUDE.md` tells every research agent which transitions and bypasses are forbidden.
2. `.githooks/pre-commit` rejects commits whose active project state is inconsistent.
3. `scripts/submit.sh` rejects GPU submissions unless the state is consistent and the current task is
   `IN_PROGRESS`.
4. Pre-registration and an independent verification path protect the scientific claim. These require judgment
   and cannot be reduced to a file-consistency check.

This clone uses `git config core.hooksPath .githooks`. New clones must set the same repository-local option.
Never use `--no-verify`, disable the hook, submit around the wrapper, or weaken a check to pass work that should
be repaired or blocked.

## Weekly pruning

At least once every seven days with project activity:

- reconcile the active queue with `STATUS.md`;
- close or park stale tasks;
- ensure every blocker has an owner;
- confirm the current task is still the shortest path to the phase exit criteria;
- move no historical evidence and rewrite no past result.
