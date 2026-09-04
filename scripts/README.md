# scripts/

Reproduction scripts for the Olmo 3 7B safety-number reproduction (BACKLOG Task 1).

Only scripts needed to reproduce results live here. Throwaway/temporary scripts go in
their own subdir and are not committed.

## Current scripts
- `check_project_state.py` — validates `STATUS.md` against the machine-marked active tables in
  `BACKLOG.md` and `INBOX.md`, enforces the one-task WIP limit, and checks that blocked tasks name a live
  blocker. **Updated 2026-09-04 (Gus):** a BLOCKED task may name either an INBOX ID, when a person must
  act, or one or more task IDs, when it simply waits on sibling tasks. Requiring an INBOX ID for a purely
  task-dependent blocker forced such tasks to be mislabelled READY, which is what `S1-SYNTH` was doing.
  This is stricter, not looser: referenced INBOX IDs must still be live, referenced task IDs must exist
  in the active table, and naming an already-`DONE` task as a blocker now fails as a stale state. **Note
  for editors:** any backticked task ID appearing in a BLOCKED row's Next action is read as a blocker, so
  do not mention completed tasks there — put that history in the Outcome column instead. The rule caught
  its first real stale state within the hour, when `S1-3F` closed and `S1-SYNTH` still named it.

- `compare_3f_raters.py` — S1-3F second-rater agreement (`IN-004`). Three-subtype agreement, Cohen's κ,
  the confusion matrix, per-class recall/precision, per-arm splits, and the `concessionary`/
  `misclassified` boundary count called out separately. Reports a **population-weighted** κ alongside the
  raw one: the slice is stratified equally by primary subtype, which flatters κ by ~0.10 because it
  undersamples the class where the raters disagree. Also runs the post-hoc robustness projection —
  applying the observed transition matrix to all 469 to test whether the registered verdict survives the
  second rater. It did not. It also requires the canonical living report's task pointer and update date to agree
  with `STATUS.md`. Run before commits. `submit.sh` runs it with `--require-in-progress` before any GPU
  submission, so a merely queued or stale task cannot consume compute.
- `setup_safety_eval.sh` — Gate 1: build isolated venv `.venv-safety-eval`, `pip install -e .`
  + requirements + `vllm==0.11.0`; print torch/transformers/vllm/GPU provenance to
  `logs/gate1_setup.log`. Isolated so it never touches the base env (torch 2.10 / transformers 5.0).
- `run_row.sh <model_repo> <revision> <folder:config> <run_name> [seed]` — Gates 2–5:
  run one safety-eval generation row via `evaluation/eval.py generators --use_vllm`, writing
  `runs/<run_name>/{command.txt,provenance.json,metrics.json,all.json}`. Refuses to overwrite
  an existing metrics.json. Chat template = None → model's own `apply_chat_template`
  (correct for Olmo 3 Instruct and Think). Example (Gate 2):
  `scripts/run_row.sh allenai/Olmo-3-7B-Instruct main harmbench:default 2026-07-26-instruct-harmbench-r1 0`

## Invocation reference (safety-eval @ 060cc903)
Single row: `python evaluation/eval.py generators --use_vllm --model_name_or_path <m>
--model_input_template_path_or_name None --tasks <folder>:<config> --report_output_path metrics.json
--save_individual_results_path all.json`. Task spec is `<folder>:<config_yaml>` (no `.yaml`).
Instruct rows use the plain configs (e.g. `harmbench:default`); Think rows use the
`*_wildguard_reasoning_answer` configs. Row→config map: `repro-olmo3-safety/config/rows.json`.
NOTE: eval.py has no `--revision` flag; to pin a non-main revision, pre-download that revision
into the HF cache first (or the run uses `main`). Recorded in each provenance.json.

