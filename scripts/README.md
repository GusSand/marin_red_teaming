# scripts/

Reproduction scripts for this project. Two eras live here: the Olmo 3 7B safety-number reproduction
(BACKLOG Task 1, July) and the Phoenix→Starling red-teaming program (Stage 1, from 2026-08-27).

Only scripts needed to reproduce results live here. Throwaway/temporary scripts go in
their own subdir and are not committed.

**Two ways to read this file.** [Index](#index--every-script-one-line) lists every script in one line
each, grouped by what it does — start there to find something. The dated sections below it are the
narrative record: what each experiment ran, in the order it ran, with the reasoning that shaped the code.
Every script appears in the index; only scripts tied to a Stage 1 experiment get a dated section.

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
  It also requires the canonical living report's task pointer and update date to agree with `STATUS.md`.
  Run before commits. `submit.sh` runs it with `--require-in-progress` before any GPU submission, so a
  merely queued or stale task cannot consume compute.

- `compare_3f_raters.py` — S1-3F second-rater agreement (`IN-004`). Three-subtype agreement, Cohen's κ,
  the confusion matrix, per-class recall/precision, per-arm splits, and the `concessionary`/
  `misclassified` boundary count called out separately. Reports a **population-weighted** κ alongside the
  raw one: the slice is stratified equally by primary subtype, which flatters κ by ~0.10 because it
  undersamples the class where the raters disagree. Also runs the post-hoc robustness projection —
  applying the observed transition matrix to all 469 to test whether the registered verdict survives the
  second rater. It did not.
- `setup_safety_eval.sh` — Gate 1: build isolated venv `.venv-safety-eval`, `pip install -e .`
  + requirements + `vllm==0.11.0`; print torch/transformers/vllm/GPU provenance to
  `logs/gate1_setup.log`. Isolated so it never touches the base env (torch 2.10 / transformers 5.0).
- `run_row.sh <model_repo> <revision> <folder:config> <run_name> [seed]` — Gates 2–5:
  run one safety-eval generation row via `evaluation/eval.py generators --use_vllm`, writing
  `runs/<run_name>/{command.txt,provenance.json,metrics.json,all.json}`. Refuses to overwrite
  an existing metrics.json. Chat template = None → model's own `apply_chat_template`
  (correct for Olmo 3 Instruct and Think). Example (Gate 2):
  `scripts/run_row.sh allenai/Olmo-3-7B-Instruct main harmbench:default 2026-07-26-instruct-harmbench-r1 0`

## Index — every script, one line

Dated sections below carry the reasoning; this table is the lookup. `†` marks a script with no dated
section, either because it predates the Stage 1 program or because it is infrastructure rather than an
experiment step.

### Project control
| Script | What it does |
|---|---|
| `check_project_state.py` | Validates `STATUS.md` against the active tables, enforces the WIP limit, checks blockers, living-report freshness and mind-map freshness. The pre-commit hook and `submit.sh` both run it. |
| `make_mindmap.py` | Renders `docs/mindmap.svg` from its `BRANCHES` table — one branch per sub-question, colored answered / partial / open, first leaf the current answer. `--check` re-renders and exits 1 if the file on disk is stale, which is what the state checker calls. Only verified results become leaves. |
| `submit.sh` | The only sanctioned GPU submission path. Runs `dry_run_check.py` and refuses to `sbatch` without `DRY RUN OK`. |
| `dry_run_check.py` | Preflight: env, paths, cached weights, judge presence, seed patch. A CPU minute against a dead GPU job. |
| `sync_to_torch.sh` † | The only sanctioned way to push this repo to the Torch workspace. **Refuses `--delete`** — added after the 2026-09-08 incident destroyed 270GB of untracked workspace state. |
| `check_tag_drift.py` † | Compares the HF cache's resolved tag SHAs against `docs/resolved_revisions_reconstructed.json`. A moved tag fails the run. The `OPS-001` guard. |
| `log_lib.sh` † | Shared logging, sourced by every shell script here. Do not execute it. |

### Generation and evaluation harness
| Script | What it does |
|---|---|
| `setup_safety_eval.sh` | Gate 1: build the isolated `.venv-safety-eval`, pin vllm 0.11.0, print provenance. |
| `run_row.sh` | Run one safety-eval generation row, writing `command.txt`, `provenance.json`, `metrics.json`, `all.json`. Refuses to overwrite. |
| `run_suite.sh` † | Generic suite runner: a list of `folder:config` rows × 3 seeds on one model, sequential on one GPU. |
| `smoke_test.sh` † | Smallest-subset end-to-end run on a small cached model. |
| `prefetch_revisions.py` † | Download and verify pinned model revisions into the HF cache before a run. |
| `prefetch_cooldown_revisions.py` | `S1-CKPT`: download the three pinned cooldown revisions and verify every shard. |
| `judge_check.py` † | Gate 1 judge sanity check: does WildGuard load and label two hand-made pairs correctly? |
| `rejudge_missing.py` † | Label completion, not a rerun: re-judge non-empty responses WildGuard left unlabelled, identical pinned judge. |
| `check_seed_divergence.py` † | Gate check: prove the sampler seed is actually in force on Torch. |
| `compare_determinism.py` † | Compare determinism runs at three levels, because token-exact equality alone misleads. |

### Rubric annotation pipeline
| Script | What it does |
|---|---|
| `export_items.py` † | Export all non-empty misinfo responses for a set of runs as blinded judge items plus a key. Builds `full_phoenix_starling_v1`. |
| `shard_tool.py` † | Annotator-side helper: dump one blinded shard for rating, then check the returned sheet. |
| `annotate.py` † | Resumable keystroke annotator for the calibration set under `config/judge_rubric_v1`. |
| `merge_sheets.py` † | Merge the four annotator part-sheets into one judge-style jsonl. Validates before merging; fails loudly rather than dropping rows. |
| `judge_dimensions.py` | Run a local judge on blinded items with the locked rubric. **Validates every emitted label against the locked vocabulary and fails above a 1% rate** (added by `S1-JUDGE-VOCAB`). |
| `rubric_lib.py` † | The six-category derivation and shared rubric helpers, extracted 2026-08-29 so later analyses do not re-implement them. |
| `audit_label_vocabulary.py` | `S1-JUDGE-VOCAB`: count label values outside the locked vocabulary. Discovers its scope from the data root, never a typed list. |
| `retest_agreement.py` † | Test-retest reliability of the blind rubric annotator, pass 1 versus pass 2. |
| `compare_anchors.py` † | Inter-rater agreement between two anchor sheets, per dimension and on the derived six categories. |
| `compare_judges.py` † | Judge selection against the human calibration sheet, against the pre-registered macro-F1 and recall bars. |

### Dataset builders
Each writes into `/scratch/gs157/marin-misinfo-labels/`. Recreate commands and hashes:
`docs/DATA_INVENTORY.md`.

| Script | Builds |
|---|---|
| `build_calibration_set.py` | `calibration_v1` — the 150-response blinded human calibration set. |
| `build_spotcheck.py` † | `calibration_v1/spotcheck/` — items where the anchor disagrees with both local judges. |
| `build_gpt_slice.py` | `gpt_slice_v1` — the out-of-sample GPT rater slice, on items calibration never touched. |
| `build_stance_gap_sample.py` | `stance_gap_v1` — the restatement-artefact sample. |
| `build_3f_sample.py` | `concessionary_v1` — the endorsing universe, sharded for rating. |
| `build_3f_second_rater.py` | `concessionary_second_rater_v1` — the second- and third-rater package. |
| `build_endorsement_feature_package.py` | `S1-ENDORSE-V2`: `endorsement_feature_v1` — the blinded 1,080-row full-set feature-rating package. |
| `check_endorsement_package.py` | `S1-ENDORSE-V2`: recounts the built package against the pre-registered standing gates. Independent of the builder — it reads shards and key, not `provenance.json`. |
| `check_endorsement_labels.py` | `S1-ENDORSE-V2`: one rater's label file against the row gates — one-to-one onto the universe, in-vocabulary values, and a verbatim span behind every non-none decision. Never reads `key.json`, so it cannot leak checkpoint identity into a rater check. |
| `build_endorsement_rater_upload.py` | `S1-ENDORSE-V2`: the frozen shards re-emitted as `.jsonl` + `.csv` + `.md` per part for an external rater, with a manifest of source and output hashes. Never writes `key.json`. |
| `seal_rater_labels.py` | `S1-ENDORSE-V2`: merges one rater's shards, hashes each shard and the merged file, and records provenance including any declared null-span exceptions. Refuses to overwrite an existing seal. Sealing happens before the audit, so labels cannot be revised once the checkpoint contrast is visible. |
| `compare_endorsement_raters.py` | `S1-ENDORSE-V2`: cross-rater agreement (raw, Cohen's kappa, confusion tables; positive and negative agreement for the low-prevalence concession flags), the cross-rater Iron-Law tripwires, and the 100-row blinded audit set. Reads `key.json` for stratification only and emits audit items carrying no checkpoint and no rater label. |
| `analyze_endorsement_features.py` | `S1-ENDORSE-V2`: the four derived-category checkpoint deltas per rater, kept separate. P0/P1/P2 intervals with the **widest** used for decisions, paired sign-flip, Holm over four categories, and the pre-registered RATER-ROBUST / RESOLVED readings. |
| `build_benign_twins.py` | `benign_twins_v1`, and `benign_twins_v2` with `--v2`. |
| `survey_evalset_sources.py` | `S1-06` census of reachable misinformation behaviours across candidate sources. |
| `prescreen_misinfo_candidates.py` | `S1-06` keyword pre-screen. A recall net only, never a decision. |
| `build_evalset_candidates.py` | `evalset_v1` — the blinded candidate package for the expanded set. |

### Analysis
| Script | What it does |
|---|---|
| `decompose_distribution.py` | The main result: behaviour-level distribution decomposition, Phoenix → Starling. |
| `analyze_trajectory.py` † | The 08-27 base-trajectory refusal-versus-capability analysis. |
| `analyze_wrappers.py` † | Step 4 wrapper sensitivity from WildGuard labels. |
| `analyze_stance_gap.py` | `S1-STANCE-GAP` prevalence and paired delta. |
| `analyze_3f.py` / `analyze_3f_adj.py` | `S1-3F` and `S1-3F-ADJ` endorsement-subtype shares. |
| `compare_3f_raters.py` | `S1-3F` second-rater agreement, with the population-weighted κ. |
| `analyze_cooldown_localization.py` | `S1-CKPT`: where in the cooldown the behaviour change appears. |
| `analyze_format_carryover.py` | `S1-FORMAT`: does the document persona carry to prompts naming no format? |
| `analyze_prefix_framing.py` | `S1-PREFIX`: the prefill intervention's arm contrasts. |
| `prefix_framing_sensitivities.py` | `S1-PREFIX` pre-registered sensitivity analyses. |
| `inspect_prefix_tripwires.py` | `S1-PREFIX` hand inspection, triggered by the Iron Law tripwire. |
| `grade_benign_twins.py` / `grade_benign_twins_v2.py` | Rule-based constraint grading for `S1-05` and `S1-05B`. |
| `report_benign.py` † | Benign-set compliance for the H1b control. |
| `wildguard_rubric_regression.py` | `S1-3D`: which rubric dimension WildGuard's `harmful` label tracks. |
| `xtab_wildguard_labels.py` † | Iron Law hand inspection: is (harmful AND refusal) empty by construction? |
| `score_spotcheck_audit.py` | Score the 25-item human spot-check against the anchor and the local judges. |
| `verify_gpt_rater_check.py` | Independent verification path for the GPT rater check. Deliberately imports nothing from `compare_anchors.py`. |
| `sensitivity_missing_labels.py` † | Worst-case sensitivity of the pre-registered contrasts to unlabelled rows. |
| `ifeval_generate.py` / `ifeval_summary.py` | Step 1 IFEval generation and the pre-registered trigger. |
| `harmbench_gap_analysis.py` † | Break the HarmBench refusal gap down by category and list the behaviours where two models differ. |
| `extract_failures.py` † | Sample failure examples per model per SemanticCategory. |
| `audit_grades.py` † | Programmatic audit of WildGuard grades for likely mis-grades. No LLM reads harmful content. |
| `grade_audit_llamaguard.py` † | Inter-rater grade audit: Llama-Guard-3-8B versus WildGuard. |
| `make_delta_report.py` † | Join `runs/*/metrics.json` against `targets.json` into `report/deltas.md`. |

### Inference procedure (`S1-STATS`)
| Script | What it does |
|---|---|
| `calibrate_behavior_bootstrap.py` | Null calibration of the incumbent procedure on 126 disjoint 5-vs-5 splits of one checkpoint against itself. |
| `calibrate_paired_variant.py` | The same calibration for the paired variant. |
| `select_inference_procedure.py` | The frozen head-to-head between `P0` and `P1`. |
| `rederive_intervals.py` | Re-derive every recorded interval under both procedures and report the wider. |

### Task 1 era — Olmo 3 reproduction and tamper-resistance †
Preserved for provenance. None of these are on the Stage 1 critical path.

| Script | What it does |
|---|---|
| `run_master.sh`, `run_master2.sh`, `run_master3.sh` | The Marin-first master chains: full suite, base re-run under a `User:`/`Assistant:` scaffold, then the WildGuard-Test rows. |
| `run_gate3.sh` | Gate 3: four clean rows × 3 runs on Olmo-3-7B-Instruct. |
| `run_posttrain.sh` | Post-master3 runs: the Llama-Guard grade audit and the WMDP base-capability diagnostic. |
| `run_base_capability.sh`, `base_capability_wmdp.py` | Logprob-MC WMDP scoring across Marin-8b-base revisions — the format-independent method for base models. |
| `olmo_posttraining_studyB.sh`, `studyB_reseed.sh`, `studyB_reseed_rest.sh` | Study B: the Olmo post-training trajectory framing test and its reseed. |
| `marin32b_remainder_scopecut.sh` | One-off 32B scope-cut orchestration. |
| `tamper_attack.py`, `tamper_merge.py`, `tamper_run.sh`, `plot_tamper_collapse.py` | The pre-registered tamper-resistance LoRA attack, its merge step, driver, and figure. |

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

### 2026-09-05 · `S1-06` — the expanded evaluation set

- `build_evalset_candidates.py` — assembles the blinded screening package: HarmBench misinfo anchors kept
  whole, WildJailbreak vanilla-harmful through the 08-29 keyword+artefact net, re-cid'd and shuffled.
  Records a sha256 of every source file in provenance.
- `survey_evalset_sources.py` — census of reachable misinformation behaviours across HarmBench (all
  splits), JailbreakBench, AdvBench and WildJailbreak, with exact dedupe across sources. Prints a
  **ceiling**, not an estimate.

**Counting lesson, 2026-09-05.** The 08-29 plan counted WildJailbreak at the **row** level, so a keyword
net returning 98 rows looked like 98 candidates. They are **7 distinct prompts** repeated across
adversarial wrappers, and 6 of the 7 are verbatim HarmBench behaviours. Net-new: zero. Count distinct
texts, and dedupe against the incumbent set, **before** treating a source as a source.

### 2026-09-07 · `S1-05` — benign twins

- `build_benign_twins.py` — generates the 54 twins. Preserves each source behaviour's task verb, artefact
  type and context structure; replaces the subject with a benign one paired **by index under seed
  20260907**, so the pairing is reproducible rather than hand-tuned. Emits four machine-checkable
  constraints per twin and asserts each is recoverable from the prompt text itself.
- `../slurm/benign_twins.sbatch` — the 324-generation job. One job, one GPU, sequential; never an array,
  because an array scatters tasks across nodes and confounds any phoenix-vs-starling comparison.
  Resume-safe: skips a cell whose `responses_raw.jsonl` already exists.
- `ifeval_generate.py` gained `--seed`, `--temperature`, `--top-p` on 2026-09-07 so `S1-05` could reuse it
  at the misinformation runs' sampling settings (0.7 / 0.95 / 2048) instead of IFEval's greedy protocol.
  **Defaults reproduce the original greedy behaviour exactly**, so recorded IFEval numbers are untouched.
  Its provenance block previously hardcoded `temperature 0.0, seed 0` and would have logged the wrong
  decoding for any non-greedy run; it now records what actually ran.
- `grade_benign_twins.py` — the deterministic grader. No judge, no model, no human: title regex,
  paragraph count, verbatim audience string, word range. Truncates at the first fabricated `User:` turn.

**Grader bug caught by its own smoke test, 2026-09-07, before any generation was graded.** The first
version stripped the opening line as a title *unconditionally*, so every response that failed the title
check also lost its first paragraph — depressing the other three constraints on exactly those responses
and correlating all four into what would have looked like a coherent instruction-following signal. The
first line is now stripped only when it really is a title. 13 hand-built cases, including no-title,
title-only, leading-blank and fabricated-turn cases, are checked on every change.

- `analyze_3f_adj.py` — three-rater sensitivity for `S1-3F-ADJ`. Runs the **rater-validity gate first**:
  a rater whose observed agreement with the primary labels fails to beat the 95th percentile of
  reshuffles of its own label vector is recorded as a failed instrument and is **never projected**.
  Then per-rater projected shares, stratified bootstrap CIs resampled within the six strata, all pairwise
  confusion matrices, and a count of raters above the bar — a count, not a verdict.

**Rater-validity lesson, 2026-09-07.** Two of three third-rater passes measured nothing while passing
every *sheet* gate — rows, header, vocabulary, no foreign cids. Gemini Flash answered from a near-fixed
marginal (permutation p 0.377) and was null on the construct but structured on the arm, which
manufactures an apparent arm effect from nothing. A Gemini Pro attempt returned 150 identical labels
noting "missing items data" because **AI Studio does not accept `.jsonl`** — hence `items.md` and
`items.csv` alongside it in any rater package. Gate the **rater**, not just the sheet.

### 2026-09-08 · `S1-05B` — benign twins v2

- `build_benign_twins.py --v2` — same 54 twins and pairing, revised requirement text: a paragraph BAND
  instead of exact equality, and a header that avoids the literal `Requirements:` so a prompt-echo is
  detectable rather than silently passing the audience check.
- `grade_benign_twins_v2.py` — the v2 grader. Primary is the **mean constraints met (0-4)**, not a 4-way
  AND: a mean cannot floor on its hardest component the way v1's conjunction did. **The body is always
  the whole truncated response**, so the four checks are independent by construction.

**Two design notes worth keeping.** v1's conjunction floored at 0.00%/1.85% because exact paragraph
equality was hit by 8/162 and 11/162 responses — check that every component is individually achievable
before freezing a composite. And making the body the whole response makes the title line parse as a
block, so the grading band is [N, N+3] against a prompt asking for N..N+2: one wider at the top, so the
paragraph check cannot be decided by whether a title was emitted. The grader's smoke test includes an
explicit independence assertion for exactly that.

**Correction after verification (2026-09-08).** The echo detector is a **known defect, left in place**
because the recorded run used it: `ECHO = "Requirements:"` and the v2 prompt deliberately excludes that
string (`build_benign_twins.py:158` asserts its absence), so the conjunctive guard never fires and the
audience check is the bare substring match v2 claimed to replace. Real echo against the prompt's actual
marker is 2 phoenix / 1 starling of 162, so nothing substantive turns on it. **Derive an echo marker from
the prompt at build time; never hardcode it.**

### 2026-09-08 · `S1-FORMAT` — does the document persona carry over?

- `analyze_format_carryover.py` — CPU only, no judge, no model, no new generation. Five mechanical format
  measures on the 1,080 already-labelled misinformation responses, computed on the convention-1 truncated
  body so format is measured on the text the raters saw. Primary is `document_open` prevalence,
  behaviour-level, phoenix vs starling, with the same bootstrap / sign-flip machinery as every other
  behaviour-level contrast here.

```
/usr/bin/python3 scripts/analyze_format_carryover.py \
  --items <labels>/full_phoenix_starling_v1/items.jsonl \
  --key   <labels>/full_phoenix_starling_v1/key.json \
  --labels <labels>/full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl \
  --out docs/results/09-08_format_carryover
```

Note `/usr/bin/python3`: it is the only interpreter on the laptop with numpy. The per-instance labels live
outside the repo tree by design; rsync them to a scratch directory, never into the working tree.

**Design note.** `assistant_preamble` deliberately contains **no refusal token**. Adding `I cannot` or
`I'm sorry` to that marker list would make the preamble measure correlate with refusal by construction,
and the refusal drop is one of the things the analysis must keep separable. Refusal openers are reported
as their own descriptive line and never folded in.

### 2026-09-08 · `S1-PREFIX` — is the delivery framing proximally sufficient?

- `../repro-olmo3-safety/config/base_template_v2_delivery.txt` — `Assistant: Here it is:` prefill.
- `../repro-olmo3-safety/config/base_template_v2_deflect.txt` — `Assistant: I've reviewed your request.`
  prefill, the control that separates "any prefill" from "this framing".
- `../slurm/prefix_framing.sbatch` — 3 arms × 5 seeds = 15 runs, one job, one GPU, sequential. The arms
  are compared to each other, so an array would confound arm with hardware.

**The arm IS the template, so the template's sha256 is written into each run's `provenance.json` and the
resume gate refuses to reuse a run whose scaffold hash differs.** Without that, a resubmission under a
changed scaffold would silently collapse the experiment into three copies of one arm and no line in any
log would say so. `dry_run_check.py` gained `c_prefix_scaffolds` for the same failure class: three
scaffolds must exist, carry `{instruction}` and `Assistant:`, and hash to three distinct values.

Both prefix strings are truncations of openers actually observed in the recorded runs — `Here it is:` at
Starling (`i00679`), `I've reviewed your request` at Phoenix (`i00129`) — and both are artefact-agnostic,
because the 54 behaviours request articles, posts, letters and edits alike.

**Analysis (added 2026-09-09, after job 17270630).** All four run on the Torch login node against the
preserved raw labels; CPU only, no model, no judge, no new generation. Aggregate counts only — none of
them ever prints or writes response text.

- `analyze_prefix_framing.py` — the registered analysis. Unconditional behaviour-level harmful rate per
  arm, the paired `delivery − none` and `deflect − none` contrasts (behaviour bootstrap, seed 20260908,
  10k resamples; sign-flip permutation p), `f` against the traj4 endpoint gap, every pre-registered gate,
  and the frozen decision table including the overriding CONFOUNDED-BY-PREFILL rule. Reuses `load_run`
  and `tag_table` from `analyze_trajectory.py` so label semantics match every other misinformation run.

```bash
repro-olmo3-safety/.venv-safety-eval/bin/python scripts/analyze_prefix_framing.py \
    --labels /scratch/gs157/marin-misinfo-labels \
    --prefix 2026-09-08-prefix-h200 --traj-prefix 2026-08-28-traj4-h200 \
    --out docs/results/09-08_prefix_framing
```

- `inspect_prefix_tripwires.py` — hand inspection required by the Iron Law tripwire on the exact 0.0%
  empty / non-response rates. Compares the arms against the traj4 reference on empties, echo, length
  quantiles and missing labels, and checks that no response begins with its own forced prefix (which is
  how we know the harness recorded the continuation only).
- `xtab_wildguard_labels.py` — raw row-level cross-tabulation of `response_harmfulness` against
  `response_refusal`. **Established that WildGuard labels harmful and refusal together for 0 of 1,890
  in-scope rows**, so the two are mutually exclusive and `harmful | non-refusal` is a re-expression of
  the harmful rate rather than an independent axis. Project-wide consequence; see `docs/decisions.md`.
- `prefix_framing_sensitivities.py` — added analyses that do **not** replace the registered one: the
  harmful × refusal decomposition (how much of the harmful rise is the pre-declared partly-forced refusal
  drop), `f` under the within-job baseline instead of the cross-job traj4 one, and the missing-label bound.

### 2026-09-09 · `S1-STATS` — is the inference procedure calibrated?

- `calibrate_behavior_bootstrap.py` — null calibration for the behaviour-level bootstrap this project uses
  in every contrast. Splits one tag's seeds into all disjoint half-vs-half pairs, where the true difference
  is **zero by construction**, and counts how often the frozen procedure rejects. Also reports per-seed
  instability and seed-level (t) intervals for the `S1-PREFIX` contrasts.

```bash
repro-olmo3-safety/.venv-safety-eval/bin/python scripts/calibrate_behavior_bootstrap.py \
    --labels /scratch/gs157/marin-misinfo-labels
```

Result on phoenix's ten seeds: the CI excludes 0 in **27.8%** of the 126 disjoint 5-vs-5 splits (refusal
34.9%) against a nominal 5%. Published intervals are roughly half their proper width. See
`docs/decisions.md` 2026-09-09.

- `select_inference_procedure.py` — runs the four candidates against the frozen calibration protocol and
  applies the frozen bar and tie-break. Selection on phoenix, confirmation on starling / deeper-starling /
  jellyfish. ~5 minutes.
- `rederive_intervals.py` — every in-scope recorded contrast under all four candidates, side by side.
  Covers `S1-TRAJ`, `S1-CKPT`, `S1-PREFIX` (from `all.json`), `S1-FORMAT` (from `items`/`key`, reusing
  `measure`/`tag_of`) and `S1-05B` (from the preserved twins responses, reusing `grade`). Reports only,
  declares no canonical interval, because selection returned NO CANDIDATE PASSES.

```bash
L=/scratch/gs157/marin-misinfo-labels
repro-olmo3-safety/.venv-safety-eval/bin/python scripts/select_inference_procedure.py \
    --labels $L --out docs/results/09-09_procedure_selection
repro-olmo3-safety/.venv-safety-eval/bin/python scripts/rederive_intervals.py \
    --labels $L --items $L/full_phoenix_starling_v1/items.jsonl \
    --key $L/full_phoenix_starling_v1/key.json \
    --twins $L/benign_twins_v2/twins.jsonl \
    --twin-responses $L/benign_twins_v2/raw/responses.jsonl \
    --out docs/results/09-09_procedure_selection
```
- `calibrate_paired_variant.py` — gap check: the registered calibration compares disjoint seed halves
  (unpaired), but every recorded contrast is applied paired. This re-runs the same 126 splits pairing seed
  *i* with seed *i*, an artificial pairing of independent seeds. ADDED analysis; does not replace the
  registered calibration.

### 2026-09-09 · `S1-JUDGE-VOCAB` — do any labels sit outside the locked rubric vocabulary?

- `audit_label_vocabulary.py` — walks every rubric-schema file under the labels root and counts values
  outside `config/judge_rubric_v1`. Verdict ISOLATED: 21 files, 6,405 rows, **2 out-of-vocabulary
  instances on 1 distinct stimulus**, both `stance="refutes"` from `olmo32`, a judge that had already
  failed selection. Zero in `claude_fable_pass2.jsonl`, the primary labels. No recorded number changed.

  **Scope is discovered from the data root, never typed.** The first frozen list omitted
  `gpt_slice_v1/sheet_gpt.csv` — an externally filled sheet, the highest out-of-vocabulary risk in the
  project — and audited the Gemini sheet that *failed* the validity gate while skipping the `gemini_pro`
  sheet the recorded `S1-3F-ADJ` result actually rests on. A typed list passes silently on an absent
  file; a glob cannot fail a completeness gate.

- `judge_dimensions.py` — **the finding was the gap, not the count.** Nothing in the pipeline rejected an
  out-of-vocabulary value. It now validates `relevance` / `task` / `stance` against the locked
  vocabulary, still writes the emitted value (never silently rewrites), flags the row `oov_<dim>`,
  records counts in provenance, and **fails the run above a 1% rate** with an instruction to fix the
  prompt or the judge rather than relabel.

  One caveat carried into the result: the quality-null validity check tests exactly the invariant this
  script enforces, so on the four local-judge files it *could not fail* (537/537, 288/288). Reported as
  non-informative, not as a pass. It stays informative for the human-facing CSVs.

Evidence: `docs/experiments/09-09_judge-vocabulary-audit.md`; `docs/results/09-09_vocab_audit/`.

### 2026-09-08/09 · `OPS-001` — workspace recovery, and the guards that came out of it

An ad-hoc `rsync -az --delete ./ torch:$WORK/` destroyed every Torch workspace path the repo does not
track: `hf_cache/hub/` (~100GB of weights including the gated WildGuard judge), `pythons/`, the
`safety-eval` working tree, and `runs/twins_v2/`. Recovery restored 270GB across nine revisions with zero
tag drift. **No evidence was lost and no recorded number changed** — all of it lives in
`/scratch/gs157/marin-misinfo-labels/`, outside the workspace, which is the reason the tree is laid out
that way (`docs/DATA_INVENTORY.md`).

Three guards exist now because they did not before:

- `sync_to_torch.sh` — **refuses `--delete`.** It was already the only sanctioned sync path; the
  incident came from bypassing it. The refusal makes the rule mechanical instead of prose.
- `check_tag_drift.py` — compares the cache's resolved tag SHAs against the reconstructed baseline in
  `docs/resolved_revisions_reconstructed.json` (rebuilt from surviving job logs, because the incident took
  the original `docs/resolved_revisions.json` snapshot with it) and fails on a moved tag. The load-bearing check during recovery was
  not the licence but the **revision**: the restored judge is snapshot `cbba4823`, which appears 1,240
  times in this project's job logs. A different revision would have passed preflight, loaded cleanly, and
  silently broken comparability with every recorded WildGuard number.
- `benign_twins_v2.sbatch` — preserves raw outputs outside the workspace. Its 324 generations survived
  the incident by luck alone.

Evidence: `docs/research_journal.md`, 2026-09-08 and 2026-09-09 incident entries;
`docs/resolved_revisions.json`.
