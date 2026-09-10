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

**Status: UNVERIFIED** — independent reproduction pending.

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

**Frozen consequence, applied:** keep `P0` as the recorded procedure and label every interval in this
project as **conditional on the seed draw**. No new candidate is invented here; that is what the plan
forbids and the prohibition is doing its job.

### The bar was mis-specified, and that is not self-corrected here

`P1` is calibrated by any reasonable reading: six of its eight cells lie between 4.8% and 7.1%. It fails
only because one cell rejected 0 of 126 times, under a 2.0% floor.

**A two-sided bar was the wrong instrument.** For an interval procedure, over-coverage is a loss of power;
under-coverage is a false claim. They are not symmetric errors and should not share a rejection rule. That
is a design error in this preregistration, made by the agent that wrote it.

It is **not** repaired by re-running with a one-sided bar. Choosing the bar after seeing which candidates
clear it selects on the outcome — the same failure the plan explicitly guards against one paragraph above.
The decision is escalated as **`IN-008`**: either Gus approves adopting `P1`, or a successor experiment
pre-registers a one-sided bar **before** looking at these rates again. Until then `P0` stands as recorded
and every interval carries the conditional-on-seeds label.

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

**`S1-FORMAT` — the predicted case.** DOES NOT CARRY stands: `document_open` still spans zero and is
nowhere near the +40pp CARRIES bar. But the recorded **"well-powered null, MDE 4.34pp"** does not survive.
The interval widens from 5.92pp to 15.11pp, so the minimum detectable effect is roughly **11pp**, not
4.34pp. The verdict was never close enough for this to matter — but the *precision* claim attached to it
was overstated and is corrected here. **This was written down as the expected outcome before the run.**

**`S1-05B` — the honest limit.** At **3 seeds** `P1` has 2 degrees of freedom and returns [+58.34, +241.66]
against `P0`'s [+137.04, +162.35]. The verdict does not flip — both exclude zero — but the point estimate
of +1.50 constraints carries far less precision than recorded. As pre-registered, the correct statement is
**"not resolvable at this seed count"**, not a flipped verdict.

### What a reader should take from this

Every substantive conclusion in this project survives. **No direction reverses and no significance call
changes.** What was wrong is the *precision*: published intervals are roughly half their proper width, so
large effects were never at risk and narrow-interval claims — power, MDE, "well-powered null" — were.
The one such claim in the corpus has been corrected.
