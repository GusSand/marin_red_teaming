# CLAUDE.md — 

<!-- Fill in the one-liner: what this project studies and the primary model(s). -->
**Project:** WE are doing some Red Teaming on open models. 

Primary model: `marin-community/marin-8b-base` 
Repo branch: 

This file is the entry point. Detailed docs live in `docs/`. Keep this file short.

---

## How you work (autonomy model)

You run mostly unattended, including overnight, on my remote GPU and the rule is simple:

- **Work freely on anything unblocked.** Don't ask permission for normal research work (editing code, writing configs, launching jobs, reading logs, analyzing results, committing and pushing to `main`).
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

## How to write (Gus, 2026-08-28)

Attention-friendly prose, everywhere: chat, journal, reports, INBOX, commit messages.

- **Short sentences. One idea each.** If a sentence has two clauses joined by "which" or "and", split it.
- **Lead with the number or the verdict**, then the reason. Not the reverse.
- **No restating context the reader already has.** A subtitle is one line. A caption is one sentence.
- **Cut qualifiers that don't change the decision.** "In absolute value", "specifically", "it is worth noting" go.
- **Bold the load-bearing phrase, not the whole sentence.**
- **Tables over paragraphs** when there are three or more parallel items.
- **Say what was done, not how hard it was.**

Test: could a skilled colleague read it once, fast, and know what to do? If they have to reread, it is too long.

Reports follow the Open Athena review template (see `docs/reports/`): masthead, title, one-line deck, motivation with fact tiles, setup, claims with `RESULT:` lines, figures, recommendations, Q&A, reference grid. Reports live in `docs/reports/` beside the commit that produced the numbers. The wiki gets a pointer, never a copy.

---

## Research integrity (non-negotiable — matters MORE because I'm not watching)

1. **Iron Law:** perfect or suspiciously clean results = a bug, not a breakthrough. Flag it as a likely bug and stop; do not celebrate. Again 0% or 100% in ML is not believable!!!
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
- Delete checkpoints, datasets, or logs. Change access/sharing.
- Anything under "Research integrity" above.

**Log discipline (so I can reconstruct the night):**
- Every job writes to a known path: `logs/<jobid>_<short-name>.log`.
- Every job gets one line in the journal: jobid, config file, partition, status, key metric or error.
- Compute: **NYU Torch** as of 2026-08-27. See the Compute section below. The old
  paperspace A100 80GB is gone; anything that still hardcodes `/home/paperspace` is broken.

---

## Compute — NYU Torch (added 2026-08-27)

Cluster access, SSH and etiquette: @~/github/hpc/CLAUDE.md. Read it before touching
anything remote. Short version: SSH keys do not work on Torch, auth is a Duo device-code
flow only Gus can complete, and you ride his warm shared connection. Check it with
`ssh -o BatchMode=yes -o ConnectTimeout=6 torch true` before any remote work, and if that
fails, ask rather than retrying.

**Slurm: Tandon first, always.** Account `torch_pr_173_tandon_advanced` (fairshare 1.0),
verified 2026-08-27 against `sacctmgr show assoc user=gs157`, which lists exactly
`torch_pr_173_tandon_advanced`, `torch_pr_173_general` and `users`. Note `gs157` is the
**login user**, not a Slurm account; do not pass it to `--account`.
For this project's 8B generation plus a 7B judge, `partition=l40s_public` (48GB L40S; plain
`l40s` is invalid for this account, and no `l40s_tandon` exists, so L40S runs use the public
partition with the tandon account). If vLLM OOMs, or for anything at 32B, move to
**`h200_tandon`** first, which is the 112-GPU group pool, rather than `h200_public`, which is
a 24-GPU pool shared by every public user. `torch_pr_173_general` and public-pool partitions
are fallbacks when tandon stalls, not defaults. QoS=normal, walltime cap 48h.

**GPU-hours need no approval, any size.** Still log the estimate in the experiment file
before submitting.

**Remote workspace**: `/scratch/gs157/marin-red-teaming` (created 2026-08-27), with the venv at
`repro-olmo3-safety/.venv-safety-eval/`, the HF cache at `hf_cache/`, the vendored safety-eval
checkout at `repro-olmo3-safety/safety-eval/`, run artifacts at `runs/`, and job logs at `logs/`.
(Corrected 2026-08-31: this line said `env/` and `safety-eval/`; neither path exists. Use
`repro-olmo3-safety/.venv-safety-eval/bin/python`, which is what the sbatch files already use.) Per-instance labels go to the sibling
`/scratch/gs157/marin-misinfo-labels/`, deliberately outside the repo tree.

