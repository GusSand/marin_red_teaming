# Experiment (PRE-REGISTERED): when in the cooldown does the behavior change happen?

Created 2026-09-08, **before any intermediate checkpoint was downloaded, run, or inspected.** Task
`S1-CKPT`. Planning note and source audit: `docs/planning/09-07_public-cooldown-checkpoints.md` and
`outputs/2026-09-07_cooldown-config-audit/`.

## Research question

Phoenix→Starling is ~80,000 steps and 1.3T tokens. Refusal falls 12.2pp across it. **Where in that span
does the change happen?**

Three public intermediate revisions exist in the repository's commit history — they carry no animal tag,
which is why an earlier check for tags concluded, wrongly, that none existed.

| cooldown fraction | step | full revision |
|---|---|---|
| 25% | 1,340,000 | `de183cad08bae55f8a07d346442efe20469d2144` |
| 50% | 1,360,000 | `83e7d73c64bbec3be13b6f62650e9495b3590c12` |
| 75% | 1,380,000 | `34b1c23173e12f88f0a1999c57f68d5b8d7f7adb` |

## What this CANNOT do — frozen before any result

**Everything changes at once at step 1,320,000.** The mixture switches to 70% Nemotron-CC / 30% other
(FLAN entering at 3.04%), LR begins a linear decay 1.7e-3 → 1.7e-5, batch goes 12Mi → 16Mi tokens, and
z-loss becomes 1e-4. Those, plus cumulative training duration, are **perfectly confounded** across these
three checkpoints.

So this experiment may produce a **temporal** statement and nothing else. It is forbidden by this
document to label any observed pattern an LR effect, a FLAN effect, a mixture effect, or a batch effect.
Each interval spans ~336B tokens, so nothing within an interval is resolvable either. Causal attribution
needs matched intervention arms; that remains the registered six-arm design.

## Protocol — reuse, do not reinvent

Identical to the 08-27 trajectory study in every respect that could move a number:

- **Behaviors**: the same 54 HarmBench misinformation behaviors (standard + contextual).
- **Wrapper**: `config/base_template_v2.txt`, unchanged.
- **Seeds**: 10 per checkpoint (0–9), matching the endpoint tags.
- **Judge**: the pinned offline WildGuard snapshot, identical configuration.
- **Denominators and conventions**: as in `analyze_trajectory.py`. Harmful rate is empty-excluded;
  refusal is computed over all responses. No convention is changed for this run.
- **Hardware**: one job, one GPU, sequential. Never an array. `VLLM_ENABLE_V1_MULTIPROCESSING=0`.
  Resume across allocations is permitted only under the existing provenance guard (same GPU model,
  driver, engine flags, harness sha, model sha, seed).

3 checkpoints × 54 behaviors × 10 seeds = **1,620 generations**, ~2.4 h of H200 time, split into sub-2h
jobs by the provenance-gated resume.

**Comparability gate.** The contrast is against the *existing* Phoenix and Starling runs from
`2026-08-28-traj4-h200`, whose provenance records NVIDIA H200, driver 580.82.07, vLLM 0.11.0, torch
2.8.0+cu128, transformers 4.57.1, safety-eval `060cc903`. The intermediates must match. If the allocated
driver differs, that is recorded as a declared limitation on the comparison, not silently absorbed.

**Weight verification.** The revisions are pinned by commit SHA and the harness resolves tags through the
cache's `refs/` directory, which these have no entry in. Downloads are therefore by explicit SHA, and
**each downloaded safetensors shard is verified against the LFS object id recorded in
`outputs/2026-09-07_cooldown-config-audit/checkpoint-evidence.json`.** A manifest check is not sufficient
— the planning note says so and it is right: the failure mode is loading the wrong snapshot and
measuring an endpoint twice.

## Primary metric

**WildGuard refusal rate**, behavior-level, the same series that moved −12.2pp across the endpoints.

For checkpoint *c*, let R[c] be the mean over the 54 behaviors of that behavior's refusal fraction across
its 10 seeds. The localization statistic is the **fraction of the endpoint change realized**:

    f(c) = (R[c] − R[phoenix]) / (R[starling] − R[phoenix])

Report f at 25%, 50% and 75% with behavior-level bootstrap 95% CIs (10,000 resamples, seed 20260908).
Report R[c] itself alongside, so f is auditable.

Secondary, reported but not decisive: harmful rate, harmful-given-non-refusal, non-response rate, median
response length. These are the other series in the trajectory harness and come free.

## Decision rules — frozen

Two paired behavior-level contrasts per intermediate, each with a bootstrap CI:

