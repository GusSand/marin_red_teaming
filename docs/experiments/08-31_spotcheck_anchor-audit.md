# Experiment (PRE-REGISTERED): does gs157's spot-check support the Claude anchor?

Created 2026-08-31, **after gs157's 25 labels were written and validated, and before any comparison to
any anchor or judge was computed.** gs157 has not seen `sheet_claude.csv`, `sheet_gpt.csv`, `key.json`
or the `judge/` outputs. The analyst has not computed the comparison. Criteria are therefore frozen
before unblinding, which is the property that matters here.

Closes `IN-002`. Gates `S1-SYNTH`. Parent: `08-28_phoenix-starling_distribution-decomposition.md`,
step 2 deviation of 2026-08-29, which created the spot-check but **fixed no threshold for it** — it says
only that the audit is "reported alongside". This document supplies the missing decision rule.

## Research question

The step-3 labels over the 1,080 come from a blind Claude Fable 5 annotator. No local judge cleared
selection, so that anchor carries the decomposition alone. On the items where it was most contested,
does an independent human adjudicator side with it?

## Inputs

| input | path |
|---|---|
| gs157's 25 labels | `/scratch/gs157/marin-misinfo-labels/calibration_v1/spotcheck/sheet.csv` |
| Claude anchor, 150 | `.../calibration_v1/sheet_claude.csv` |
| GPT anchor, 150 | `.../calibration_v1/sheet_gpt.csv` |
| local judges qwen72, olmo32 | `.../calibration_v1/judge/*.jsonl` |
| subset provenance | `.../calibration_v1/spotcheck/why.json` |

Labels only. No response text is read, printed or committed.

## The guard — why raw agreement is the wrong number

`build_spotcheck.py` selected these 25 **because** the Claude anchor disagrees with *both* local judges
on some categorical dimension. They are the maximally contested items in the calibration set, not a
random draw. Raw agreement is therefore low by construction.

**Raw gs157-vs-Claude agreement on these 25 must never be compared to the 150-item anchor figures**
(stance κ 0.78, derived-6 0.71) or quoted as an agreement rate for the anchor. Any report that puts the
two side by side without this sentence is wrong. This paragraph is frozen before the numbers exist so it
cannot be softened after.

## The statistic — head-to-head adjudication

Each contested item already carries two rival labels. gs157 is the adjudicator, so the informative
quantity is who he sides with, not how often he agrees with one of them.

Per dimension *d* ∈ {relevance, task, stance}, restrict to the **contested set for that dimension**:
items where the anchor's label differs from *both* local judges on *d*. (Selection required this on at
least one dimension, not all, so the restriction must be recomputed per dimension and its n reported.)

Within that set,each item falls in exactly one bucket:

| bucket | rule |
|---|---|
| **anchor** | gs157 == Claude |
| **judges** | gs157 ∈ {qwen72, olmo32} and gs157 ≠ Claude |
| **neither** | gs157 matches no one |

Report counts and shares per dimension, plus n. **Stance is primary** — it is the dimension the step-3
decomposition turns on.

## Exclusions — frozen

- The 8 items whose `notes` begin with `no_stance` are **excluded from the stance comparison** and
  reported as a separate third bucket, per `config/annotator_conventions_v1.md` rule 6 scope note. Their
  `stance=endorses` is a recording convention gs157 had and the anchors did not; comparing it would
  measure the convention, not the raters. They remain in the relevance and task comparisons.
- No other exclusions. No item is dropped for being hard.

## Pre-registered readings

| outcome | reading |
|---|---|
| **anchor** > **judges** on stance, and **neither** ≤ 40% | Supports the anchor. It wins the head-to-head where it was most contested. Step-3 labels stand; `IN-002` closes as satisfied. |
| **judges** ≥ **anchor** on stance, or **neither** > 50% | Undermines it. The step-3 labels get an explicit caveat, a line goes in `docs/decisions.md`, and `S1-SYNTH` must state it as a limitation. |
| anything else | Mixed. Reported as mixed, with a caveat weaker than the undermines branch. |

**`neither` is the bucket to watch.** A high `neither` share means both the anchor and the local judges
are off on contested items — a failure mode no agreement statistic computed *between* them could reveal.

Secondary, reported but not decisive: gs157 against the GPT anchor on the same sets; per-dimension raw
agreement with each source; the derived six-category and three-way collapses.

## Power — stated before the numbers

n = 25 items, and the stance contested set after the `no_stance` exclusion will be smaller still,
plausibly 10–17. **This cannot support a precise estimate and no percentage from it should be quoted as
one.** The honest output is directional: the anchor looks sound, looks shaky, or both raters are off.
Exact n per dimension is reported alongside every share. If a contested set falls below **n = 8**, that
dimension is reported as **not evaluable** rather than as a result.

## Standing data gates

- gs157's sheet validates against the locked contract (`shard_tool.py check`) — already confirmed OK,
  25/25, all values in vocabulary.
- Every spot-check cid appears in all four label sources; report any that do not.
- Assert the selection property actually holds: for each item, the anchor differs from both local judges
  on at least one dimension. A failure means `why.json` and the sheet have drifted apart.

## Verification

Fresh subagent, given only the five label files and this document, denied the analysis script. It
recomputes the per-dimension contested sets, the three bucket counts, and n. Tolerance: **exact counts**
— these are integers over 25 items, so there is no sampling tolerance to allow. Mismatch → `INBOX`,
logged UNVERIFIED.

## Decision consequences

- Closes `IN-002` either way. A "supports" verdict satisfies it; an "undermines" verdict satisfies it
  too, with a caveat attached.
- Feeds `S1-SYNTH`'s statement of what is established about the rater.
- Does **not** change the step-3 numbers. It changes how confidently they are described.

## Cost

CPU, seconds. No GPU, no Slurm.

## Results

(empty until run)
