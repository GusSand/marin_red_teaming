# Experiment (PRE-REGISTERED): is the project's interval procedure calibrated, and what changes if it isn't?

Created 2026-09-09, **before any candidate procedure has been run on any recorded contrast.** Task `S1-STATS`.

## Why this exists

`S1-PREFIX`'s verification found that the behaviour-level bootstrap used in every contrast in this project
resamples the 54 behaviours and **conditions on the seeds drawn**. It therefore propagates item-sampling
noise and none of the generation noise. Phoenix's per-seed harmful rate spans **31.48%–64.81%, sd 10.38pp**,
against a binomial-only 6.80pp, so the ignored component is the larger one.

Null calibration already run (`scripts/calibrate_behavior_bootstrap.py`, reproduced on two independent code
paths): on all **126 disjoint 5-vs-5 splits of phoenix against itself**, where the true difference is zero by
construction, the frozen procedure's CI excludes zero in **27.8%** of splits (refusal 34.9%) against a
nominal 5%.

**That finding is the motivation, not the hypothesis.** It is already observed and is not re-tested here.
What is pre-registered below is the choice of a replacement and the consequences for recorded verdicts.

## Research question

Which interval procedure is calibrated on this data, and which recorded verdicts change under it?

## Scope — which recorded contrasts are affected

**In scope** (a seed dimension exists and is averaged over before a behaviour-level bootstrap):

| experiment | contrasts | seeds per cell |
|---|---|---|
| `S1-TRAJ` `docs/results/08-27_misinfo_rvc/analysis.json` | 7 Holm-corrected | 10 (kestrel/ocelot 3) |
| `S1-CKPT` `outputs/cooldown_localization.json` | 3 checkpoint contrasts + `f` | 10 |
| `S1-05B` `docs/results/09-08_benign_twins_v2/twin_grades_v2.json` | Δ constraints met | **3** |
| `S1-FORMAT` `docs/results/09-08_format_carryover/format_carryover.json` | 5 measures | 10 |
| `S1-PREFIX` `docs/results/09-08_prefix_framing/prefix_framing.json` | 2 contrasts + `f` | 5 |

**Out of scope, and this is a reasoned exclusion rather than an omission.** `S1-3D`, `S1-3F`, `S1-3F-ADJ`,
`S1-STANCE-GAP` and the `IN-002` spot-check are single-pass rater and label analyses: one observation per
item, no seed dimension, nothing averaged away. For those the item-level bootstrap resamples the only
sampling unit there is, which is correct. They are not re-derived. If any of them is later found to average
over repeated generations, it moves in scope and this line is what says so.

## Candidate procedures

| id | procedure |
|---|---|
| `P0` | **incumbent** — percentile bootstrap over behaviours, conditioning on the seed draw |
| `P1` | seed as the unit — paired *t* interval over per-seed rates |
| `P2` | two-way cluster bootstrap — resample behaviours **and** seeds independently, recompute |
| `P3` | variance components — estimate behaviour and seed variance, build a Wald interval from both |

`P0` is carried only as the reference line. It is not eligible to win.

## Calibration protocol

**Selection set:** phoenix, 10 seeds, all 126 disjoint 5-vs-5 splits, on both the harmful and refusal series.
True difference is zero by construction, so every rejection is a false positive.

**Confirmation set, never used for selection:** starling, deeper-starling and jellyfish, same construction.
Choosing and evaluating on the same tag would select a procedure fitted to phoenix's particular seed noise.

**Acceptance bar — frozen.** A procedure passes only if its empirical type-I error falls inside
**[2.0%, 12.0%]** for a nominal 5%, on **both** series, on **both** the selection and the confirmation sets.
The band is deliberately wide: the 126 splits share seeds and are **not independent**, so the binomial
Monte-Carlo error of 1.9pp understates the true uncertainty by an unknown factor. A narrow band would be
false precision.

**Tie-break, frozen before any procedure is run.** Among passing candidates, take the one with the
**narrowest median interval width** on the `S1-PREFIX` `delivery − none` contrast — that is, the most power
subject to being calibrated. Written down now so a procedure cannot be chosen after its intervals are seen.

**If no candidate passes:** report that plainly, keep `P0` as the recorded procedure, and label every
interval in this project as conditional on the seed draw. **Do not invent a fourth candidate after seeing
these results** — that would be selecting a procedure on the outcome it produces. A new candidate needs its
own preregistration.

## Re-derivation and the verdict-flip rule — frozen

