# Experiment (PRE-REGISTERED): does the document-persona difference appear in the misinformation set?

Created 2026-09-08, **before any format statistic was computed on the misinformation responses.** Task
`S1-FORMAT`. CPU-only. No new generation. Uses the 1,080 responses already collected and labelled for
`08-28_phoenix-starling_distribution-decomposition.md`.

## Why this exists

`S1-05B` found that the entire benign-twins delta is carried by two checks one emitted document header
satisfies together. Starling opens with `Title: X` / `Dear <audience>,`; Phoenix opens with a chat
preamble. That raises a specific alternative to both Stage 1 hypotheses:

> A shift from chat-preamble output to document output would produce the benign gains **and** the +28.5pp
> attempt-strong shift together, with no change in instruction-following or in safety behaviour.

The twins cannot test this — they never touch the misinformation set. This does.

## Disclosure

I designed this after seeing `S1-05B`'s per-constraint results, so the marker definitions are borrowed,
not invented: they are taken **verbatim** from the `S1-05B` verifier's diagnostic code, which was written
against the benign twins with no sight of the misinformation data. **I have not computed any format
statistic on the misinformation responses.** The measures below are frozen before the first look.

## Research question

Is the Phoenix→Starling output-format difference present in the misinformation responses, at what
magnitude, and does the rubric-measured shift co-vary with it?

## Data

`/scratch/gs157/marin-misinfo-labels/full_phoenix_starling_v1/` — `items.jsonl` (blinded responses),
`key.json` (cid → checkpoint, BehaviorID), and the merged pass-2 rubric sheet. 54 behaviours × 10 seeds ×
2 checkpoints = 1,080 rows. Same rows behind the verified decomposition; no new data are collected.

Bodies are cut at the first `\nUser:` — convention 1, the same truncation the raters were told to apply,
so format is measured on the text that was labelled.

## Format measures — frozen, mechanical, no judge

| measure | definition on the truncated body |
|---|---|
| `document_open` | first non-empty line matches `^(Title:\|#)\s*\S` **or** `^(Dear\|To)\s+\S` |
| `title_anywhere` | any line matches `^(Title:\|#)\s*\S` |
| `salutation` | any line matches `^(Dear\|To)\s+\S` |
| `assistant_preamble` | first non-empty line starts with one of: `Here's`, `Here is`, `I've`, `I'll`, `Sure,` |
| `single_block` | body contains no blank line |

**`assistant_preamble` deliberately contains no refusal token.** `I cannot`, `I'm sorry` and friends are
excluded by design: including them would make the preamble measure correlate with refusal by construction,
and the refusal drop is one of the things this is meant to keep separable. Refusal-opener prevalence is
reported alongside as its own descriptive line, never folded into `assistant_preamble`.

`document_open` is the **primary** measure. It is the benign twins' effect expressed as one variable.

## Primary analysis

Behaviour-level: for behaviour *b* and checkpoint *c*, the mean of `document_open` over its 10 seeds; then
the mean over 54 behaviours. Report Δ = starling − phoenix with a behaviour-level bootstrap 95% CI
(10,000 resamples, seed 20260908) and a sign-flip permutation p. Same machinery as every other
behaviour-level contrast in this project.

## Decision rules — frozen

| outcome | rule | reading |
|---|---|---|
| **CARRIES** | Δ ≥ +40pp and CI excludes 0 | One persona difference spans both the benign and the misinformation sets. `S1-SYNTH` must state that the most visible Phoenix→Starling change is output format, and treat the compliance account as confounded with it. |
| **DOES NOT CARRY** | Δ < +10pp or CI includes 0 | The twins' format effect does not transfer. The misinformation shift is not a format artefact and the benign instrument was simply measuring something else. |
| **PARTIAL** | anything between | Reported as partial, read in neither direction. |

+40pp is chosen because the twins' `title` gap was +86pp and the `audience` gap +71pp: a persona that
transfers should be visible at a substantial fraction of that, and +40pp is roughly half the smaller one.
+10pp is the project's standing "two label flips is not an effect" floor scaled to this n.

## Secondary — descriptive only, and stated as such before the numbers exist

1. Cross-tab each format measure against the derived rubric category, **within checkpoint**.
2. Refusal rate and attempt-strong rate **within** `document_open` strata.

**These are associations, and stratum 2 conditions on a post-treatment variable.** If format is a mediator,
conditioning on it removes real effect; if format and stance share a cause, conditioning induces bias.
Neither direction supports a causal claim. This is written here, before the run, so no post-hoc reading can
promote it. **No verdict in this experiment may rest on the secondaries.**

## Tripwires and gates

- Iron Law: an exact 0% or 100% prevalence on any measure at either checkpoint → hand inspection before
  interpretation. This wording has now missed two exact rates in `S1-05B`; here it also covers **any
  measure computed as a secondary**, not only the primary.
- Any measure below 5% at both checkpoints is reported as uninformative and excluded from the cross-tabs.
- Join completeness: every cid in the label sheet resolves in `key.json`; no duplicate cids; 540 rows per
  checkpoint; 54 behaviours × 10 seeds per checkpoint, exactly.
- Empty bodies reported per checkpoint.

## Verification

Fresh subagent, given only `items.jsonl`, `key.json`, the label sheet and this document; denied my script.
It re-implements the five measures and recomputes the primary. Tolerance **0.5pp** on prevalences,
**1.0pp** on Δ.

## Decision consequences

- A **CARRIES** result changes what `S1-SYNTH` can claim: the headline stops being "compliance rose" and
  becomes "output format changed, and the compliance measures are downstream of it" — and Stage 2 needs an
  endpoint that is not format-sensitive.
- A **DOES NOT CARRY** result retires the confound and restores the `S1-05B` reading to a straightforward
  general-versus-stance question, to be settled by `S1-05C`.
- Either way it does not change any recorded step-3 number. It reinterprets them or it does not.

## Cost

CPU only, minutes. No GPU hours.

## Results

(empty until run)
