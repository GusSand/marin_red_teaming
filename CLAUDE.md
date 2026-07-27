# CLAUDE.md — 

<!-- Fill in the one-liner: what this project studies and the primary model(s). -->
**Project:** WE are doing some Red Teaming on open models. 

Primary model: `marin-community/marin-8b-base` 
Repo branch: 

This file is the entry point. Detailed docs live in `docs/`. Keep this file short.

---

## How you work (autonomy model)

You run mostly unattended, including overnight, on my local GPU and the NYU Slurm cluster. The rule is simple:

- **Work freely on anything unblocked.** Don't ask permission for normal research work (editing code, writing configs, launching jobs, reading logs, analyzing results, committing to the working branch).
- **Queue anything you can't or shouldn't do yourself** as a line in `INBOX.md`, then keep going on the next unblocked task. **Never idle waiting on me.**
- When I answer an `INBOX.md` item, unblock whatever depended on it and continue.
- write scripts in the scritps dir. 
- If you need some temporary scripts create a specific dir and move things there as well. 
- I only need in scripts the ones we would use to repro. 
- Make sure you document all the appropiate scripts in a readme.md inside scripts.

Two plain-text files hold the state — no ID scheme, no ceremony:

- `BACKLOG.md` — your queue. Checklist of tasks, top = next. You add/reorder/close items freely.
- `INBOX.md` — my queue. Things needing me: a decision, a credential, an interactive job, a review. One line each, newest on top. Append `→ answer:` inline when I reply.

If 3+ INBOX items sit unanswered, put a one-line `STALE — please triage` note at the top so I see it.

---

## Research integrity (non-negotiable — matters MORE because I'm not watching)

1. **Iron Law:** perfect or suspiciously clean results = a bug, not a breakthrough. Flag it as a likely bug and stop; do not celebrate.
2. **Never fabricate or simulate data or results.** If any number is from a mock, stub, dry-run, or placeholder, say so loudly at the top of the report.
3. **Never silently change the experiment** — not because it's slow, not because you think it's wrong. If you believe it's wrong, write an INBOX item and pick up other work. Don't touch the design.
4. **Reuse before you write.** Search the repo for existing code/data first. Don't duplicate.

---

## Verification (the doer never signs off on its own work)

One persona used to check the other's work. Keep that check — separate the *doing* from the *checking* by context, not by session role.

- **Pre-register success criteria before a run, not after.** Write what counts as success in the experiment file *before* launching. Results can't move the goalposts afterward.
- **Before any result is logged as a finding, reproduce it from raw data.** Spawn a fresh subagent given only the raw data / checkpoint + the pre-registered criteria — *not* your reasoning or your result scripts. It re-runs the eval end-to-end itself (reload checkpoint, rerun the eval/analysis pipeline, recompute the metric) and compares its number to your claimed number. Match within tolerance → log it. Mismatch, can't reproduce, or a standing gate fails → INBOX item, and it does **not** enter the journal as a finding.
  - **Independent path:** rerunning your exact script just reproduces your exact bug. Re-derive from raw data / a fresh code path where possible; at minimum recompute the headline metric a second, independent way.
  - **Determinism:** diffusion sampling is stochastic — fix and record seeds, and compare within a stated tolerance / CI, not exact equality. Write the tolerance in the experiment file *before* the run.
  - **Cost gate:** reproduction reruns *eval only*, never retraining. If verifying would need more than a short batch job (retrain, big sweep), don't — escalate to INBOX and log the result as **UNVERIFIED** until I clear it.
- **Standing data gates** (the checker applies these every time):
  - Enough data? How many items — actually enough to support the claim?
  - Duplicates / leakage? No overlap between train and test.
  - Labels correct? All true are true, all false are false, none both.
  - Split? ~20% held-out test, or k-fold. Never trained on eval data.

Limitation: a subagent shares some of your blind spots, so this is weaker than a truly independent reviewer. Its job is to decide what's solid enough to auto-log vs. what gets escalated to me — I'm still the final check on flagged items.

---

## Compute boundary — local GPU (Slurm deferred)

