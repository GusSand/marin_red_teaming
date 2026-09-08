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

## Results

(empty until run)