Apply the winning procedure to every in-scope contrast. Each recorded verdict is then classified:

| class | rule |
|---|---|
| **UNCHANGED** | the experiment's own decision rule resolves the same way under the corrected interval |
| **FLIPPED** | it resolves the other way |
| **WEAKENED** | direction and point estimate hold, but a threshold, power or precision claim no longer does |

`S1-FORMAT` is the expected `WEAKENED` case: its "well-powered null" and 4.34pp minimum detectable effect
were both computed from a `P0` standard error. A null argued from a narrow interval is exactly what this
defect breaks. **Predicted here, before running, so that finding it cannot be presented as a discovery.**

`S1-05B` is the hardest case and its limit is stated now: **3 seeds**. `P1` has 2 degrees of freedom there,
so its interval will be very wide regardless of the truth. If the winning procedure cannot separate anything
at 3 seeds, the correct output is "not resolvable at this seed count", not a flipped verdict.

Every reclassification gets a correction line in `docs/research_journal.md` and, where it changes what a
reader should believe, in the living report. **Original numbers are never overwritten** — they stand as the
registered values with the corrected interval reported beside them.

## Success criteria

1. A procedure is selected by the frozen bar and tie-break, or "none passes" is reported.
2. Every in-scope contrast has a corrected interval next to its recorded one.
3. Every in-scope verdict is classified UNCHANGED / FLIPPED / WEAKENED by its own decision rule.

## Tolerance

Corrected intervals reported to 2 decimal places in pp. Calibration rates to 1 decimal place. A verdict
changes class only when its decision rule resolves differently — never on a marginal shift in a bound.

## Verification

Fresh verifier, given the raw label directory, this document, and the recorded result JSONs; denied
`scripts/calibrate_behavior_bootstrap.py` and whatever re-derivation script this task writes. It
re-implements the winning procedure and recomputes the calibration rates and at least the `S1-FORMAT` and
`S1-PREFIX` corrected intervals. Tolerance as above.

## Cost

CPU only. No GPU, no new generation, no judge. Runs on the Torch login node against labels already
preserved in `/scratch/gs157/marin-misinfo-labels`. Minutes.

## Results

Run 2026-09-09, CPU only on the Torch login node. Evidence:
`docs/results/09-09_procedure_selection/procedure_selection.json` and `rederived_intervals.json`.
Scripts: `scripts/select_inference_procedure.py`, `scripts/rederive_intervals.py`.

**Status: VERIFIED — REPRODUCED WITH CONCERNS** (2026-09-09). A fresh verifier, denied all three analysis
scripts, wrote four implementations from the preregistration and matched **32 of 32 calibration cells**
within the 3.0pp tolerance (max |Δ| 1.6pp; `P1` and `P3` are closed-form and matched to the digit at all 16
of their cells, so the two implementations are the same estimator rather than two things that happen to
agree). Spot-check contrasts matched to **0.19pp** on any bound. It independently recomputed
`document_open` end to end from raw items and reproduced the SE inflation.

It also found a defect in this document, which is recorded below rather than quietly fixed. **`S1-05B`'s
re-derivation is not yet independently confirmed** — see the open item at the end.

### Selection: NO CANDIDATE PASSES

Type-I error over the 126 disjoint 5-vs-5 splits at each tag. Nominal 5%.

| tag | series | `P0` incumbent | `P1` seed-level t | `P2` cluster boot | `P3` var. comp. |
|---|---|---|---|---|---|
| **phoenix** *(selection)* | harmful | 27.8% | 4.8% | 2.4% | 4.0% |
| **phoenix** *(selection)* | refusal | 34.9% | 5.6% | 6.3% | 6.3% |
| starling | harmful | 10.3% | 7.1% | 0.0% | 1.6% |
| starling | refusal | 15.9% | 7.1% | 0.8% | 0.8% |
| deeper-starling | harmful | 2.4% | 5.6% | 0.0% | 0.0% |
| deeper-starling | refusal | 7.1% | **0.0%** | 0.0% | 0.0% |
| jellyfish | harmful | **40.5%** | 4.8% | 5.6% | 5.6% |
| jellyfish | refusal | 30.2% | 5.6% | 5.6% | 7.9% |

Against the frozen `[2.0%, 12.0%]` bar: **all four fail.** `P0` fails on the high side, at up to 40.5%.
`P1`, `P2` and `P3` each fail on the **low** side — too conservative in at least one cell.

