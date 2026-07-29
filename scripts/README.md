# scripts/

Reproduction scripts for the Olmo 3 7B safety-number reproduction (BACKLOG Task 1).

Only scripts needed to reproduce results live here. Throwaway/temporary scripts go in
their own subdir and are not committed.

## Current scripts
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

### 32B compute topology (2026-07-28/29)
32B base-vs-base ran one model per A100 80GB (bf16 fits): `marin-32b-base` (Qwen3 arch, fp32 weights
= 122G on disk) on the LOCAL box; `Olmo-3-1125-32B` (Olmo3 arch, 61G) on a REMOTE Paperspace A100
reached via `ssh -i ~/.ssh/marin_worker paperspace@184.105.215.102`. Remote results are rsynced back
to local `repro-olmo3-safety/runs/` before the remote is shut down (fresh-instance storage is ephemeral).
