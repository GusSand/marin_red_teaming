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

## Amendment 2026-09-07 — a rater-validity gate, frozen before any further labels exist

The first third-rater pass used **Gemini Flash** and **failed as an instrument**. It passed every gate
this document had — 150 rows, exact header, no duplicates, no foreign cids, all labels in vocabulary —
and still measured nothing. That is a gap in the gates, not a surprise about the model.

**Naming discipline:** the failed rater is **Gemini Flash**, not "Gemini". Attributing a null to a model
family when the small fast variant was used would be wrong, and the write-up says Flash everywhere.

gs157 is running a **Gemini Pro** pass. The gate below is frozen **before those labels exist**, so it
cannot be tuned to whatever comes back.

### Hard precondition — a rater's labels must carry item-level information

Before any rater's labels enter any statistic:

**Permutation test.** Compute the rater's agreement with the primary labels. Then shuffle the rater's own
label vector across items ≥ 10,000 times and recompute. **Require the observed agreement to exceed the
95th percentile of that null** — equivalently p < 0.05.

Rationale: a rater that ignores items and answers from a fixed marginal produces exactly the observed
distribution and exactly chance agreement. No other gate detects that, because every *sheet-level* check
passes. Gemini Flash scored **p = 0.377**: 38% of random reshuffles of its own labels matched the primary
rater at least as well as its real labels did.

**Failing this gate means the labels are not projected into any downstream statistic**, and the pass is
recorded as a failed instrument rather than as a dissenting opinion.

### Secondary red flag — independence from the treatment variable

Report χ² of the rater's label against **arm**, conditional on the primary rater's class. The slice is
balanced 25 per subtype per arm, so a rater tracking content should show no arm dependence within a
primary class.

Rationale, and the reason this is now explicit: Gemini Flash was null on the construct (χ² 2.71, n.s.
against the primary class) but **not** null on the arm — `unqualified` share 0.573 Phoenix vs 0.853
Starling, +28.0pp, χ² 14.52, significant. **A rater that is noise on the construct but structured on the
treatment is worse than noise: it manufactures an apparent arm effect from nothing.** Its projected share
of 0.8368 was that artifact, and it pointed the same way as the primary result — the most dangerous
direction to be wrong in.

A significant arm dependence is reported as a confound whether or not the permutation gate passes.

### Standing constraint is unchanged

Still a blinded sensitivity analysis. `S1-3F` stays closed as **MIXED** whatever any rater returns. No
"two of three" majority is treated as truth — and the Flash pass is a reminder that a majority can be
manufactured by a rater that is not reading.

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
