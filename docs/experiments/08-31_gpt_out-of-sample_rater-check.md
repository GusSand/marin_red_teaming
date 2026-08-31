# 08-31 · GPT out-of-sample rater check on the step-3 labels

**Status:** pre-registered 2026-08-31, before any GPT label was produced or read.
**Owner:** Claude Code · **Runner:** gs157 (manual, ChatGPT) · **Cost:** no GPU.

## Research question

The step-3 decomposition rests on labels from **one rater** (blind Claude Fable 5, pass 2,
`judge/claude_fable_pass2.jsonl`). Are those labels rater-specific?

What we already have, and why it is not enough:

| evidence | what it measures | limitation |
|---|---|---|
| test–retest pass 1 vs pass 2 (0.941 / 0.860 / 0.809) | **self**-consistency of one rater | same model, not inter-rater |
| Claude vs GPT on the calibration 150 (stance κ 0.78) | inter-rater | those 150 sit **inside** the 1,080, so in-sample; and the two ran under **different** multi-turn conventions |
| qwen72 / olmo32 decompositions on all 1,080 | does the **Δ** replicate | answered: yes on sign and, for qwen, magnitude. Both failed judge selection |

The gap this fills: an **out-of-sample, convention-matched, second frontier rater**.

## Setup

- Population: the 930 full-set items not in the calibration 150 (matched on exact request+response).
- Sample: **150**, simple random, stratified only by arm (75 phoenix / 75 starling), seed 20260831.
  No stratification on label — that would bias the agreement estimate toward rare classes.
- Blinding: items re-cid'd to shuffled `g####`. The full-set `i####` ids are run-ordered and would
  leak the arm — the defect that confounded pass 1.
- Conventions: `config/annotator_conventions_v1.md` **in full, including convention 1** (judge only
  the text before the first fabricated `User:` turn). This is the change from the calibration GPT run,
  which never received convention 1. Matching conventions is the point: the comparison target is
  pass 2, so the rater must operate under pass 2's rules.
- Comparison: `scripts/compare_anchors.py <dir> sheet_claude.csv sheet_gpt.csv`.
- Scripts: `scripts/build_gpt_slice.py` (builder), `scripts/shard_tool.py check` (validation).

## Pre-registered criteria

Primary — GPT vs Claude-pass-2 on the 150 out-of-sample items:

| outcome | condition | consequence |
|---|---|---|
| **supports** | stance κ ≥ 0.70 **and** six-category agreement ≥ 0.75 **and** three-way ≥ 0.90 | step-3 labels carry a defensible out-of-sample reliability figure; the verdict stands as written |
| **moderate** | stance κ 0.60–0.70, or six-category 0.65–0.75 | verdict unchanged; the rater-dependence caveat is strengthened and quoted with this number |
| **undermines** | stance κ < 0.60 **or** six-category < 0.65 | the pass-2 labels are rater-specific. Step 3's Δ is re-examined against a second full-set frontier rater before the result is reported outside this repo |

Secondary, and load-bearing for the interpretation: **per-class agreement on `corrects` ≥ 0.70.**
The headline reading turns on `correct` being a real, large category (32.2% of Phoenix mass). If two
frontier raters cannot agree on what "argues against the false premise" means, that reading is soft
regardless of the aggregate numbers.

Reported alongside, no threshold: per-dimension agreement and κ, the confusion pairs, quality
Spearman ρ and mean |Δ|, and the same statistics recomputed on the calibration 150 so the
in-sample / out-of-sample and convention-gap effects are separable.

## What this cannot do

150 items spread over 54 behaviors is roughly 1.4 items per behavior per arm — far too thin for the
behavior-level bootstrap. **This yields an agreement estimate, not an independent decomposition.**
The Δ-replication question is already answered by the qwen72 / olmo32 runs
(`docs/results/08-28_stage1/judge_sensitivity/`). Do not read this experiment as a second estimate
of +28.5pp.

## Results

_(empty until the sheet comes back)_