**The frozen rule contradicts itself, and that is the finding.** Found in verification. This document
states that `P0` "is not eligible to win" — and its no-winner branch then hands the win to `P0`. The rule
cannot be executed as written without violating its own eligibility clause. So it is **not** executed as
written.

**Recorded outcome: the procedure decision is OPEN.** Not "keep `P0`", not "adopt `P1`".

**Action taken instead, which requires no selection at all:** report `P0` and `P1` side by side on every
in-scope contrast, and **rest each verdict on the wider of the two intervals.** This is monotonically a
weakening of every claim — it cannot manufacture a finding — so it is not exposed to the
selection-on-outcome objection that blocks re-running with a friendlier bar. It is available immediately
and it is what the classification table below does.

### The bar was mis-specified, and that is not self-corrected here

`P1` is calibrated by any reasonable reading: six of its eight cells lie between 4.8% and 7.1%. It fails
only because one cell rejected 0 of 126 times, under a 2.0% floor.

**A two-sided bar was the wrong instrument.** For an interval procedure, over-coverage is a loss of power;
under-coverage is a false claim. They are not symmetric errors and should not share a rejection rule. That
is a design error in this preregistration, made by the agent that wrote it.

**The floor is also below the estimator's own resolution.** With 126 splits the achievable rates near the
bottom are 0.00%, 0.79%, 1.59%, 2.38% — **nothing can land in [1.6%, 2.4%)**, so clearing a 2.0% floor
requires at least 3 rejections in 126. Verification's simulation puts the per-cell standard deviation of a
126-split type-I estimate at **1.4–1.9pp**, so the floor sits entirely inside the estimator's noise: a
procedure with exactly nominal coverage fails it by chance a meaningful fraction of the time. This document
correctly warned that the 1.9pp binomial error understates the uncertainty, and then set a floor 2.0pp
above zero anyway.

It is **not** repaired by re-running with a one-sided bar. Choosing the bar after seeing which candidates
clear it selects on the outcome — the same failure the plan explicitly guards against one paragraph above.
The decision is escalated as **`IN-008`**: either Gus approves adopting `P1`, or a successor experiment
pre-registers a one-sided bar **before** looking at these rates again.

**The tie-break never fired.** No candidate passed, so the `S1-PREFIX` median-width criterion was never
applied. Stated plainly so it is not mistaken for a step that ran.

**`P1` was underspecified at freeze time.** This document says "seed as the unit — **paired** *t* interval".
The calibration design compares disjoint seed halves, where pairing is impossible, so the procedure actually
evaluated there is **Welch**. That refinement was made after the freeze. It is necessary and benign —
verification checked Welch against pooled-variance and no cell moved by more than 2.3pp and no conclusion
changed — but it is recorded here rather than left standing as though "paired t" had been the thing tested.
The paired form is calibrated separately in the gap check below.

### Re-derivation — ADDED analysis, clearly labelled

The frozen re-derivation step is conditional on a winning procedure, and there is none. So the table below
is a **sensitivity, not a verdict**: what each candidate gives beside the recorded `P0` value. No interval
here is canonical. **The recorded numbers stand.**

Across **20 in-scope contrasts** spanning `S1-TRAJ`, `S1-CKPT`, `S1-05B`, `S1-FORMAT` and `S1-PREFIX`:

**0 of 20 disagree between `P0` and `P1` on whether the interval excludes zero.**

| contrast | Δ | `P0` (recorded) | `P1` | zero excluded? |
|---|---|---|---|---|
| harmful: starling − phoenix | +22.22pp | [+17.04, +27.78] | [+15.70, +28.74] | both yes |
| refusal: starling − phoenix | −12.22pp | [−17.59, −7.04] | [−18.50, −5.94] | both yes |
| harmful: deeper-starling − phoenix | +22.04pp | [+16.48, +27.78] | [+13.28, +30.79] | both yes |
| refusal: cooldown-1340000 − starling | +0.37pp | [−3.89, +4.44] | [−2.98, +3.72] | both no |
| harmful: delivery − none | +29.63pp | [+21.11, +37.78] | [+13.95, +45.31] | both yes |
| harmful: deflect − none | +5.93pp | [−3.70, +15.93] | [−14.86, +26.71] | both no |
| `document_open` (S1-FORMAT primary) | +0.93pp | [−2.22, +3.70] | [−6.63, +8.48] | both no |
| `assistant_preamble` | +16.67pp | [+12.59, +20.74] | [+5.69, +27.64] | both yes |
| `single_block` | −17.41pp | [−24.44, −10.37] | [−23.66, −11.16] | both yes |
| S1-05B constraints ×100 | +150.00 | [+137.04, +162.35] | [+58.34, +241.66] | both yes |

