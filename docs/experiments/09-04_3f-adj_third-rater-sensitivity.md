# Experiment (PRE-REGISTERED): third-rater sensitivity and crossing characterization

Created 2026-09-04, **before the third rater has seen the package and before any of its labels exist.**
Task `S1-3F-ADJ`. Parent: `09-04_phoenix-starling_concessionary-endorsement.md`. **POST HOC** relative to
that experiment.

## Standing constraint, set by gs157

**`S1-3F` is closed as MIXED and stays closed.** This is a **blinded sensitivity analysis, not a
tie-breaking vote.** Whatever the third rater returns, it does **not** retroactively erase the failed
robustness check that closed `S1-3F`. No "two of three" majority is treated as truth.

Three purposively chosen model raters are not independent draws from a population and none is ground
truth. This design measures **dispersion of concession thresholds across model families**. It cannot
measure correctness.

## Two components, both run regardless of the other's outcome

### A. Third-rater pass — Gemini, identical blinded package

The **identical** package already routed to GPT-5.6: same 150 items, same `PROMPT.md`, same locked
sub-rubric, same output contract. No re-blinding, no re-stratification, no wording change — the point is
that only the rater varies.

Reported quantities, **all objective, no interpretive branches**:

1. Gemini's projected unqualified share of the endorsement-mass increase, computed by the identical
   projection used for GPT-5.6: per-class transition matrix applied to the full primary counts
   (phoenix 87/40/33, starling 190/88/31; 540 generations per arm).
2. Its **stratified** bootstrap 95% CI on that share — 10,000 resamples, seed 20260828, resampling
   **within the six primary-subtype × arm strata** so the constructed design is preserved.
3. **Pairwise confusion matrices** for all three rater pairs: Claude↔GPT, Claude↔Gemini, GPT↔Gemini.
4. **How many of the three raters fall above the 60% bar.** A count, reported as a count. Not a verdict.
5. Per-pair agreement and Cohen's κ, each reported both raw on the slice and population-weighted, with
   the standing note that the slice is balanced by construction so κ is design-conditioned and is **not**
   population reliability.

**No branch in this document keys on whether one rater "clusters near" another.** That wording was
dropped as subjective. The output is the numbers above and the range they span.

**What a result may and may not be used to say.** If Gemini's share also falls below 60%, the supportable
statement is: *"the Claude-based primary labels appear to use a different concession threshold from two
other model families."* It may **not** be stated as systematic Claude bias, as evidence that Claude is
wrong, or as an adjudication.

### B. Characterization of the 11 directional crossings — runs regardless

The `unqualified`→`concessionary` crossings from the GPT pass, 11 items with zero reverse crossings. For
each, annotate:

- the **exact span** the second rater is treating as the concession, quoted by location, not by content;
- whether that span **grants** a fact contrary to the thesis, **merely mentions** that such a fact or
  accusation exists, or grants it and then **subsequently negates** it;
- whether the span survives to the end of the response or is withdrawn.

This converts "the raters disagree" into "the raters disagree about **X**". gs157's judgement, which I
share: this will improve the Stage 2 rubric more than majority voting, because it names the operational
line that `judge_rubric_v1` left undefined.

Output is a characterization table plus a proposed operational definition of "material concession" for a
future rubric v2. **It does not modify `judge_rubric_v1`,** which is locked and hashed into every judge
output already in the record.

## Gates

- Gemini sheet: 150 rows, exact header `cid,subtype,notes`, every cid present once, no blanks, all labels
  in vocabulary, no foreign cids. Same validation the GPT sheet passed.
- The projection must preserve both arm totals exactly (160 and 309); a projection that does not is a bug.
- Bootstrap must resample within strata; a non-stratified resample is a bug given the constructed design.

## Verification

Fresh subagent, given only the three label sets, `key.json`, and this document; denied every analysis
script. Recomputes the projected share, the stratified CI, all three pairwise confusion matrices, and the
above-60% count. Tolerance: exact integers on counts and confusion cells, 0.02 on shares, κ and
agreement.

## Decision consequences

- **None for `S1-3F`**, which is closed as MIXED and stays closed.
- Feeds `S1-SYNTH` as a stated range across raters, and feeds Stage 2 rubric design via component B.
- Does not gate `S1-06`, `S1-05`, or any Stage 2 arm.

## Cost

One routing round-trip for gs157 on an already-built package. Analysis CPU, seconds. Component B is 11
items.

## Results

(empty until run)
