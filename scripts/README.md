# scripts/

Reproduction scripts for the Olmo 3 7B safety-number reproduction (BACKLOG Task 1).

Only scripts needed to reproduce results live here. Throwaway/temporary scripts go in
their own subdir and are not committed.

## Current scripts
- `check_project_state.py` — validates `STATUS.md` against the machine-marked active tables in
  `BACKLOG.md` and `INBOX.md`, enforces the one-task WIP limit, and checks that blocked tasks name
  live INBOX IDs. It also requires the canonical living report's task pointer and update date to agree
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
