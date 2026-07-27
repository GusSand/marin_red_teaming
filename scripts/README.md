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
