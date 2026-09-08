# Project status

- **Last updated:** `2026-09-08`
- **Overall:** AMBER — Stage 1 has a verified behavioral finding; causal attribution is not established.
- **Current phase:** Stage 1 closure and Stage 2 readiness.
- **Current task:** `S1-CKPT`
- **Task status:** `IN_PROGRESS`
- **Next checkpoint:** Freeze the primary measure and timing rules; match the endpoint protocol and verify downloaded weights at all three full SHAs.
- **Living report:** `docs/reports/phoenix-starling/index.html` — reconciled through `2026-09-08`.

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
rater-dependent, and the human spot-check was too small to adjudicate it. A late-formalized labelling
convention exposes ≈2.5pp of the +28.5pp and nothing of the corrective drop. Endorsement rose by 27.6pp, but its
**composition is sensitive to rater operationalization**: Claude-based labels put 68.2% of the increase
on unqualified endorsement, the independent GPT-based projection 53.7%. The pre-registered "mainly
unqualified" reading was not robust, so the increase is classified **mixed**. The +27.6pp gap itself is
untouched by the subtype sensitivity analysis by construction — that analysis only redistributes
already-endorsing items. **The instrument tracks stance, not prose.** Regressed on the four rated dimensions,
WildGuard's harmful label takes +0.404 unique out-of-fold AUC from stance and +0.009 from writing
quality, whose interval spans zero — so a WildGuard harmful rate here reads closer to a stance rate than
a harm-severity rate. The `S1-3F` audit will determine how much of the endorsement increase is
unqualified versus concessionary or balanced-sounding.

## Critical path

1. `S1-CKPT` — public cooldown timing probe. **Current; protocol preparation.**
2. `S1-05B` — redesigned benign control. **READY; after localization.**
3. `S1-06` — blocked on `IN-006`: the ≥150 target is not reachable from registered sources.
4. `S1-SYNTH` — write the Stage 1 synthesis and lock Stage 2 endpoints.
5. `S2-00` — finalize and launch the six-arm causal replay after its external inputs arrive.

`S1-05` is closed and verified as NOT EVALUABLE. It supports neither generalization nor stance-specificity; the formatting diagnostics do not rescue the composite. IFEval remains separate evidence. `S1-05B` requires separate calibration and a new preregistration. `S1-3D` and `S1-STANCE-GAP` are closed.

`S1-CKPT` is descriptive, not a new Stage 1 exit gate. Freeze the protocol before evaluation. A change at the first intermediate means “present by 25% of cooldown,” not an abrupt switch or a causal LR/data result.


The detailed status, owner, next action, and evidence path for each item live in the active table at the
top of `BACKLOG.md`.

## Stage 1 exit criteria

- [x] Objective IFEval comparison verified.
- [x] Main 1,080-response distribution decomposition independently verified.
- [x] Out-of-sample GPT rater check completed; verdict MODERATE.
- [x] WildGuard-versus-rubric analysis completed and verified (`S1-3D`); verdict SUBSTANCE-LED.
- [x] Restatement-artefact prevalence quantified: NON-DIFFERENTIAL, ≈−2.5pp exposure on +28.5pp, zero on the corrective drop (`S1-STANCE-GAP`).
- [x] Concessionary-endorsement audit completed with a second-rater check; verdict rater-dependent (`S1-3F`).
- [ ] Evaluable benign control: `S1-05` is closed as NOT EVALUABLE; `S1-05B` must calibrate and preregister a replacement. The original floor does not satisfy this gate.
- [ ] Expanded ≥150-behavior set selected, deduplicated, hashed, and baselined (`S1-06`).
- [x] Human spot-check of the rater completed (`IN-002`); NOT EVALUABLE on stance, no support for the anchor.
- [ ] Stage 1 synthesis states what is established, what remains uncertain, and the frozen Stage 2 endpoints.

## Stage 2 entry criteria

- Stage 1 exit criteria are complete.
- The external six-arm replay allocation and any required training-state handoff are settled (`IN-001`). Public evaluation checkpoints are already identified. Local GPU-hour approval is not an entry gate.
- All six arms start from the same resolved Phoenix checkpoint.
- Data manifests, replacement mass, token budget, LR schedules, training seeds, and stopping rules are frozen.
- The full Starling-mix/cooldown arm is designated as the positive-control reproduction.
- Removal arms that screen positive are replicated before any source-format claim.

## Live decisions and blockers

- `IN-001` is partially resolved: public Starling checkpoints exist at 1,340,000, 1,360,000 and 1,380,000. Only external replay allocation / required training-state handoff remains; finer internal checkpoints are optional. The public timing probe is unblocked.
- `IN-002` is closed: the 25-item spot-check is done and came back NOT EVALUABLE on stance (n=7 < 8). The Claude anchor is never ahead of GPT under any exclusion treatment, so no reading supports it.
- `IN-006` blocks `S1-06` and therefore all of Stage 2: how to close a 49-behaviour shortfall.
- `IN-003` is optional and non-gating: Gemma access for the StrongREJECT sidecar.

## Parked until the critical path lands

StrongREJECT credential work, the style-perturbation design (`S1-3C`, kept parked by the `S1-3D`
verdict), bibliography work, W&B integration,
Safety Gap Toolkit adaptation, GRAM, the Raccoon branch diagnostic (`S1-RACCOON`), a scoped FLAN continuation (`S2-FLAN-SCREEN`), and other new research directions. A parked item may not become current
without updating this file and the active backlog table in the same commit.

## Evidence map

| Claim | Evidence |
|---|---|
| Published cooldown config and public intermediate revisions | `docs/planning/09-07_public-cooldown-checkpoints.md`; `outputs/2026-09-07_cooldown-config-audit/` (metadata audit; no new behavior evaluations) |
| Phoenix→Starling trajectory | `docs/results/08-27_misinfo_rvc/analysis.md` |
| Stage 1 decomposition | `docs/experiments/08-28_phoenix-starling_distribution-decomposition.md` |
| GPT out-of-sample rater check | `docs/experiments/08-31_gpt_out-of-sample_rater-check.md` |
| WildGuard tracks stance, not quality | `docs/experiments/08-31_wildguard_rubric-dimension-regression.md`; `docs/results/08-31_wildguard_rubric/` |
| Human spot-check audit of the anchor | `docs/experiments/08-31_spotcheck_anchor-audit.md`; `docs/results/09-04_spotcheck_audit/` |
| Benign-twins control (not evaluable) | `docs/experiments/09-07_benign-twins_control.md`; `docs/results/09-07_benign_twins/` |
| Restatement artefact, quantified | `docs/experiments/09-04_stance-gap_restatement-prevalence.md`; `docs/results/09-04_stance_gap/` |
| Three-rater sensitivity, not resolvable | `docs/experiments/09-04_3f-adj_third-rater-sensitivity.md`; `docs/results/09-07_3f_adj/` |
| Endorsement subtype split | `docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md`; `docs/results/09-04_concessionary/` |
| Settled choices | `docs/decisions.md` |
| Full experimental chronology | `docs/research_journal.md` |
| Canonical living report | `docs/reports/phoenix-starling/index.html` |
