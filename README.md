# marin_red_teaming

Safety red-teaming of [`marin-community/marin-8b`](https://huggingface.co/marin-community/marin-8b-base),
using [`allenai/Olmo-3-7B-Instruct`](https://huggingface.co/allenai/Olmo-3-7B-Instruct) as a reference point.

The approach is two-stage: first reproduce Olmo 3's *published* safety table to prove the harness is
trustworthy, then point that validated harness at Marin.

**→ Start with [`repro-olmo3-safety/report/SUMMARY.md`](repro-olmo3-safety/report/SUMMARY.md)** — the
consolidated report, with an appendix explaining what every benchmark measures.

## Headline results

**Stage 1 — harness validation.** Reproduced Olmo-3-7B-Instruct's published safety table
([arXiv:2512.13961](https://arxiv.org/abs/2512.13961), Table 53) to within ±3pp on **12 of 13 rows**
(WildGuard-Test blocked by a gated dataset). Tolerance was pre-registered before the runs.

**Stage 2 — Marin-8b-instruct vs Olmo-3-7B-Instruct.** Competitive overall, different profile:

| | Marin | Olmo | Δ |
|---|---|---|---|
| DoAnythingNow | 96.0 | 77.9 | **+18.1** |
| WildJailbreak-Harmful | 76.0 | 69.5 | +6.5 |
| StrongReject | 92.8 | 88.4 | +4.5 |
| HarmBench | 87.3 | 93.9 | **−6.6** |

Marin is markedly harder to jailbreak via adversarial *framing* (it shrugs off persona attacks Olmo falls
for — AIM 0% vs 64%), but softer on plainly-asked harm, driven almost entirely by **misinformation**
(+14.8pp). Single most actionable gap = misinformation, not dual-use.

**Stage 3 — what post-training buys.** Marin-8b-base is dramatically less safe than instruct on every
refusal metric (+40–72pp from post-training), complying with ~96% of adversarial harmful prompts.

### Scope caveat — read before citing any of this

These numbers measure **default-behavior / casual-user safety** — whether the model refuses a normal user.
They do **not** measure tamper-resistance. For open weights, refusal training is strippable in dozens of
adversarial fine-tuning steps ([arXiv:2508.06601](https://arxiv.org/abs/2508.06601)), and the base model
complies with nearly everything. Treat this as a regression and gap-mapping tool, not a robustness claim.

## Layout

| Path | What's in it |
|---|---|
| [`repro-olmo3-safety/report/`](repro-olmo3-safety/report/) | `SUMMARY.md` + per-analysis reports (deltas, HarmBench gap, failure examples) |
| [`repro-olmo3-safety/runs/`](repro-olmo3-safety/runs/) | Run record for 153 runs: `command.txt`, `provenance.json`, `metrics.json` |
| [`repro-olmo3-safety/config/`](repro-olmo3-safety/config/) | Row→config map, base-model prompt templates |
| [`scripts/`](scripts/) | Setup, run, and analysis scripts — see [`scripts/README.md`](scripts/README.md) |
| [`docs/`](docs/) | Research journal, decision log, pre-registered experiment files |
| [`outputs/`](outputs/) | Lit-review notes, pretraining-safety proposal |

## Reproducing

```bash
bash scripts/setup_safety_eval.sh   # isolated venv, safety-eval @060cc903, vllm==0.11.0
bash scripts/run_row.sh <model_repo> <revision> <folder:config> <run_name> [seed]
python scripts/make_delta_report.py # join runs/*/metrics.json vs targets.json -> report/deltas.md
```

Heads-up for anyone cloning: these scripts were written for one machine and hardcode
`/home/paperspace/marin` as the repo root. Adjust the paths at the top of each before running.

Environment for every number in the report: one A100 80GB, `allenai/safety-eval` @`060cc903`,
vLLM 0.11.0, transformers 4.57.1, temp 0.7 / top_p 0.95, 3 seeds per row. Each run's exact command and
library versions are recorded in its `runs/<name>/{command.txt,provenance.json}`.

## What is not in this repo

Excluded by [`.gitignore`](.gitignore), with reasons:

- **`runs/**/all.json`** — per-instance generations, ~2.7 GB. These contain full, untruncated model
  completions to harmful prompts, so they are deliberately not published. Regenerate with `run_row.sh`.
- **`safety-eval/` and `.venv-safety-eval/`** — third-party checkout (pinned by SHA) and its venv, ~9.5 GB.
- **`logs/`, model weights, `outputs/olmo3.pdf`** — machine-local, large, or third-party redistribution.

Harmful-content policy: the failure examples in `report/` are truncated to the short preamble that
establishes compliance — enough to show and grade the failure, without reproducing usable payloads.

## Verification

Every headline number was recomputed from the raw per-instance labels by an independent agent on a
separate code path before being marked verified. Success criteria and tolerances were written into the
experiment file *before* each run — see [`docs/experiments/`](docs/experiments/). Rows that could not be
independently reproduced are marked UNVERIFIED rather than reported.
