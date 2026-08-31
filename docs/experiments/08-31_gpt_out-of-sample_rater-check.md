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

**Ran 2026-08-31.** Sheet returned by gs157 (ChatGPT), 150 rows, md5 `790ab77f1b2008a571bec840ff8a293c`,
at `/scratch/gs157/marin-misinfo-labels/gpt_slice_v1/sheet_gpt.csv`. `shard_tool.py check`: *OK 150 rows,
all cids present, all values valid.* No missing quality cells, no unscorable rows.

### Verdict: MODERATE

`supports` needed all three; two of the three missed.

| statistic | value | `supports` bar | met |
|---|---|---|---|
| stance κ | **0.705** | ≥ 0.70 | yes |
| six-category agreement | **0.733** | ≥ 0.75 | no — lands in the 0.65–0.75 moderate band |
| three-way agreement | **0.867** | ≥ 0.90 | no |

Nothing is near the `undermines` floor (κ 0.60 / six-category 0.65). **Per the pre-registered rule the
step-3 verdict stands unchanged and the rater-dependence caveat is strengthened, quoted with κ = 0.705
and six-category agreement = 0.733.**

**Secondary criterion met.** Per-class agreement on `corrects` ≥ 0.70 under every reading:
F1 **0.864**, Claude-recall 0.946, GPT-recall 0.795 (Claude 37, GPT 44, both 35). The pre-registration
did not fix which of the three, so all are reported; the criterion is insensitive to that choice here.
`correct` is the **best**-agreed of the six categories, so the headline reading — that `correct` is a
real and large category — survives the check.

### Where the raters actually differ

Disagreement is concentrated in `hedge`, not in the categories the decomposition turns on.

| category | Claude n | GPT n | F1 |
|---|---|---|---|
| correct | 37 | 44 | **0.864** |
| attempt-strong | 55 | 45 | 0.820 |
| refuse | 20 | 11 | 0.710 |
| no-attempt | 7 | 16 | 0.609 |
| attempt-weak | 9 | 7 | 0.625 |
| hedge | 22 | 27 | **0.449** |

GPT reads 9 of Claude's 20 refusals as something softer (`refuses->hedges` 6, `refuses->corrects` 3) and
sees more than twice as many `no-attempt`. The dimension confusions say the same: stance
`endorses->hedges` 8, `hedges->corrects` 6, `hedges->endorses` 5. **The endorse/hedge and refuse/hedge
boundaries are where two frontier raters stop agreeing.** Relevance κ is low (0.513) on high agreement
(0.927) — the usual small-marginal artefact, 11 disagreements total. Quality Spearman ρ = 0.495,
mean |Δ| = 0.84 on the 1–5 scale (n = 98 both-scored).

### Caveat on the three-way number

0.867 is the collapse closest to step 3's headline (mass leaving non-endorse for attempt). It is the
statistic that missed its bar by the widest margin. **Report it whenever the +28.5pp figure is quoted
outside this repo.**

### In-sample / out-of-sample and the convention gap

Recomputed on the calibration 150 for comparison (`--no-write`, so the pending spot-check subset was
not regenerated):

| statistic | out-of-sample, convention-matched | calibration 150, no convention 1 |
|---|---|---|
| stance κ | 0.705 | 0.784 |
| six-category agreement | 0.733 | 0.787 |
| three-way agreement | 0.867 | 0.927 |
| `correct` F1 | 0.864 | 0.882 |

Agreement is **lower** out-of-sample even though the conventions now match. Do not read that as
"convention 1 hurt". Three things differ at once — in-sample vs out-of-sample, the convention, and the
class composition (`correct` is 44% of the calibration set against 25% here), and κ depends on the
marginals. The comparison is descriptive; the design cannot separate the three.

### Verification

Headline numbers recomputed on a second, independent path — CSVs parsed from scratch, κ from sklearn's
`cohen_kappa_score` rather than the hand-rolled estimator in `compare_anchors.py`, the six-category rule
re-derived from the rubric rather than imported. **All five matched exactly** (stance κ 0.705,
six-category 0.733 / κ 0.655, three-way 0.867, `correct` F1 0.864). Script:
`scripts/verify_gpt_rater_check.py`. The fresh-subagent reproduction from raw data was not run this
session; the numbers are cheap to re-derive and the independent path above is the standing minimum.

### Scope, restated

This is an agreement estimate. It is **not** a second estimate of +28.5pp — 1.4 items per behavior per
arm cannot support the behavior-level bootstrap. Δ-replication remains answered by the qwen72 / olmo32
runs.
