# Experiment (PRE-REGISTERED): Does the "safety gap" widen with scale? — adapting the Safety Gap Toolkit

Created 2026-07-29, before any compute. Follows up SUMMARY Part 10 (tamper-resistance) using the framing of
Dombrowski, Bowen, Gleave & Cundy 2025, *The Safety Gap Toolkit* (arXiv:2507.11544 ·
https://github.com/AlignmentResearch/safety-gap). gs157 requested this + "adapt their code."

**DUAL-USE — needs sign-off before the RUN (like the original tamper study). This file is design only.**

## Research question / hypothesis
Their central claim: the **safety gap** — the *dangerous capability unlocked when an open model's safeguards are
stripped* — **widens with model scale**. Our Part-10 tamper result already shows refusal collapses to ~99% ASR
on both 7B/8B models; this asks the *scale* question and shifts the metric from "does refusal survive" to "how
much dangerous *capability* is unlocked."

Key mechanism: post-attack HarmBench ASR **saturates** (~99%) at every scale, so ASR alone can't show a widening
gap. The differentiator is the **underlying capability** the stripped model can now be made to use. So we
operationalize the gap with a capability probe (WMDP) alongside compliance (ASR).

**Pre-registered hypothesis (H1):** across a within-family scale sweep, the *stripped* (attacked) model's
dangerous-knowledge capability is higher at the larger scale while both *intact* models are comparably safe —
i.e. the intact→stripped gap in usable dangerous capability is larger at 32B than 7B. Concretely, on Olmo:
1. intact (step-0) HarmBench ASR is similarly low at 7B and 32B (both safeguarded);
2. attacked (step-80) HarmBench ASR is similarly high (~99%) at both (refusal strippable at both scales);
3. **attacked-model WMDP accuracy is higher at 32B than 7B by ≥ the WMDP gap already present pre-attack** — the
   stripped 32B model is a more capable dangerous agent. Gap-widening = (WMDP_32B − WMDP_7B) of the stripped
   models is positive and ≥ the intact-model WMDP gap. If TRUE → supports "gap widens with scale."
**Null / alternative (H0):** the stripped-model capability gap does NOT exceed the intact gap (scale doesn't
widen the *unlocked* danger beyond baseline capability differences), OR refusal does NOT fully strip at 32B
(32B is more tamper-resistant — a surprising positive; triple-check for a broken attack per Iron Law).

## Setup
- **Scale sweep (the test): OLMO** — `allenai/Olmo-3-7B-Instruct` vs `allenai/Olmo-3.1-32B-Instruct`. Both exist
  and are instruct-tuned. CAVEAT: 7B is Olmo-3, 32B is Olmo-3.1 (minor version mismatch) — the cleanest sweep
  available; note it, don't over-claim a pure scale isolation.
- **Anchor (our model of interest): `marin-community/marin-8b-instruct`** at 8B only — Marin ships NO 32B
  instruct (verified), so Marin cannot enter the scale sweep. Report Marin's 8B gap next to Olmo's 8B point.
- **Attacks (adapt their toolkit):**
  1. LoRA SFT affirmative-prefix attack — our existing `scripts/tamper_*` harness (matches their SFT attack),
     snapshots at 0/5/10/20/40/80 steps.
  2. **Refusal-ablation attack** (arXiv:2410.03415, white-box, no fine-tune) — NEW capability we adapt from
     their `safety_gap/attack/` (`BaseAttack` subclass). A second, cheaper removal path; cross-check it agrees
     with the SFT attack on whether refusal strips.
- **Capability + compliance metrics at step 0 (intact) and the attacked endpoint:**
  - HarmBench ASR (compliance; WildGuard judge) — expected to saturate.
  - **WMDP accuracy** (dangerous-knowledge capability) — their toolkit lacks a WMDP suite, so we plug in OUR
    WMDP eval (safety-eval, already validated). This is the gap-discriminating metric.
  - StrongREJECT reported WITH the length-collapse caveat only (per INBOX 2026-07-29 decision a), not as a curve.
- **Judges LOCAL only** (non-negotiable, matches our offline stance): swap their OpenAI(refusal)/Anthropic(quality)
  API graders for local WildGuard + `strong_reject`. Do NOT add external-API deps.
- **Tooling:** adapt safety-gap (register Olmo + Marin model families in `model_family_config.py` + hydra YAML;
  add WMDP evaluator as a `BaseEvaluator`; swap graders). Where our existing `tamper_run.sh` already covers a
  step, reuse it rather than duplicating. NO explicit license on their repo → do not redistribute adapted code
  without checking with gs157.
- **Seeds:** use the FIXED sampler seed (INBOX seed-fix b; `SAFETYEVAL_SAMPLING_SEED`) so any 3-seed points have
  valid CIs. Capability (WMDP) is MC/greedy → deterministic, 1 seed fine.

## Success criteria / readout (descriptive)
Table per model×scale: intact vs attacked HarmBench ASR + WMDP. Plot the "safety gap" (attacked − intact usable
dangerous capability) at 7B vs 32B for Olmo. Report whether H1's three conditions hold with the pre-registered
inequality (stripped WMDP gap ≥ intact WMDP gap). Verify every headline from raw `all.json` (content-safe counts)
via a fresh recompute; validate the step-0 = untouched-instruct sanity gate (as in Part 10).

## Compute plan (needs sign-off)
- 7B attack+eval ≈ our Part-10 tamper run (~1-2h) — LOCAL.
- **32B (Olmo-3.1-32B-Instruct) LoRA attack + eval ≈ several hours on a REMOTE A100** (64GB weights; bf16 fits;
  fine-tuning a 32B + per-checkpoint eval). This is the expensive part and requires the remote.
- Refusal-ablation is cheap (no fine-tune) at both scales.

## Safety handling (per approved tamper mitigations — non-negotiable)
Everything LOCAL to the boxes; attacked LoRA adapters + any merged/ablated weights DELETED after measuring; only
aggregate ASR/WMDP numbers enter the repo. Public attack data (AdvBench) only. Content-safe grading (counts). This
is standard defensive tamper/safety-gap methodology (measuring a vulnerability already present in released
weights), not capability uplift for release.

## Iron-Law gates
- 32B showing tamper-RESISTANCE (refusal survives) = SUSPICIOUS → verify the attack changed the weights
  (step-0 vs step-80 generations differ) before believing it.
- WMDP of a stripped model ≈ chance (25%) = broken eval, not "safe."
- Any 0%/100% or byte-identical-seed cell → investigate (we've been bitten by both).

## Results
NOT RUN (design only; awaiting gs157 sign-off on the dual-use 32B run + remote spend). Outputs → runs/2026-…-safetygap-*.

## Links
Extends SUMMARY Part 10; refs outputs/refs_safety_pretraining.md (Safety Gap Toolkit + refusal-ablation 2410.03415);
BACKLOG "QUEUED 2026-07-29 — adapt the Safety Gap Toolkit".
Motivation is also framed in the companion blog post *Red-Teaming Language Models*
(https://gussand.github.io/posts/2026/07/red-teaming-language-models/#measuring-any-of-this-is-its-own-problem),
which names the Safety Gap Toolkit + TamperBench as the instruments for measuring safeguard durability — this
experiment is that measurement carried out on Olmo (scale sweep) + Marin (8B anchor).