### Classification of the in-scope verdicts

| experiment | class | note |
|---|---|---|
| `S1-TRAJ` | **UNCHANGED** | all six contrasts keep their exclude-zero decision |
| `S1-CKPT` | **UNCHANGED** | all six; the three "differs from Phoenix, not from Starling" calls hold |
| `S1-PREFIX` | **UNCHANGED** | SUFFICIENT holds; the control still does not fire |
| `S1-FORMAT` | **UNCHANGED verdict, WEAKENED power claim** | see below |
| `S1-05B` | **UNCHANGED verdict, NOT RESOLVABLE at 3 seeds** | see below |

**`S1-FORMAT` — the predicted case, recomputed end to end in verification.** DOES NOT CARRY stands:
`document_open` still spans zero and is nowhere near the +40pp CARRIES bar. But the recorded
**"well-powered null, SE 1.547pp, MDE 4.34pp, +40pp bar 25.8 SEs away"** does not survive.

| quantity | recorded | corrected |
|---|---|---|
| SE | 1.547pp | **3.338pp** (2.17x) |
| MDE at 80% power | 4.34pp | **9.44pp** |
| distance to the +40pp bar | 25.8 SEs | **11.9 SEs** |

**And the mechanism is visible in the raw data: `starling` seed 5 shows `document_open` at 31.48%, against
0–3.7% at eight of the other nine starling seeds.** One seed carries the entire measure. `P0` is
structurally blind to that, which is exactly why it reported a tight interval. **The null was "well-powered"
only under an assumption the data itself contradicts.** The verdict was never close enough for this to
change it — but `docs/decisions.md` carries the precision claim as a recorded line, and it is corrected
there by a new dated line rather than by editing the original.

**This was written down as the expected outcome before the run.** The single-seed mechanism was not, and is
verification's find.

**`S1-05B` — the honest limit, and the one item still open.** At **3 seeds** `P1` has 2 degrees of freedom
and returns [+0.58, +2.42] constraints against `P0`'s [+1.37, +1.63]. The verdict does not flip — both
exclude zero — but the recorded ±0.13-constraint precision does not survive. As pre-registered, the correct
statement is **"not resolvable at this seed count"**, not a flipped verdict.

**Not yet independently confirmed.** The verifier could not locate the per-seed constraint counts, which are
not in `twin_grades_v2.json`, and correctly declined to close the item rather than assume. The raw grades do
exist, at `benign_twins_v2/twins.jsonl` and `benign_twins_v2/raw/responses.jsonl`; the path has been handed
over and the recompute is pending. **`S1-05B` stays UNVERIFIED in this task until it returns.**

### ADDED gap check: the paired variant, which the registered calibration did not cover

The registered calibration compares **disjoint** seed halves, an unpaired contrast. But every recorded
contrast is applied **paired** — seed *s* is the same sampling seed on both sides. The paired variant was
therefore never calibrated. Closing that (`scripts/calibrate_paired_variant.py`) by pairing seed *i* of one
half with seed *i* of the other: an **artificial** pairing of independent seeds, the worst case, since the
pairing carries no information.

| tag | series | `P0` | `P1` | `P2` | `P3` |
|---|---|---|---|---|---|
| phoenix | harmful | 27.8% | 7.9% | 4.0% | 7.1% |
| phoenix | refusal | 34.9% | 9.5% | 9.5% | 10.3% |
| starling | harmful | 10.3% | 2.4% | 0.0% | 1.6% |
| starling | refusal | 15.9% | 4.0% | 1.6% | 3.2% |
| deeper-starling | harmful | 2.4% | 7.1% | 0.0% | 0.0% |
| deeper-starling | refusal | 7.1% | **0.0%** | 0.0% | 0.0% |
| jellyfish | harmful | 40.5% | 6.3% | 7.9% | 8.7% |
| jellyfish | refusal | 30.2% | 3.2% | 6.3% | 7.1% |

`P1` paired sits in [2.4%, 9.5%] in **seven of eight** cells and fails, again, only at deeper-starling
refusal. The paired form runs slightly more liberal than the unpaired (7.9 / 9.5 at phoenix against
4.8 / 5.6) and still never exceeds 10.3%. **The conclusion is unchanged in the configuration that is
actually used.**

### Why `P0` fails, confirmed: its error rate tracks seed instability exactly

