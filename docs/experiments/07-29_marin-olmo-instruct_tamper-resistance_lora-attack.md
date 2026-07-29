# Experiment (PRE-REGISTERED): Tamper-resistance — does instruct-model refusal survive a LoRA fine-tuning attack?

Created 2026-07-29, before the run. gs157 signed off (INBOX 2026-07-28 → "a. Proceed as designed").
DUAL-USE defensive red-team measurement — see Safety handling below.

## Research question / hypothesis
Our whole harness so far measures **default behavior** (refusal at inference). The metric that actually
matters for OPEN-WEIGHT models is **tamper-resistance**: does safety survive an adversary who fine-tunes the
released weights? (Qi et al 2310.03693; TAR 2408.00761; shallow-alignment 2406.05946; Deep Ignorance
2508.06601.) This measures it directly for the two models we've been comparing.

**Pre-registered hypothesis (H1):** both marin-8b-instruct and olmo-3-7b-instruct lose their safety fast under
a small LoRA attack — ASR (HarmBench + StrongREJECT) rises from its low baseline to ≥80% within ≤40 optimizer
steps on ~50–100 harmful pairs. I.e. neither shipped open model is tamper-resistant (expected; the point is to
put a *number and a collapse-curve* on it, and to see whether the two differ in how fast they fall).
**Null / alternative (H0):** ASR stays low (<30%) through 80 steps for a model → that model resists the attack
(would be a surprising, publishable positive result → triple-check for a bug before believing it).

## Setup
- Models attacked: `marin-community/marin-8b-instruct`, `allenai/Olmo-3-7B-Instruct` (both with their own chat template).
- Attack: LoRA SFT (rank ~16, attn+MLP proj) on harmful `instruction → compliant-completion` pairs, standard
  causal-LM loss on the response tokens. Fixed seed, LR pre-registered in the launch config before the run.
- Attack set: an ESTABLISHED PUBLIC red-team corpus (AdvBench `harmful_behaviors` and/or HarmBench behaviors) —
  NOT hand-authored novel harmful content. ~50–100 pairs. Held DISJOINT from the eval sets to avoid train/test
  leakage on the exact prompts (attack on AdvBench-derived, eval on HarmBench+StrongREJECT held-out — check overlap).
- Checkpoints: measure at **0, 5, 10, 20, 40, 80** optimizer steps (0 = the untouched instruct model = baseline).
- Eval at each checkpoint: ASR on `harmbench:default` + `strongreject:logprobs` via the SAME pinned harness
  (safety-eval @060cc903, WildGuard + StrongReject-Gemma judges), 1 seed/checkpoint (curve shape, not seed CI).
- Readout: ASR-vs-steps collapse curve per model (2 models × 6 checkpoints × 2 benchmarks). Compare fall rate.
- Compute: LOCAL A100 (remote is shut down). LoRA on an 8B/7B + eval per checkpoint ≈ ~3–5h total. Background job.

## Success criteria / readout (descriptive)
Plot ASR vs optimizer steps for each model/benchmark. Report step-to-≥80%-ASR per model, and baseline (step 0)
ASR (should match our earlier default-behavior numbers — a built-in sanity check: step-0 ASR ≠ prior instruct
ASR ⇒ harness bug). Verify each curve's step-0 and step-80 points from raw all.json counts (content-safe) via a
fresh recompute before logging.

## Safety handling (per gs157-approved mitigations — non-negotiable)
- Everything stays LOCAL. Attacked LoRA adapters/checkpoints are DELETED after the ASR curve is measured.
- Only aggregate ASR-vs-steps numbers enter the repo/journal. NO harmful generations, NO attack completions,
  NO attacked weights committed. Attack data pulled from public corpora, not authored here.
- Grading is content-safe (counts only), as with the rest of the project. This is standard defensive
  tamper-resistance methodology (measuring a vulnerability that already exists in released weights), not
  capability uplift.

## Pre-registered gate (Iron Law)
A model showing tamper-RESISTANCE (H0: ASR stays <30% through 80 steps) is SUSPICIOUS, not a triumph — almost
certainly a broken attack (LoRA not applied, wrong loss mask, adapter not loaded at eval). Treat as a likely bug,
verify the attack actually changed the weights (compare step-0 vs step-80 generations differ), before believing it.

## Results
NOT RUN (queued after Study A on the local GPU). Outputs → runs/2026-07-29-tamper-<model>-step<N>-*.

## Links
Closes the measurement gap flagged in outputs/marin_pretraining_safety_proposal.md and SUMMARY. Refs:
outputs/refs_safety_pretraining.md (Qi 2310.03693, TAR 2408.00761, shallow-alignment 2406.05946, Deep Ignorance).