**Slurm is not in use for now (2026-07-07).** All compute runs on the local GPU:
one **NVIDIA A100 80GB**. Run training/inference as background processes
(`nohup python … > logs/… 2>&1 &`), poll with `ps`/log tails, never inline in the
session. Re-enable the Slurm workflow below if/when we move to the cluster.

Model training and inference run on the GPU, not inline in your session.

**You may do yourself:**
- Edit code, write/modify run scripts.
- Launch background jobs on the local A100, poll status (`ps`, `nvidia-smi`), read
  job logs, summarize outcomes. (Slurm `sbatch`/`squeue`/`sacct` — deferred.)
- Run small, fast local checks (data shape, tokenizer sanity, a few-step smoke test) that finish in seconds.

**Never do unattended:**
- Interactive `srun` / anything that blocks waiting on a terminal — it hangs you. Batch only.
- Delete checkpoints, datasets, or logs. Push to `main`. Change access/sharing.
- Anything under "Research integrity" above.

**Log discipline (so I can reconstruct the night):**
- Every job writes to a known path: `logs/<jobid>_<short-name>.log`.
- Every job gets one line in the journal: jobid, config file, partition, status, key metric or error.
- Compute: **local A100 80GB**, background processes. Slurm partition/account/QoS/
  walltime — N/A for now (Slurm deferred; fill in if we move to the NYU cluster).

---

## Logging & journal

- `docs/research_journal.md` — append-only, one entry per experiment. TLDR level, enough for a teammate to understand what we did:
  - Research question · Method (model, dataset, inputs) · Results (no interpretation) · Interpretation (only if flagged clearly as yours).
- `docs/experiments/MM-DD_<model>_<dataset>_<experiment>.md` — **one file per experiment, created before the run, not after.** At plan time it holds the research question / hypothesis, setup (model, dataset, inputs), and success criteria + tolerance — these *are* the pre-registered criteria the verifier checks against. After the run, fill in results (no interp), verified/unverified, learnings, and links to the scripts. A scoping question like "which model?" or "which dataset?" is its own **selection experiment** (e.g. `07-01_diffusion_model-selection.md`): candidates = the hypotheses, the small runs = the setup, the chosen one + why = the result.
- `docs/decisions.md` — append-only, one line per settled choice (`2026-07-01 · picked model Y over X/Z → experiments/07-01_diffusion_model-selection.md`). **Write a line the moment a selection experiment reaches a verdict** (dataset/model/method chosen) — not while still exploring. Never rewrite past lines. Look here before re-opening a decision.
- If you create a dataset, add it to `docs/DATA_INVENTORY.md` with how to recreate it, size, and which experiment used it.

---

## Research & lit review

When a task needs prior-work or novelty checking — does this exist, who's done it, is my angle actually new — do a real source-grounded pass, not a guess from memory.

- **Tool:** `paperclip` (local CLI) for lit review.
  <!-- Fill in the exact invocation once, so you don't reason it out each time: -->
  - Invocation: `TODO` (e.g. `paperclip <subcommand> "query"`)
- **Output goes to `outputs/`, never into the memory files.** Anything citable → `refs.bib` (or the relevant experiment file). Findings are reference material, not project state.
- **Isolation (non-negotiable):** run `paperclip` — or any external research agent — from a throwaway working dir with no write access to the repo root. It must never be able to touch `BACKLOG.md`, `INBOX.md`, or the journal. If a research run and the memory files ever end up in the same writable space, that's the bug that lets a hallucinating subagent overwrite your state.

---

## Git & memory safety

- Commit completed work to the working branch with a descriptive message. Don't push to `main`.
- `.gitignore` large artifacts (checkpoints, logs, model weights); keep `docs/`, `BACKLOG.md`, `INBOX.md`, journal checked in — that's the project memory.
- **Treat `research_journal.md`, `BACKLOG.md`, and `INBOX.md` as append-only.** Don't rewrite or overwrite them wholesale. If a subagent or tool touches them, that edit must be a clean git diff I can revert. A bad autonomous run must always be recoverable.