Scratch quota is **5TB, 18% used**, and it is **not backed up and is flushed**. Anything that
must survive belongs in the repo or `$ARCHIVE`. `$HOME` is only 50GB, which is why `HF_HOME`
must point into scratch; the preflight fails if it is unset.

### Login-node /tmp (learned 2026-08-29)

`/tmp` on the Torch login nodes is a **2 GB shared tmpfs** and fills up. Symptom: VS Code Remote-SSH
(and anything using `mktemp`) fails with "no space left" while quotas look fine. `~/.bashrc` and
`~/.bash_profile` on Torch now export `TMPDIR=/scratch/gs157/tmp`; keep it that way.

### Preflight rule

Submit GPU jobs only via `bash scripts/submit.sh slurm/<file>.sbatch`. It runs
`scripts/dry_run_check.py` and refuses to sbatch unless that prints `DRY RUN OK`. A minute of
CPU beats a queue wait plus a dead GPU job. Extend the check whenever a new failure class
appears; the ones it already covers are the ones that have actually bitten this project.

### Commit cadence (Gus, 2026-08-27)

**Commit before starting any new experiment**, and often in general. A commit is the boundary
that makes a result attributable to a known state of the code: if the tree moved between a run
and its analysis, provenance files point at code that no longer exists.

- Commit and push straight to `main` (Gus, 2026-08-27). Two people on this repo, no PR flow.
- The natural commit points are: before submitting a job, after a gate check resolves, and after
  correcting a claim in the journal.
- Record the commit SHA in the experiment doc when a run's numbers are the ones being kept.

### Comparing runs: pin the hardware (added 2026-08-27, learned the hard way)

**Any comparison between runs must hold the GPU fixed.** vLLM only claims reproducibility on
identical hardware and version. A Slurm *array* scatters tasks across nodes, so an array is the
wrong tool for a reproducibility or determinism test: use one job that loops sequentially on one
allocated GPU.

This is not hypothetical. On 2026-08-27 a determinism check ran as a 3-task array, landed on
gl040 / gl064 / gl024, and "failed". The failure was the test design, not the harness.

Rules that follow:
- **Determinism, seed and reproducibility tests: one job, one GPU, sequential runs.** Never an array.
- **Provenance must record hostname, GPU UUID, driver version, engine flags and the seed env var.**
  A reproducibility claim that cannot name the GPU it ran on is not checkable. `run_row.sh` does
  this now.
- **Set `VLLM_ENABLE_V1_MULTIPROCESSING=0`** for any run whose reproducibility matters; it is
  vLLM's documented first step for reproducible offline V1 inference.
- **Trajectory/production runs may still use arrays** (different checkpoints are meant to differ),
  but any *same-configuration* comparison drawn from them is confounded by hardware and must say so.
- **Convert percentage-point differences to item counts before calling anything an effect.** On the
  54-item misinformation subset one item is 1.85pp, so "3.7pp" is two classifications.
- **Token-exact equality is the harshest test and the least informative alone.** Always compare
  labels and the reported rate alongside it.

### Never-dos on Torch

- No compute on login nodes. sbatch only, and never interactive `srun`: it blocks and hangs you.
- Never edit files directly on Torch. **This repo is the source of truth**; rsync up.
- Do not attempt ssh auth yourself. The Duo flow is Gus-only.
- Large transfers go through `torch-dtn`, not the login node.

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

- Commit completed work to `main` with a descriptive message and push it (Gus, 2026-08-27: two-person project, no PR flow needed; supersedes the earlier working-branch rule).
- `.gitignore` large artifacts (checkpoints, logs, model weights); keep `docs/`, `BACKLOG.md`, `INBOX.md`, journal checked in — that's the project memory.
- **Treat `research_journal.md`, `BACKLOG.md`, and `INBOX.md` as append-only.** Don't rewrite or overwrite them wholesale. If a subagent or tool touches them, that edit must be a clean git diff I can revert. A bad autonomous run must always be recoverable.