## Planned (created as each gate is unblocked)
- `smoke_test.sh` — smallest-subset end-to-end run on a small cached model (Gate 1, after install).
- `make_delta_report.py` — join runs/*/metrics.json against targets.json → report/deltas.md (Gate 6).

## Provenance rule
Every run writes to `repro-olmo3-safety/runs/<date>-<model>-<row>/` with command.txt,
provenance.json (commits, revisions, seed, params, GPU), metrics.json, all.json.
Logs go to `logs/<jobid>_<short-name>.log`. Never overwrite prior results.

## Suite runner + base models + 32B / trajectory studies (2026-07-28/29)
- `run_suite.sh <model_repo> <revision> <label_prefix> "<folder:config> ..."` — runs a
  space-separated list of `folder:config` rows × 3 seeds (0,1,2) sequentially on one model
  via `run_row.sh`. Skips any row whose `metrics.json` already exists (safe to re-invoke).
  Reads `TEMPLATE` from the env (passed to `run_row.sh` as
  `--model_input_template_path_or_name`); unset → defaults to `hf` (the model's own chat template).
- **Base models have no chat template.** For base models export
  `TEMPLATE=repro-olmo3-safety/config/base_template_v2.txt` (the scaffold
  `User: {instruction}\n\nAssistant:`). The earlier minimal `{instruction}` template was
  confounded by prompt-echo — see `DECISIONS.md`. Instruct models: do NOT set `TEMPLATE` (use hf).
- `base_capability_wmdp.py` — logprob multiple-choice WMDP scorer (`device_map="auto"`), used for
  base-model capability across Marin pretraining revisions and the 32B tier (content-safe, counts only).
- `marin32b_remainder_scopecut.sh` — one-off launcher for the marin-32b-base base suite after the
  BBQ/Toxigen scope cut (Option 1): waits for the in-flight `bbq-r1` to finish, then runs
  `strongreject:logprobs`×3 + `wmdp:default`×3 + `toxigen:default`×1 (single Toxigen seed). Base
  scaffold template. See `docs/experiments/07-28_marin-vs-olmo-32b_base-vs-base_safety.md` (DEVIATION).
- `olmo_posttraining_studyB.sh` — Study B launcher (runs on the remote box): waits for the 32B
  toxigen r1 to free the GPU, then runs the Olmo post-training trajectory
  `allenai/Olmo-3-7B-Instruct-{SFT,DPO,Instruct}` × {`do_anything_now:default`,`harmbench:default`}
  × 3 seeds (18 rows), hf chat template. Does NOT auto-shut-down the box (shutdown is manual after
  verification). See `docs/experiments/07-28_olmo-posttraining-trajectory_framing-test.md`.
- `studyB_reseed.sh` — Study B RESEED (INBOX seed-method → b): re-runs Olmo `{SFT,DPO,Instruct}` ×
  {`do_anything_now:default`,`harmbench:default`} × 3 seeds with the fixed per-run vLLM sampling seed
  (`run_row.sh` now exports `SAFETYEVAL_SAMPLING_SEED`), so the previously byte-identical cells get valid
  3-seed CIs. Download-run-delete per checkpoint (local disk tight); writes new `-reseed` label prefixes
  so the original buggy-CI runs are preserved for before/after. Updated SUMMARY Part 8.
- `studyB_reseed_rest.sh` — remainder of the above (DPO + final only; SFT's 6 rows already completed).
  Same seed-fixed protocol.

### 32B compute topology (2026-07-28/29)
32B base-vs-base ran one model per A100 80GB (bf16 fits): `marin-32b-base` (Qwen3 arch, fp32 weights
= 122G on disk) on the LOCAL box; `Olmo-3-1125-32B` (Olmo3 arch, 61G) on a REMOTE Paperspace A100
reached via `ssh -i ~/.ssh/marin_worker paperspace@184.105.215.102`. Remote results are rsynced back
to local `repro-olmo3-safety/runs/` before the remote is shut down (fresh-instance storage is ephemeral).

## Torch port (added 2026-08-27)

- `submit.sh` — the only sanctioned way to submit a GPU job on NYU Torch. Runs
  `dry_run_check.py` and refuses to `sbatch` unless it prints `DRY RUN OK`. Enforces
  sbatch-options-before-the-file, because args after the file go to the script silently.
  Ported from `safety-decay/scripts/submit.sh`.
- `dry_run_check.py` — preflight. Checks imports, GPU visibility, the pinned safety-eval
  SHA, **that the seed patch is applied**, `OPENAI_API_KEY` (safety-eval builds a client at
  import even for local judges), the base scaffold, that no script still hardcodes
  `/home/paperspace`, `HF_HOME`, and free scratch. Extend it whenever a new failure class
  costs a GPU job.
- `../slurm/misinfo_refusal_vs_capability.sbatch` — 18-task array (6 revisions x 3 seeds)
  for `docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md`.
  Run `--array=9,10,11` (phoenix) alone first as the port gate.

### 2026-08-28 additions (trajectory study on Torch)

- `../slurm/misinfo_trajectory_seq.sbatch` — **the inferential launcher.** 46 runs sequential on
  one GPU model: jellyfish/phoenix/starling/deeper-starling x 10 seeds, kestrel/ocelot x 3.
  Provenance-gated resume (GPU model, driver, engine flags, harness sha, model sha, seed; hard
  fail on mismatch). Walltime capped 1h50 because the cluster utilization watchdog kills
  sub-50% jobs at 2h. Namespace via `MARIN_RUN_PREFIX`. Supersedes the array script above.
- `../slurm/determinism_check.sbatch`, `determinism_check_h200.sbatch`,
  `determinism_check_h200_crossgpu.sbatch` — gate check 3: seed 0 x3 + seed 1 x2 sequentially on
  one GPU (L40S, H200), and a one-run cross-card check on a second H200.
- `compare_determinism.py` — three-level comparison (exact response hash, WildGuard labels,
  54-item rate) across run dirs. Warns when runs span more than one GPU.
- `prefetch_revisions.py` — pulls the six base revisions into the workspace cache and pins their
  commits to `docs/resolved_revisions.json`; fails if two tags collapse to one commit.
- `analyze_trajectory.py` — **the analysis path.** Reads per-instance labels from the out-of-tree
  label dir, computes the pre-registered series (refusal, harmful, harmful|non-refusal, empty,
  length, non-response), the three paired contrasts with bootstrap CI + sign-flip permutation p +
  Wilcoxon, McNemar for comparability with `unstable` 5-5 splits, Holm across seven tests, flip
  lists, verdicts against the pre-registered thresholds. Aggregate counts only. Does not import
  the generation path. Run in the safety-eval venv (needs numpy/scipy):
  `python scripts/analyze_trajectory.py --labels $SCRATCH/marin-misinfo-labels --prefix 2026-08-28-traj4-h200 --out docs/results/08-27_misinfo_rvc`
- `log_lib.sh` — shared logging: `progress.log`, phases, heartbeat with GPU %, signal-aware EXIT
  trap (TERM/INT -> rc 143). The heartbeat's `gpu=0 %` lines were the utilization warning nobody read.

### 2026-08-29 additions (Stage 1 step 2/3 — rubric annotation)

- `shard_tool.py` — annotator-side helper. `dump` prints a window of items from one blinded shard
  (`--start/--count`, so a rater works in batches instead of loading 270 items at once); `check`
  validates one `sheet_part<N>.csv` against its shard using the same contract `merge_sheets.py`
  enforces at merge time. Run `check` per part so a bad sheet is caught by its author.
- `merge_sheets.py` — merges the four annotator part-sheets into one judge-style jsonl for
  `decompose_distribution.py`. Fails loudly on missing/duplicate cids, out-of-vocabulary values, or
  quality scores present when `task=no_attempt` (and absent when it is not).
- `rubric_lib.py` — shared helpers for `judge_rubric_v1` sheets: derived six categories, the
  three-way collapse, Cohen's kappa, agreement + confusion, tie-aware Spearman, sheet loading. Pure
  stdlib, so it runs outside the safety-eval venv. `compare_anchors.py` keeps its own inline copy on
  purpose — its outputs are already in the record and it is frozen. Note its Spearman used ordinal
  ranks (ties broken arbitrarily); `rubric_lib.spearman` uses average ranks, so recompute both sides
  with the same function before comparing rho values.
- `retest_agreement.py` — test-retest reliability of the blind annotator, pass 1 vs pass 2. The two
  passes sharded the same items differently, so every item common to both was labelled twice by
  independent instances. Reports per-dimension agreement/kappa, derived-six and three-way agreement,
  quality rho, **broken down by checkpoint**, plus a sign check on each pass's pooled category
  deltas (a category whose sign flips between passes is not safely measurable with this rater).
  Verified by an identity self-check: pass 1 against itself gives 1.000 on every dimension.
  `python scripts/retest_agreement.py --pass1 <dir> --pass2 <dir> --key key.json --out <file.json>`

### 2026-08-31 additions (Stage 1 step 3e — out-of-sample GPT rater check)

- `verify_gpt_rater_check.py` — independent recomputation of the 08-31 rater-check headline numbers.
  Parses the two sheets from scratch, takes kappa from sklearn's `cohen_kappa_score` instead of the
  hand-rolled estimator, and re-derives the six-category rule from the rubric rather than importing
  it. Deliberately shares no code with `compare_anchors.py` — rerunning that script would only
  reproduce its own bugs. Run in the safety-eval venv:
  `python scripts/verify_gpt_rater_check.py $LABELS/gpt_slice_v1`
- `compare_anchors.py` gained two **additive** fields/flags on 2026-08-31: `derived6.per_class`
  (n_A / n_B / n_both / F1 / both recalls per category, for the pre-registered per-class criterion)
  and `--no-write`, which reports without regenerating `spotcheck/` or overwriting
  `anchor_agreement.json`. `--no-write` exists because recomputing on `calibration_v1` would
  otherwise clobber the 25-item spot-check subset gs157 has not yet run. The freeze noted above is
  intact: rerunning it on `calibration_v1` reproduces every field of the recorded
  `anchor_agreement.json` exactly (stance 0.853/0.784, task 0.84/0.700, relevance 0.867/0.378,
  derived6 0.787/0.705, derived3 0.927, quality n=109 rho=0.561).

### 2026-08-31 · `annotate.py --max-chars`

- `annotate.py` gained `--max-chars N` (default 4000, unchanged; `0` = show the whole response). The
  `calibration_v1/spotcheck/` audit must judge the **whole** response including fabricated `User:` turns
  — that subset audits the two calibration anchors, which never got the truncation convention — and 11 of
  its 25 items run past 4000 characters, up to 10,628. Labelling those against a silently truncated
  display would have measured the display cap instead of the raters. Run that audit with
  `--max-chars 0`. Full-set passes keep the default.

### 2026-08-31 additions (Stage 1 step 3d / `S1-3D` — WildGuard versus the rubric)

- `wildguard_rubric_regression.py` — **the S1-3D analysis path.** Regresses WildGuard's binary
  `harmful` label on the four locked rubric dimensions over the existing 1,080 Phoenix/Starling
  responses. Primary metric is each dimension's *unique* out-of-fold AUC contribution under 6-fold
  cross-validation **grouped by `BehaviorID`**, so the 10 seeds and both checkpoints of one behavior
  never straddle a fold. Fold assignment is frozen: sorted BehaviorIDs, `random.Random(20260828)`
  shuffle, six contiguous blocks of nine. L2 logistic regression at `C=1.0`, chosen in advance because
  stance nearly separates the outcome. Also emits marginal AUC per dimension, full-data coefficients
  for direction only, harmful-rate cross-tabs, every standing data gate, and the pre-registered
  verdict branch. CPU only, no GPU, no Slurm. Needs numpy + scikit-learn:
  `python scripts/wildguard_rubric_regression.py --labels <dir with key.json and claude_fable_pass2.jsonl> --out docs/results/08-31_wildguard_rubric`
  Reads only `key.json` and `judge/claude_fable_pass2.jsonl`; it never opens `items.jsonl`, so no
  response text is touched. Pre-registration:
  `docs/experiments/08-31_wildguard_rubric-dimension-regression.md`.

### 2026-09-04 · `IN-002` — human spot-check audit of the Claude anchor

- `score_spotcheck_audit.py` — scores gs157's 25-item spot-check. The subset was written by
  `compare_anchors.py`, so the rival is the **GPT anchor**, not the local judges — check
  `anchor_agreement.json -> spotcheck.source` before assuming otherwise; `build_spotcheck.py` writes a
  `why.json` and `compare_anchors.py` does not, which is how to tell which produced a given directory.
  Statistic is head-to-head adjudication per dimension over that dimension's contested set (items where
  the two anchors differ): `claude` / `gpt` / `neither`. Stance primary, `no_stance`-flagged items
  excluded from it, a contested set below n=8 reported not evaluable. Local judges are a secondary
  reference. Labels only; never opens `items.jsonl`. CPU, seconds:
  `python scripts/score_spotcheck_audit.py --calib <calibration_v1 dir> --out docs/results/09-04_spotcheck_audit`
  Pre-registration: `docs/experiments/08-31_spotcheck_anchor-audit.md`.

### 2026-09-04 · `S1-STANCE-GAP` — does the restatement artefact bias the headline?

- `build_stance_gap_sample.py` — builds the blinded sample. Stratified by **arm only**; stratifying on
  any pass-2 label would bias the prevalence estimate toward whichever classes the artefact hides in,
  which is the thing being measured. Re-cids to shuffled `r####` (the run-ordered `i####` would leak the
  arm), truncates at the first fabricated `User:` turn per convention 1, and assigns shards
  **round-robin within each arm** so no shard is arm-skewed — a global round-robin over a shuffled list
  left shards ~10pp imbalanced and breached the pre-registered ±5pp gate. A seeded 10% of items is
  duplicated into a *different* shard for within-rater agreement; provenance asserts that property.
- `analyze_stance_gap.py` — the analysis path. Primary is the behaviour-paired difference in prevalence,
  because +28.5pp is itself a paired difference and an artefact common to both arms largely cancels.
  Behaviour bootstrap 95% CI, 10k, seed 20260828; differential iff the CI excludes 0 **and** |delta| ≥
  5pp. Also emits prevalence per arm, what pass-2 called the flagged items, duplicate-pair agreement, and
  a sensitivity **band** on the six category masses — a band, never a corrected point value, since a
  240-item sample cannot recompute 1,080 exact masses. Smoke-tested on synthetic random labels: null in,
  null out. Needs numpy.

### 2026-09-04 · `S1-3F` — concessionary vs unqualified endorsement

- `build_3f_sample.py` — blinded package over the 469 pass-2 `endorses` items (the universe, not a
  sample: the sub-rubric is additive and subdivides that class). Re-cids to shuffled `e####`, truncates
  at the first fabricated `User:` turn, round-robins **within arm** so shards are balanced. Note the
  balance gate measures deviation from the **universe** arm proportion (160/309 = 34.1% phoenix), not
  from 50/50 — the endorses universe is not balanced, so a 0.5 target would flag a correctly built split.
  A seeded 10% is duplicated into a different shard.
- `analyze_3f.py` — subtype mass changes with the **step-3 denominator**: all of a behaviour's
  generations, not just its endorsements, so the three subtype masses sum to the endorsement mass and are
  commensurable with −12.2 / −12.2 / +28.5pp. Behaviour bootstrap CI, sign-flip permutation p, Holm over
  three subtypes. Mass change only, never a flow. Smoke-tested on synthetic random subtypes: the three
  deltas summed to +27.60pp (the real endorsement-mass increase, confirming the denominator), split
  evenly three ways, verdict MIXED, duplicate agreement 0.277 ≈ chance. Needs numpy.

- `build_3f_second_rater.py` — the 150-item second-frontier-rater package. Stratified 75/75 by arm and
  **25 per subtype per arm**. Equal allocation is deliberate, not proportional sampling: the internal
  duplicate check produced zero `concessionary`/`misclassified` pairs, so that boundary — the one the
  preregistration names as decisive — is unmeasured, and this slice is the only instrument for it.
  Emits `upload/{items.jsonl,PROMPT.md,sheet.csv}` plus a `key.json` that is **never uploaded**.

**Rater-dispatch rule, learned 2026-09-04.** Give every concurrent rater a **private** working directory.
Two S1-3F raters each wrote a helper script to the same shared scratchpad path and one executed the
other's version pointed at a different shard. Both caught it by cid discontinuity and re-ran, and the
per-shard provenance gate confirmed 0 rows misattributed — but that gate is the only thing that catches
this class, because a foreign cid is still a valid key entry and passes an ordinary missing/unexpected
check.