Per-seed spread by checkpoint:

| tag | harmful sd | refusal sd | `P0` type-I (harmful / refusal) |
|---|---|---|---|
| jellyfish | **13.57pp** | 10.62pp | **40.5% / 30.2%** |
| phoenix | 10.38pp | 10.66pp | 27.8% / 34.9% |
| starling | 5.55pp | 4.79pp | 10.3% / 15.9% |
| deeper-starling | **4.43pp** | 4.72pp | **2.4% / 7.1%** |

`P0`'s false-positive rate is **monotone in the seed standard deviation it ignores**, from 2.4% where seed
noise is smallest to 40.5% where it is largest. That is not a correlation found by searching; it is the
predicted signature of the diagnosed defect, and it is the strongest internal evidence that the diagnosis
is right rather than a coincidence of one checkpoint.

It also explains the single stubborn cell. At deeper-starling, seed noise is smallest, so `P0` is nearly
calibrated (2.4%) and the seed-aware procedures — which add a seed term that is genuinely near zero there —
become conservative. **The one cell that fails the bar is the one where the incumbent needed no fixing.**

### Incidental substantive finding: cooldown roughly halves sampling variance

Phoenix's harmful rate varies **sd 10.38pp** across seeds; Starling's **5.55pp**, deeper-starling's
**4.43pp**. Refusal shows the same pattern, 10.66pp → 4.79pp → 4.72pp. The cooled-down checkpoints are
about **twice as consistent** run to run as the base checkpoints.

This is a by-product of a methods task and has **not** been pre-registered or tested — no interval, no
verdict, and it must not be quoted as a result. But it belongs in Stage 1's picture: the change from
Phoenix to Starling is not only a shift in the mean, it is a **tightening of the distribution**. Flagged
for `S1-SYNTH` as a hypothesis worth its own preregistration, not as a finding.

### Four limits on the calibration evidence itself, from verification

1. **The eight cells are four correlated seed-draws, not eight independent experiments.** All 126 splits in
   a cell are re-partitions of *one* draw of 10 seeds, not 126 experiments; and harmful and refusal within a
   tag come from the same responses. Effective replication is four checkpoints from one training run, on one
   prompt set, under one judge.
2. **The "confirmation set" is less independent than the framing implies** — same 54 prompts, same judge,
   same hardware, checkpoints from one run. It guards against fitting to phoenix's particular seed noise. It
   does not establish generalisation.
3. **`P1` is not certified calibrated, only not grossly anti-conservative.** Verification's simulation
   (200 synthetic null datasets per cell, per-seed additive shift — *synthetic, not a measurement*) puts
   `P1`'s true type-I at 4.2–4.7% with per-cell estimator sd 1.4–1.9pp, which makes deeper-starling's 0.0%
   about 2.3 sd low in one of eight cells: unremarkable. But that null model is close to the model `P1`
   assumes, so it establishes the estimator's noise level, not calibration against whatever real dependence
   the generations carry. Per-cell uncertainty is about ±2pp. **That is enough to prefer `P1` over a
   procedure running at 28–40%. It is not enough to quote `P1` as calibrated to a couple of points.**
4. **Unlabeled rows were not re-examined for this exercise.** 23 of 2,160 behaviour-seed cells carry no
   WildGuard label and are coded 0 on both series; **21 of 23 are jellyfish, 10 of them in jellyfish seed 2
   alone.** That is bounded for the *contrasts* in `sensitivity_missing_labels.json`, but jellyfish's
   between-seed dispersion is a direct input here. Excluding the 16 affected behaviours moves jellyfish
   harmful sd from 13.57pp to 12.00pp and jellyfish refusal `P1` from 5.6% to 3.2%. Nothing changes; the
   line is carried rather than omitted.

### What a reader should take from this

Every substantive conclusion in this project survives. **No direction reverses and no significance call
changes.**

But "0 of 20 flip" is the wrong headline on its own, and verification was right to push on it. The accurate
version:

> **0 of 20 direction verdicts flip. At least 2 of 20 precision or power claims weaken, one of them a
> recorded line in the decision log. Every interval in the in-scope set is roughly half the width it should
> be** — the `P0`/`P1` median width ratio is 2.16x on harmful and 2.47x on refusal across the null splits,
> independently corroborated by the 2.17x measured directly on `S1-FORMAT`.

Any claim shaped **"narrow interval, therefore null"** or **"N standard errors from the bar"** is
width-dependent, and those do change. Claims shaped "this effect is large and in this direction" do not.
