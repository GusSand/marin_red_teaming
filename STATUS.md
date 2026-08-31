# Project status

- **Last updated:** `2026-08-31`
- **Overall:** AMBER — Stage 1 has a verified behavioral finding; causal attribution is not established.
- **Current phase:** Stage 1 closure and Stage 2 readiness.
- **Current task:** `S1-3D`
- **Task status:** `READY`
- **Next checkpoint:** Pre-register and run the CPU-only WildGuard-versus-rubric analysis.
- **Living report:** `docs/reports/phoenix-starling/index.html` — reconciled through `2026-08-31`.

This is the operational source of truth. `BACKLOG.md` holds the ordered task queue. `INBOX.md`
holds live requests for Gus. `docs/research_journal.md` and the legacy sections of the backlog and
inbox are historical evidence, not current status.

## Current objective

Close Stage 1 with a defensible account of what changed between Phoenix and Starling. Freeze a broader
misinformation evaluation before any Stage 2 training. Then run the controlled Phoenix continuation
experiment that separates data-mixture and learning-rate effects.

## Current finding

**Phoenix→Starling is a real behavioral-distribution change, not yet a causal training claim.** On the
54-behavior, 10-seed evaluation, refusal mass fell 12.2pp, corrective mass fell 12.2pp, and
attempt-strong mass rose 28.5pp. General instruction following improved 11.8pp. Quality given attempt
moved only +0.12 and was not significant. The direction replicates across raters; the magnitude is
rater-dependent. The new `S1-3F` audit will determine how much of the endorsement increase is
unqualified versus concessionary or balanced-sounding.

## Critical path

1. `S1-3D` — determine which rubric dimensions WildGuard actually tracks.
2. `S1-3F` — split endorsement into unqualified, concessionary, and misclassified correction/hedge.
3. `S1-05` — run the triggered benign-twins control.
4. `S1-06` — freeze and baseline the expanded ≥150-behavior evaluation.
5. `S1-SYNTH` — write the Stage 1 synthesis and lock Stage 2 endpoints.
6. `S2-00` — finalize and launch the six-arm causal replay after its external inputs arrive.

The detailed status, owner, next action, and evidence path for each item live in the active table at the
top of `BACKLOG.md`.

## Stage 1 exit criteria

- [x] Objective IFEval comparison verified.
- [x] Main 1,080-response distribution decomposition independently verified.
- [x] Out-of-sample GPT rater check completed; verdict MODERATE.
- [ ] WildGuard-versus-rubric analysis completed and verified (`S1-3D`).
- [ ] Concessionary-endorsement audit completed with a second-rater check (`S1-3F`).
- [ ] Benign-twins control completed (`S1-05`).
- [ ] Expanded ≥150-behavior set selected, deduplicated, hashed, and baselined (`S1-06`).
- [ ] Stage 1 synthesis states what is established, what remains uncertain, and the frozen Stage 2 endpoints.

## Stage 2 entry criteria

- Stage 1 exit criteria are complete.
- David has answered checkpoint-availability and compute-budget questions (`IN-001`).
- All six arms start from the same resolved Phoenix checkpoint.
- Data manifests, replacement mass, token budget, LR schedules, training seeds, and stopping rules are frozen.
- The full Starling-mix/cooldown arm is designated as the positive-control reproduction.
- Removal arms that screen positive are replicated before any source-format claim.

## Live decisions and blockers

- `IN-001` blocks Stage 2: intermediate Starling checkpoint availability and training budget from David.
- `IN-002` needs Gus: complete the 25-item spot-check or explicitly waive it in light of the out-of-sample GPT audit.
- `IN-003` is optional and non-gating: Gemma access for the StrongREJECT sidecar.

## Parked until the critical path lands

StrongREJECT credential work, the current style-perturbation design, bibliography work, W&B integration,
Safety Gap Toolkit adaptation, GRAM, and other new research directions. A parked item may not become current
without updating this file and the active backlog table in the same commit.

## Evidence map

| Claim | Evidence |
|---|---|
| Phoenix→Starling trajectory | `docs/results/08-27_misinfo_rvc/analysis.md` |
| Stage 1 decomposition | `docs/experiments/08-28_phoenix-starling_distribution-decomposition.md` |
| GPT out-of-sample rater check | `docs/experiments/08-31_gpt_out-of-sample_rater-check.md` |
| Settled choices | `docs/decisions.md` |
| Full experimental chronology | `docs/research_journal.md` |
| Canonical living report | `docs/reports/phoenix-starling/index.html` |
