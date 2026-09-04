# Experiment (PRE-REGISTERED): how much do restatement-without-assertion items move the headline?

Created 2026-09-04, **before any item was rated for the restatement pattern and before any prevalence
was inspected.** Task `S1-STANCE-GAP`, promoted ahead of `S1-3F` by gs157 on 2026-09-04 because it is
the open risk to numbers now going into an external presentation.

**POST HOC.** Raised 2026-08-31 while closing `S1-3D`, after the step-3 result existed. Label it post
hoc wherever it is reported.

## Research question

The locked rubric gives `relevance` and `task` explicit wording for a restated request but gives
`stance` none — all four stance classes assume the response asserts something. Convention 6 fixed that
on 2026-08-31. The pass-2 annotation that produced the 1,080 labels **never had the rule** and resolved
the ambiguity undocumented, so the derived six-category masses behind −12.2 / −12.2 / +28.5pp inherit an
unrecorded convention.

How prevalent is the pattern, and **could it move the headline?**

## The sharp version of the question

+28.5pp is a *paired difference*. A labelling artefact that occurs equally in both arms largely cancels
in that difference. It biases the headline only if it is **differentially distributed** between Phoenix
and Starling. So the primary quantity is not prevalence — it is the **paired-behaviour difference in
prevalence**.

## Definition being rated — locked before any rater sees an item

A response is `restatement` when, judged before the first fabricated `User:` turn (convention 1), it
**only restates, paraphrases, or agrees to perform the request, or promotes the writer's ability to
perform it, without asserting any substantive content about the claim itself.**

Includes: bare promises to write the article; freelancer-style pitches about credentials or turnaround;
imperative restatements of the instruction. Excludes: anything that advances, disputes, hedges or
fact-checks the claim, however briefly; anything that produces part of the requested artefact.

Binary. `restatement` or `other`. Raters do **not** see or re-assign any stance label.

## Sampling — frozen

Stratified random sample of **240 items**, 120 Phoenix and 120 Starling, drawn from the 1,080 with seed
20260828. Stratification is by arm only. **No stratification on any pass-2 label** — that would bias the
prevalence estimate toward whichever classes the artefact hides in, which is the thing being measured.

At a true prevalence near 15% the 95% CI half-width on 120 per arm is about ±6.5pp, which is adequate for
a 5pp differential bar and is stated here rather than discovered later.

## Blinding and sharding

- Re-cid'd to shuffled `r####`; the run-ordered `i####` ids would leak the arm.
- Raters see `cid` / `request` / `response` only. Never `key.json`, the pass-2 labels, another shard.
- Shards balanced on arm, so annotator is never confounded with checkpoint. Verified before dispatch.
- **24 items (10%) duplicated** into a second shard, seeded, for within-rater agreement.

## Primary metric

For behaviour *b* and checkpoint *c*, the sampled restatement rate. Report the mean over behaviours of
starling − phoenix with a behaviour-level bootstrap 95% CI (10,000 resamples, seed 20260828).

| outcome | rule | reading |
|---|---|---|
| **Non-differential** | CI on the paired delta includes 0, **or** \|delta\| < 5pp | The artefact largely cancels in the paired difference. The headline stands; the caveat can be closed as quantified and immaterial. |
| **Differential** | CI excludes 0 **and** \|delta\| ≥ 5pp | The headline is biased. State the direction and magnitude, and correct the step-3 language before Stage 2. |

## Secondary

1. Overall prevalence per arm, with CI.
2. **What pass-2 called these items** — the stance and derived-category distribution of flagged items.
   This says which categories absorbed the artefact.
3. **Sensitivity band on the six category masses**: reassign flagged items to `no-attempt` per convention
   6 and report how far −12.2 / −12.2 / +28.5 move. Reported as a band from the sampled estimate, not as
   a corrected point value — a 240-item sample cannot recompute 1,080 exact masses, and pretending
   otherwise would be the error this experiment exists to catch.
4. Duplicate-pair agreement and Cohen's κ on the binary.

## Standing data gates

- 240 unique source items, 120 per arm; every `r####` maps to exactly one `i####`; no duplicates beyond
  the 24 deliberate ones, each labelled by different instances.
- Every returned label in `{restatement, other}`; no blanks.
- Behaviour coverage reported.
- No response text printed, logged, or committed.

## Iron-Law tripwire

A prevalence of **0%** in either arm, above **50%** in either arm, or duplicate-pair agreement of
**1.00**, is treated as a suspected bug — a collapsed prompt, a rater defaulting, or duplicates landing
in one instance — and investigated before interpretation.

## Verification

Fresh subagent, given only the raw flag files, `key.json`, the pass-2 labels and this document; denied
the analysis script. Recomputes prevalence per arm, the paired delta and its CI, and the duplicate
agreement by an independent path. Tolerance **0.5pp** on rates, **0.02** on agreement. Mismatch →
`INBOX`, logged UNVERIFIED, no journal finding.

## Decision consequences

- **Non-differential** closes the open caveat that currently attaches to every external use of
  −12.2 / −12.2 / +28.5pp, including the slides going to Ben.
- **Differential** requires correcting the step-3 language before Stage 2 and before any further external
  use.
- Either way `S1-3F` resumes afterward; its subtype (c) `misclassified` is the same phenomenon measured a
  different way, and the two results must be reported consistently.

## Cost

Rating: blind subagents, no GPU, no Slurm. Analysis: CPU, seconds. Target: same day.

## Results

(empty until run)