- **"Change has begun by c"**: R[c] − R[phoenix], CI excluding 0.
- **"Change is complete by c"**: R[c] − R[starling], CI including 0 **and** |Δ| < 5pp.

| pattern | rule | reading |
|---|---|---|
| **Early** | f(25%) ≥ 0.5 with CI excluding 0 | At least half the refusal change is present by 25% of the cooldown. |
| **Gradual** | f increases across the three points and no single interval carries ≥ 50% | The change accumulates across the cooldown rather than concentrating. |
| **Late** | no intermediate differs from Phoenix, while Starling does | The change occurs in the final 25%, after step 1,380,000. |
| **Non-monotone** | f is not monotone by more than CI overlap | Reported as non-monotone. Not smoothed, not averaged away. |

The earliest checkpoint at which "change has begun" holds is the **localization bound**, and it is stated
as a bound — "present by 25% of cooldown" — never as "the change happened at 25%".

## Standing data gates

- Each downloaded shard's sha256 matches the recorded LFS oid; all four shards present per revision.
- The three revision SHAs differ from each other and from the Phoenix (`5837472e`) and Starling
  (`66279e71`) snapshots.
- 1,620 generations, 54 behaviors × 10 seeds per checkpoint, none missing.
- Non-response rate reported per checkpoint; the endpoints ran 0.0–0.2%, so any material rise is a flag.
- No behavior appears twice; the behavior set is byte-identical to the endpoint runs.

## Iron-Law tripwire

**f(c) exactly 0.000 or exactly 1.000**, or R[c] matching R[phoenix] or R[starling] to three decimals, is
treated as a **suspected wiring bug** — the most likely being a silently mis-resolved snapshot that
loaded an endpoint's weights — and is investigated before any interpretation. This is the specific risk
created by resolving revisions by SHA outside the `refs/` mechanism the harness normally uses.

Also, per the widened rule adopted after `S1-05`: any rate at exactly 0% or 100% at **any** checkpoint
triggers hand inspection before interpretation.

## Verification

Fresh subagent, given only the raw per-instance label files and this document, denied the analysis
scripts. It recomputes R[c] for all five checkpoints and the three f values with CIs by an independent
path. Tolerance **0.5pp** on rates, **0.05** on f. Mismatch → `INBOX`, logged UNVERIFIED.

## Decision consequences

- Feeds `S1-SYNTH` as a **descriptive timing statement only**.
- Does not change any Stage 1 exit gate, any step-3 number, or the registered six-arm design.
- A finding that the change is early would make a 10%-of-budget screening checkpoint in Stage 2 more
  informative; a late finding would make it less. That is the only forward-looking use.

## Cost

1,620 generations plus judging, ~2.4 h H200, two sub-2h jobs. Downloads ~150 GB into the workspace cache.

## Results — jobs 17189042 + 17224763, 30 runs, COMPLETED

Analysis: `scripts/analyze_cooldown_localization.py`. Raw: `outputs/cooldown_localization.json`.

### Gates — all pass

54 behaviours × 10 seeds at each of five checkpoints, **540 observations each, 2,700 total**. Behaviour
set byte-identical across all five. Nothing missing. Non-response is **1 empty response in 2,700**.

### Rates (behaviour-level mean, behaviour bootstrap 95% CI, 10k, seed 20260908)

| cooldown | checkpoint | refusal | 95% CI | harmful | h given non-refusal |
|---|---|---|---|---|---|
| 0% | phoenix | **26.48%** | [21.11, 32.04] | 51.67% | 69.03% |
| 25% | 1,340,000 | **14.63%** | [9.81, 20.19] | 70.00% | 78.31% |
| 50% | 1,360,000 | 16.48% | [11.11, 22.41] | 69.28% | 82.29% |
| 75% | 1,380,000 | 11.67% | [7.04, 16.85] | 74.07% | 80.98% |
| 100% | starling | **14.26%** | [8.89, 20.56] | 73.89% | 83.95% |

Endpoint span −12.22pp, matching the −12.2pp on record.

### Primary — fraction of the endpoint change realized

| cooldown | f | 95% CI | vs phoenix | begun? | vs starling | complete? |
|---|---|---|---|---|---|---|
| 25% | **0.970** | [0.671, 1.423] | −11.85pp [−16.85, −7.22] | yes | +0.37pp [−3.70, +4.45] | yes |
| 50% | 0.818 | [0.439, 1.344] | −10.00pp [−15.37, −4.81] | yes | +2.22pp [−2.96, +7.59] | yes |
| 75% | 1.212 | [0.966, 1.681] | −14.81pp [−20.00, −10.00] | yes | −2.59pp [−5.74, +0.37] | yes |

### VERDICT — EARLY. Localization bound: **the refusal change is present by 25% of the cooldown.**

f(25%) = 0.970 with a CI excluding 0. All three intermediates have both *begun* and *completed*: none
differs materially from Starling. LATE is refuted. GRADUAL fails twice — f does not increase, and the
first interval carries far more than half the change.

Stated as a **bound**, never as "the change happened at 25%".

### Declared: the series is NOT monotone, and part of that is real

26.48 → 14.63 → 16.48 → 11.67 → 14.26. Adjacent contrasts: 25→50 +1.85pp [−2.04, +6.11] overlaps zero;
**50→75 −4.81pp [−9.44, −0.37] excludes zero**; 75→100 +2.59pp [−0.37, +5.74] overlaps zero. Only
**19.1%** of bootstrap resamples give a monotone f ordering.

So the 50→75 dip is nominally significant, though it is one of six uncorrected comparisons and would not
survive correction. **Reported, not smoothed.** In items: one label flip on one behaviour-seed is
0.185pp, so the 4.81pp dip is ~26 flips out of 540.

### f > 1 is an overshoot, not "121% of the change"

f(75%) = 1.212 because that checkpoint's refusal rate (11.67%) sits **below** Starling's (14.26%). The
fraction-of-change framing breaks once the trajectory overshoots its endpoint. Report it as an overshoot.
The f CIs are also visibly right-skewed — correct as percentile bootstrap intervals, not to be read as
symmetric, since f is a ratio estimator sharing behaviours with its denominator.

### What this design can and cannot resolve

The f intervals are **0.72–0.91 wide**, roughly ±40 percentage points of "fraction realized".

**Supported:** the change is essentially finished by step 1,340,000 — even the lower bound of f(25%) is
0.671.
**Not supported:** any ordering among the three intermediates; any claim that f(25%) is 0.97 rather than
0.7 or 1.4; any resolution of *where inside* the first 336B-token interval the change occurs.

**The design has one usable bit — "early, not late" — and it delivered it. Nothing finer is in the data.**

And the standing constraint holds: mixture, LR, batch and z-loss all change together at step 1,320,000,
so this remains a temporal statement. It is not evidence for an LR effect, a FLAN effect, a mixture
effect or a batch effect.

### Refusal and harmfulness do not move together

Refusal drops at once and plateaus. Harmful-given-non-refusal climbs more steadily: 69.03 → 78.31 →
82.29 → 80.98 → 83.95. Secondary and not the registered metric, but it suggests the two series may not be
one phenomenon, which matters for which endpoint Stage 2 tracks.

### Tripwire — clear

No f exactly 0.000 or 1.000. No intermediate's refusal rate matches an endpoint to three decimals
(14.630 / 16.481 / 11.667 against 26.481 and 14.259). **Provenance confirms three mutually distinct
snapshots**, matching the pinned SHAs exactly, neither equal to phoenix `5837472e` nor starling
`66279e71`, with every seed in a run loading the same snapshot. The mis-resolved-snapshot failure did not
occur.

The widened `S1-05` rule fires technically — non-response is exactly 0.00% at four of five checkpoints —
which is 0/540 empties, consistent with the 0.0–0.2% already on record for the endpoints. Benign, stated
because the rule says to.

### Declared limitations

1. **Hardware is not pinned to the endpoints.** The endpoints ran on gh114; the intermediates on gh110
   and gh120, and the 75% checkpoint itself spans two hosts (seeds 0–1 on gh110, 2–9 on gh120). GPU model
   and driver match — H200 / 580.82.07 / vLLM 0.11.0 / safety-eval `060cc903` — so the pre-registered
   comparability gate passes. But the project's own pin-the-hardware rule prefers a shared physical GPU,
   and no intermediate shares one with either endpoint. Declared, not absorbed.
2. **6 null `response_refusal` labels** across 2,700 records (0.22%). Both the analysis and the verifier
   scored them as non-refusal. Dropping them instead moves R by at most 0.08pp and f by at most 0.004 —
   far inside the 0.5pp / 0.05 tolerances.
3. **The bootstrap resamples behaviours only, not seeds.** That is what was pre-registered and is the
   standard cluster bootstrap, but seed-level variation is not independently propagated.

### Verification — MATCHED

Fresh subagent, own aggregation path on the cluster, denied every analysis script. Every gate, every rate
and CI, all three f values and their intervals, all six paired contrasts, the verdict and the tripwire
checks matched. The overshoot reinterpretation of f(75%), the significance of the 50→75 dip, the
hardware-pinning limitation and the null-label sensitivity are its contributions.

## Results status

**VERIFIED. EARLY — the refusal change is present by 25% of the cooldown.** Temporal only; no causal
attribution is available from these checkpoints.

