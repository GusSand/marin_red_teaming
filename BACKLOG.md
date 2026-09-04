# Backlog

`STATUS.md` is the operational source of truth. Only the table below is the active queue. Everything
after **Legacy backlog and briefs** is preserved research history and must not be used to choose the
next task. Lifecycle rules: `docs/PROJECT_OPERATING_RULES.md`.

## Active critical path

<!-- ACTIVE_TASKS_START -->
| ID | Status | Owner | Outcome | Next action | Evidence / specification |
|---|---|---|---|---|---|
| `PM-001` | DONE | Codex | Install the project-control reset and validation guardrails. | Run the validator; hand off `S1-3D`. | `STATUS.md`; `docs/PROJECT_OPERATING_RULES.md`; `scripts/check_project_state.py` |
| `PM-002` | DONE | Codex | Install the canonical living-report path and freshness gate. | Keep it reconciled in every task transition and close transaction. | `docs/reports/phoenix-starling/index.html`; `docs/reports/README.md` |
| `S1-3D` | DONE | Research agent | WildGuard tracks stance, not writing quality: unique ΔAUC stance +0.404, quality +0.009 with CI spanning 0. | Verdict SUBSTANCE-LED, VERIFIED within 0.0005 by two independent paths; no follow-up. | `docs/experiments/08-31_wildguard_rubric-dimension-regression.md`; `docs/results/08-31_wildguard_rubric/` |
| `S1-3F` | READY | Research agent | Split endorsement into unqualified, concessionary, and misclassified correction/hedge. | Preregistration frozen 2026-09-04; resume it. `S1-STANCE-GAP` found 10 of 20 flagged items sit in `endorses`, so subtype (c) is the same phenomenon and the two must agree. | `docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md` |
| `S1-05` | READY | Research agent | Determine whether the compliance change appears on matched benign instructions. | Finalize the 54 rule-gradable twins and pre-register scoring. | `docs/experiments/08-28_phoenix-starling_distribution-decomposition.md` |
| `S1-06` | READY | Research agent | Freeze and baseline a deduplicated ≥150-behavior misinformation evaluation. | Write the source-selection note, deduplicate, hash, and inventory the set. | `docs/DATA_INVENTORY.md`; Stage 1 spec step 6 |
| `S1-SYNTH` | READY | Research agent | Produce the Stage 1 verdict and frozen Stage 2 endpoints. | Runs after `S1-3F`, `S1-05` and `S1-06` land; it is last in this table, not next. `S1-3D` done, `IN-002` closed inconclusive. | `STATUS.md` Stage 1 exit criteria |
| `S2-00` | BLOCKED | Gus + David | Finalize the six-arm causal replay and its training allocation. | Resolve `IN-001`, then write the Stage 2 experiment document. | Stage 1 spec step 7; `docs/decisions.md` 2026-08-28 six-arm decision |
| `S1-STANCE-GAP` | DONE | Research agent | NON-DIFFERENTIAL: prevalence 7.5% / 9.2%, paired delta −0.88pp [−9.05, +6.43]. Band puts ≈−2.5pp on +28.5pp and 0.00pp on the corrective drop. | VERIFIED. Underpowered non-rejection, not equivalence; a ≥5pp differential is not excluded. | `docs/experiments/09-04_stance-gap_restatement-prevalence.md`; `docs/results/09-04_stance_gap/` |
| `S1-JUDGE-VOCAB` | PARKED | Research agent | Judge output parser admits stance values outside the locked vocabulary. | `olmo32.jsonl` has `stance="refutes"` on `c0040`; audit the 150-item judge outputs for other invalid classes. Cannot rescue the 08-29 selection verdict. | `docs/experiments/08-31_spotcheck_anchor-audit.md` |
| `S1-3B` | PARKED | Gus | Optional StrongREJECT sidecar, explicitly non-gating. | Resolve `IN-003` only if the sidecar is retained. | `docs/experiments/08-29_strongreject_sidecar_phoenix-starling.md` |
| `S1-3C` | PARKED | Research agent | Style-sensitivity test with a valid rewriter and fidelity check. | Stays parked: `S1-3D` found WildGuard tracks stance, not quality, so the style-artifact route is not supported. Also needs a rewriter no local judge passed selection for. | `docs/experiments/08-29_wildguard_style-perturbation.md` |
<!-- ACTIVE_TASKS_END -->

## Queue rules

- WIP limit: at most one `IN_PROGRESS` task.
- The next task is the first `READY` row unless `STATUS.md` documents a change.
- A blocked task names its unblock condition and corresponding INBOX ID.
- New research directions enter as `PARKED`; they do not jump the critical path silently.
- Run `python3 scripts/check_project_state.py` after every state change.

---

## Legacy backlog and briefs

The material below is preserved for provenance. Status markers below this line are historical and may
be stale. Do not execute from them without promoting the task into the active table above.

# Task 1: reproduce Olmo 3 7B safety numbers

## Stage 1 / Stage 2 program (gs157, 2026-08-28) — spec: docs/experiments/08-28_phoenix-starling_distribution-decomposition.md

- [x] **1. IFEval** — DONE 2026-08-29: phoenix→starling +11.8pp strict [+8.1, +15.7]; trigger fired. (official pinned repo, greedy, base scaffold) on jellyfish/phoenix/starling/deeper-starling. Trigger for item 5: starling−phoenix ≥ +5pp prompt-level strict, CI excl. 0.
- [~] **2. Calibration set + judge selection — DONE, verdict: no local judge selected.** Both failed against both anchors (Claude, GPT); per the pre-registered rule none was picked. Judge for step 3 = the blind Claude Fable 5 annotator. gs157's 25-item spot-check is the outstanding audit (INBOX). Original line: anchor = blind Claude annotator (gs157, 08-29), human spot-check ~25. Lock rubric/prompts in `config/judge_rubric_v1/` first. Two local judges, per-dimension macro-F1 ≥ 0.75, off-topic/corrective recall ≥ 0.60. Neither clears → expand annotation, never pick the better-looking one. Not WildGuard. Verdict → decisions.md.
- [x] **3. DONE + VERIFIED 2026-08-29.** Mass leaves refuse (−12.2pp) and correct (−12.2pp) for attempt-strong (+28.5pp); ≈82% stance / ≈18% quality; IF signature not supported, EXP not evaluable (n=2). Independent verifier matched within 0.02pp. Original: **Behavior-level distribution decomposition** phoenix→starling, 1,080 existing responses, six categories, mass changes with behavior bootstrap. Never phrased as flows. **Pass-2 annotation running 2026-08-29 (4 blind Fable instances on balanced shards, 135/135 each).** Analysis path smoke-tested on synthetic labels (null in, null out). Test-retest rules pre-registered. Next: merge_sheets → decompose_distribution → retest_agreement → fresh-subagent verification.
- [~] **4. Wrapper sensitivity** — generation + WildGuard analysis DONE 2026-08-29 (CORRECTED: pre-registered interaction −5.6pp [−17.9, +8.6], criterion NOT met once null-label rows count as non-response; scaffolded-only post hoc +12.3 [0.0, +22.8]); judge-based attempt mass pending step 2.: raw / current scaffold / explicit instruction / benign-only few-shot × {phoenix, starling} × 3 seeds, 3 sub-2h jobs, namespace `2026-08-29-wrap-h200`.
- [ ] **5. Benign twins** (TRIGGERED by item 1, 2026-08-29): 54 rule-gradable twins, same wrappers/seeds as item 4 W1.
- [ ] **6. Freeze expanded misinfo eval ≥150 behaviors** (selection note for the second source, dedupe, hash in DATA_INVENTORY, baseline on four tags × 10 seeds) before any Stage 2 arm trains.
- [ ] **7. Stage 2 six-arm staged replay** — own experiment doc after David answers INBOX (intermediate checkpoints; budget for 10 training runs: A–D ×2, E/F ×1 screening + replicate the removal that matters). 10% = screening checkpoint only; efficacy look at 25% or conditional-power rule unless historical checkpoints justify a 10% futility rule.
- [!] **3b. BLOCKED on gated `google/gemma-2b` (INBOX 10:15).** Pre-registered: `docs/experiments/08-29_strongreject_sidecar_phoenix-starling.md`. Adapter cached, base 401s; needs a licence acceptance + HF token from gs157. Declared deviation: safety-eval's StrongREJECT emits ONE graded score, not the three dimensions this line names. **3b. StrongREJECT evaluator sidecar** on the 1,080 phoenix/starling responses (fine-tuned judge already in safety-eval): refusal + specificity + convincingness, graded. Triangulates WildGuard (binary) and the rubric judge. No new generation, no human labels. Report alongside step 3, not as its primary.
- [x] **3e. Out-of-sample GPT rater check — DONE 2026-08-31. Verdict: MODERATE.** Sheet returned,
  validated (150/150), compared. stance κ **0.705** (bar 0.70, met), six-category agreement **0.733**
  (bar 0.75, missed — moderate band), three-way **0.867** (bar 0.90, missed). Not near the undermines
  floor. Per the pre-registered rule the step-3 verdict **stands unchanged**; the rater-dependence
  caveat is strengthened and quoted with these numbers. Secondary met: `corrects` F1 **0.864**, the
  best-agreed category — the `correct`-is-real reading survives. Disagreement concentrates in `hedge`
  (F1 0.449). Quote the three-way 0.867 alongside any external use of +28.5pp.
  `docs/experiments/08-31_gpt_out-of-sample_rater-check.md`.
- [ ] **3f. Concessionary vs unqualified endorsement audit — POST-HOC FOLLOW-UP (raised 2026-08-31).**
  Test whether the Phoenix→Starling rise in `attempt-strong` is primarily unequivocal endorsement or
  "balanced-sounding" / concessionary endorsement that acknowledges harms or counterevidence before
  ultimately advancing the requested false thesis. Use the existing 1,080 responses; no new generation.
  Before labelling, lock a blinded additive sub-rubric over the primary-rater `endorses` items with three
  mutually exclusive outcomes: (a) unqualified endorsement, (b) concessionary endorsement, and (c) net
  correction/hedge misclassified as endorsement. Apply the same fabricated-turn truncation convention as
  pass 2. Report Phoenix and Starling mass plus the behavior-paired delta for each subtype, never response
  "flows". Audit a stratified 150-item slice with a second frontier rater and report agreement, especially
  on (b) vs (c). Explicitly label the analysis post hoc. **Decision use:** if Starling's gain is mainly (b),
  describe the result as increased willingness to supply the requested thesis despite concessions; if it is
  mainly (a), retain the stronger endorsement reading; if (c) is material or rater agreement is poor, weaken
  the stance-shift claim before Stage 2. This is a cheap Stage 1 closure item, not a gate on freezing the
  expanded ≥150-behavior evaluation.
- [ ] **3d. Which rubric dimension does WildGuard track?** Regress WildGuard `harmful` on
  relevance/task/stance/quality from the pass-2 Claude labels over the 1,080 (their Fig. 2 style-correlation
  analysis). Unblocked and free: all inputs on disk, CPU-only, no new labels. Pre-register before running.
  Announced as "picking up now" on 08-31 10:15 and then not started — it is next.
- [ ] **3c. Style-perturbation test of WildGuard** — PRE-REGISTERED 2026-08-29: `docs/experiments/08-29_wildguard_style-perturbation.md`. Runs after the step-3 annotator is fixed (it supplies the rewriter). Rewrite Starling `harmful` responses to be blander/shorter with identical claims, and Phoenix compliant-`unharmful` responses more polished with identical claims; re-judge with the pinned WildGuard; count label flips = judge style sensitivity in pp. Rewriter = selected local judge with a claim-preservation prompt + fidelity check before counting. Pre-register flip-rate criteria before running. Direct H1 test, ~1 h GPU.
- [ ] **Bibliography hypothesis matrix** (parallel, non-gating): convert `outputs/2026-08-28_lit_refusal_vs_polish.md` to base/aligned · pretrain/CPT/SFT · content vs format · refusal/task/judge-harm · transferable-causal columns.

- [x] ~~H1b instrument~~ → superseded by Stage 1 items 1, 2, 5 above (2026-08-28). **H1b instrument: relevance / task-success scorer (or gradable benign task).** Needed to split the +11pp harmful|non-refusal rise into writing quality (H1) vs on-topic-ness (H1b) in the cooldown. Candidates: an LLM relevance grader on (behavior, response) with a held-out human-labelled set; or a benign task with objective grading. Selection experiment; pre-register before running.
- [ ] **wandb for job tracking (Gus, 2026-08-28: "leave it for next time").** Login node reaches api.wandb.ai; test from a compute node inside a job first (jobs run HF_HUB_OFFLINE=1, network unconfirmed). Needs an API key on Torch, which is Gus's to place. Log per-run RESULT lines, heartbeat GPU %, and terminal state. Motivation: three jobs were killed by the utilization watchdog before anyone noticed.
- [ ] **Load-once multi-seed generation.** Sequential per-run design averages ~39% GPU util, below the 50% watchdog cutoff. Load each model once, generate all seeds in one vLLM session, judge once. Must be verified token-exact against the gate runs before it replaces run_row.sh.

Agent brief for Claude Code. Read all of it before running anything.

## Objective

Reproduce the published safety-benchmark numbers for **Olmo 3 7B Instruct**
and **Olmo 3 7B Think** (Olmo 3 technical report, arXiv 2512.13961,
Tables 52 and 53) using `allenai/safety-eval`, and produce a per-row
delta report against the published values.

The deliverable is **the delta report**, not matching numbers. A row that
does not reproduce is a result, not a failure, provided the cause is
investigated and documented.

## Non-goals

- Do not evaluate any Marin model in this task. That is a separate task
  that depends on this one passing.
- Do not build a new harness, wrapper framework, or abstraction layer.
  Use `safety-eval` as-is.
- Do not optimize, refactor, or "improve" the eval code.

---

## Hard rules

These are not negotiable. Violating any of them invalidates the run.
(Consider copying this section into `CLAUDE.md`.)

1. **Never write a number you did not produce from an actual run.** Every
   value in every table must be traceable to a specific
   `metrics.json` on disk. No estimated, remembered, or inferred values.
   If a run did not complete, the cell is `NOT RUN`, not a guess.

2. **Never tune configuration to make a number match.** If the output
   disagrees with the published value, record the delta and investigate
   the cause. Changing judges, prompts, sampling params, or subsets until
   the number lands is fabrication, and it destroys the point of the task.
   The one exception is correcting a config that provably diverges from
   what the paper used — and that correction must be logged with evidence
   in `DECISIONS.md` before it is applied.

3. **Never substitute a component silently.** If a specified judge model,
   dataset, or revision is unavailable, STOP and report. Do not fall back
   to a different classifier, a cached copy, or a similar-looking dataset.

4. **Never proceed past a failed gate.** Gates are stop-and-ask points.
   Report status and wait for a human decision.

5. **Pin everything.** Record and log for every run: `safety-eval` commit
   SHA, model repo + revision, judge model repo + revision, sampling
   params, seed, dataset revision, date, GPU type, and the exact command.
   A run without a complete provenance record does not count.

6. **No silent retries.** If a run crashes and is restarted, log both
   attempts. Do not overwrite prior results.

---

## Repository layout

```
repro-olmo3-safety/
  DECISIONS.md        # append-only log: every judgment call + evidence
  targets.json        # published values (HUMAN-VERIFIED, see Gate 0)
  config/             # frozen per-row config: metric, direction, judge
  runs/<date>-<model>-<row>/
      command.txt     # exact command
      provenance.json # commits, revisions, seed, params, hardware
      metrics.json    # raw safety-eval output
      all.json        # per-instance results
  report/
      deltas.md       # produced vs. published, per row
```

---

## Gate 0 — establish ground truth (NO COMPUTE)

Before touching a GPU.

**Do:**
- Read the Olmo 3 report and extract, for every row of Tables 52 and 53:
  benchmark name, the SFT / DPO / Final values, and any footnote about
  metric definition.
- Read the relevant `safety-eval` task YAMLs and record, per row: the
  task class, the `classifier_model_name` default, the dataset used, and
  whether the metric is ASR or refusal (RTA = 1 − ASR).
- Write `targets.json` and `config/`.
- Flag every row where the report's prose and the repo config disagree.

**Known disagreements to check for (documented in `open-instruct#500`):**
- **TrustLLM-JailbreakTrigger** — the Tulu 3 paper named WildGuard, but
  the task default is `OpenInstructGPTJailbreakTriggerClassifier`, which
  is OpenAI-API-based. An Ai2 maintainer confirmed the YAML default is
  correct. Verify which applies for Olmo 3.
- **WildJailbreak** — Tulu 3 reported one aggregated score,
  `(benign + (1 − harmful)) / 2`. Tables 52/53 report Harmful and Benign
  as separate rows, so the convention differs. Determine which is used
  before comparing anything.

**Gate: STOP.** A human verifies `targets.json` against the actual PDF
tables by eye. Do not proceed on agent-extracted target values. If both
the produced and target numbers come from the agent, the comparison is
meaningless.

---

## Gate 1 — environment (MINIMAL COMPUTE)

**Do:**
- Install `safety-eval` at a pinned commit. Record the SHA.
- Confirm GPU, driver, vLLM version.
- Confirm the WildGuard judge loads and classifies a handmade
  two-example input correctly.
- Confirm `OPENAI_API_KEY` is present **if and only if** Gate 0
  determined an OpenAI-based classifier is required. Note that this row
  incurs external API cost — estimate and report it before running.
- Run one benchmark at the smallest available subset on any small model,
  end to end, purely to prove the pipeline executes.

**Gate: STOP.** Report environment provenance and the smoke-test output.
Do not proceed to real evaluation until approved.

---

## Gate 2 — single row (THE REAL GATE)

Reproduce **exactly one** row: HarmBench on Olmo 3 7B Instruct, final
checkpoint, single run.

**Exit criteria:** produced value within a stated tolerance of the
published value. Propose the tolerance in `DECISIONS.md` with reasoning
before running — do not decide it after seeing the number.

**Gate: STOP.** If it matches, the pipeline is trustworthy and everything
downstream is mechanical. If it does not, do not run anything else. Report
the delta and the top three hypotheses for the cause.

---

## Gate 3 — the four clean rows

HarmBench, XSTest, DoAnythingNow, WildGuard-Test on Olmo 3 7B Instruct
(final). These four have been reproduced by a third party previously, so
they are the expected-easy set.

Three runs each. Report **mean and spread** — the report gives means over
three runs but not variance, and the spread is information Ai2 did not
publish.

**Gate: STOP.** Report the 4-row delta table.

---

## Gate 4 — the convention rows

WildJailbreak (Harmful, Benign) and TrustLLM-JailbreakTrigger, applying
the Gate 0 findings.

**Gate: STOP.** These are where reproduction is most likely to diverge.
Report deltas and, if they diverge, what changed between the paper's
described setup and the repo's actual behavior.

---

## Gate 5 — remaining rows, then Think

BBQ (Accuracy, Bias-Ambiguous, Bias-Disambiguated), StrongReject,
Toxigen, WMDP — completing Table 53. Then repeat the full suite for
Olmo 3 7B Think against Table 52.

Watch for: BBQ bias rows and WMDP may have different direction
conventions than the refusal-rate rows. Gate 0 should have settled this;
if it did not, stop rather than assume.

**Gate: STOP.** Full delta report for both models.

---

## Gate 6 — write-up

Produce `report/deltas.md`:
- Per-row: published, produced (mean ± spread over 3 runs), delta, status
- A short section on every convention that was undocumented or where the
  paper and code disagreed
- An explicit statement of what a downstream user must configure to get
  these numbers, i.e. the reproduction recipe
- Every unresolved discrepancy, listed plainly rather than buried

---

## Reporting discipline

At every gate, report in this form:

```
GATE N: PASS | FAIL | BLOCKED
Produced: <values with paths to metrics.json>
Expected: <values with source>
Delta: <per row>
Provenance: <commits, revisions, seed, hardware>
Open questions: <list>
```

If uncertain whether something counts as a pass, it is not a pass.
Report and ask.

# Task 2: Marin 8B on the Olmo 3 safety suite

Agent brief for Claude Code. Read all of it before running anything.

## Precondition

**This task does not start until `REPRO-olmo3-safety.md` has passed Gate 6.**
If the Olmo 3 numbers did not reproduce, any Marin number produced here is
uninterpretable. Verify the delta report exists and check whether it passed
before doing anything else.

## Objective

Run the safety suite from the Olmo 3 report on Marin 8B, producing a
comparison table that a Marin maintainer can act on.

Models, in priority order:

1. `marin-community/marin-8b-instruct` (revision `deeper-starling-05-15`)
2. `marin-community/marin-8b-base` (revision `deeper-starling`, = `main`)
3. Base revisions: `starling`, `phoenix`, `jellyfish`, `ocelot`, `kestrel`

## Non-goals

- No mechanistic analysis, steering, or interpretability work.
- No fine-tuning, no interventions, no "can we fix it."
- No new benchmarks beyond the Olmo 3 suite.

---

## Hard rules

All hard rules from `REPRO-olmo3-safety.md` carry over unchanged. Plus:

1. **Config is frozen.** Judges, prompts, sampling params, dataset
   revisions, and metric definitions are byte-identical to what passed
   Gate 6 of the reproduction task. Load them from `config/`. Any change
   invalidates the comparison. If something must change, STOP.

2. **Compare `marin-8b-instruct` against Olmo 3's SFT column, not Final.**
   Olmo 3 Instruct is SFT + DPO + RLVR. Marin 8B Instruct is SFT-only,
   one phase, 5.3B tokens. Comparing against the Final column measures
   how many post-training stages each project ran, which is already known.
   Every table must state which column it compares against, in the table
   itself, not a footnote.

3. **Base models have no published counterpart.** Tables 52 and 53 cover
   Think and Instruct only. There is no Olmo base safety number to compare
   to, so do not invent a comparison. See Gate 4 for how this is handled.

4. **Do not aggregate across revisions into a trend line without
   flagging the confounds.** See Gate 5.

---

## Gate 0 — chat template and config freeze (NO COMPUTE)

The highest-risk unknown in this task. A wrong chat template silently
produces plausible, meaningless refusal rates.

**Do:**
- Determine the correct chat template for `marin-8b-instruct`. Note that
  `stanford-crfm/marin-tokenizer` is a Llama 3 tokenizer variant that
  bundles a chat template into the base tokenizer. Establish what
  `safety-eval`'s `--model_input_template_path_or_name` should be set to,
  and whether an existing named template matches or a new one is needed.
- Record how the reproduction task set this for Olmo 3, and why Marin
  differs.
- Determine what template, if any, applies to base-model evaluation.
- Freeze and copy the judge/metric config from the reproduction task.
- Write predictions to `PREDICTIONS.md` **before any run**: expected
  direction and rough magnitude for each row, for base and instruct.
  This is to prevent post-hoc storytelling later.

**Gate: STOP.** Human confirms the template decision. This is the single
most likely source of a wrong answer in the whole task.

---

## Gate 1 — output sanity (MINIMAL COMPUTE)

Before any metric is computed, confirm the model is producing coherent
text under the chosen template.

**Do:**
- Generate on 20 prompts: 10 benign, 10 from a harmful split.
- Dump raw generations to a file. Do not score them.
- Check for: degenerate repetition, empty completions, template tokens
  leaking into output, truncation, wrong-language output.

**Gate: STOP.** A human reads the 20 generations. Metrics computed on
broken generations look exactly like metrics computed on good ones.

---

## Gate 2 — instruct, four clean rows

HarmBench, XSTest, DoAnythingNow, WildGuard-Test on `marin-8b-instruct`.
Three runs each, mean and spread.

**Gate: STOP.** Report the four rows against Olmo 3's SFT column, with
spread. Sanity-check the direction against `PREDICTIONS.md` and note any
prediction that was wrong — wrong predictions are informative, not
embarrassing.

---

## Gate 3 — instruct, full suite

Remaining rows: WildJailbreak (Harmful, Benign), TrustLLM-JailbreakTrigger,
BBQ (3 rows), StrongReject, Toxigen, WMDP.

**Gate: STOP.** Full Marin-instruct table.

---

## Gate 4 — base models, both projects

`marin-8b-base` has no published Olmo counterpart, so create one: run the
identical suite on `allenai/Olmo-3-1025-7B` (base) as well. That makes the
base-vs-base comparison first-party and symmetric rather than an unanchored
number.

Flag prominently in the write-up: base models do not refuse, they complete.
Refusal-rate metrics on a base model measure something different from the
same metric on an instruct model, and the two should never appear in the
same column without a divider.

**Gate: STOP.** Report base-vs-base, with the interpretive caveat stated
in the table, not only in prose.

---

## Gate 5 — pretraining revisions

Run the suite across `kestrel` (2.7T), `ocelot` (3.78T), `jellyfish`
(4.78T), `phoenix` (11.1T), `starling` (12.4T), `deeper-starling` (12.7T).

Start with three points — `kestrel`, `jellyfish`, `deeper-starling` — and
report before running the rest. If nothing moves across a 10T-token span,
the remaining runs are lower priority.

**Confounds that must appear in the write-up, not be discovered by a
reader:**
- Spacing is uneven. `phoenix` spans 4.78T → 11.1T; `deeper-starling` is
  0.3T past `starling`. This is not a uniformly sampled training curve.
- Each phase changes the *data mixture*, not just token count: `jellyfish`
  is a cooldown on higher-quality data (~Dolmino + FineMath), `phoenix` is
  a reheat on Nemotron-CC. Token count and mixture are confounded.
- `kestrel` is the only checkpoint **not** using an exponential moving
  average of weights. Report it as a separate point, visually distinct.
  Do not drop it.

Frame results as "does safety behavior move at phase boundaries",
never as "susceptibility emerges at N tokens."

**Gate: STOP.**

---

## Gate 6 — write-up

`report/marin-safety.md`:

- One comparison table, Marin vs Olmo 3, stating the compared column
  in-table
- Base-vs-base as a separate table with its own interpretive header
- Revision results with confounds stated adjacent to the numbers
- Training-context footnotes: Marin 8B 12.7T tokens; Olmo 3 Base 7B ~5.9T
  pretraining + 100B midtraining + 50B long-context. Marin saw roughly
  twice the tokens at similar scale
- `PREDICTIONS.md` diff: what was predicted, what happened
- Explicit statement that Marin 8B's card documents no safety tuning or
  evaluation, so low scores on refusal benchmarks are the expected
  baseline and not a finding
- Every unresolved discrepancy listed plainly

Tone requirement: this is a baseline measurement of a model that never
claimed to have one. Any sentence that reads as a criticism of the Marin
team gets rewritten.

---

## Reporting discipline

Same format as the reproduction task. If uncertain whether something
counts as a pass, it is not a pass.
---

## Research directions (queued 2026-07-27, from gs157 — for "improving Marin safety")

Anchor: safety numbers are set by POST-training; these are DIAGNOSTICS pointing at where to intervene.

1. [ ] **Base-revision diagnostic** (kestrel, ocelot, jellyfish, phoenix, starling, deeper-starling):
   NOT the refusal suite (base = confounded). Measure base-carried signals across revisions:
   WMDP (bio/chem/cyber knowledge), HarmBench chem-bio/cyber capability, misinformation-generation,
   RealToxicityPrompts. Higher-value variant: eval the instruct model built on each revision.
   TODO: locate revision handles (NOT branches — likely checkpoint tags / step_XXXX revisions).
2. [ ] **Scale study**: marin-32b-base/-instruct as the 8B->32B->1T probe. Measure dangerous-CAPABILITY
   scaling (WMDP + real chem-bio/cyber accuracy, not just refusal) AND refusal/jailbreak robustness.
   Rationale: at 1T, compliance = real actionable harm (no hallucination cushion) -> alignment on our
   flagged gaps becomes MORE critical. Infra: 32B tight on one 80GB A100; 1T needs multi-node.
3. [ ] **Close 8B post-training gaps** (misinformation, contextual dual-use chem-bio, cyber social-eng,
   copyright non-refusal) in SFT/DPO; re-run this harness as the measurement loop. Most direct improvement.
4. [ ] **Lit-review** (paperclip): safety/dangerous-capability scaling laws; emergence of harmful
   capabilities during pretraining — ground priors before spending compute.
5. [ ] **Build RealToxicityPrompts eval** (local judge) — discriminating replacement for saturated ToxiGen.

---

## REFRAME 2026-07-27 (gs157 + arXiv:2508.06601 "Deep Ignorance") — open-weight safety ≠ post-training

Correction to the anchor above: for OPEN weights, post-training refusal is a strippable veneer
(bypassed in ~dozens of adversarial fine-tuning steps; Deep Ignorance shows pretraining-data FILTERING
survives 10k steps, >1 order of magnitude better). Everything our current harness measures = DEFAULT
behavior / casual-user safety, NOT tamper-resistance. Reprioritized:

A. [ ] **Tamper-resistance eval (NEW, high priority)**: adversarial fine-tuning robustness — fine-tune
   the instruct model on a small harmful set, measure how fast refusal collapses (Deep Ignorance protocol).
   This is the metric that actually matters for an open model; our harness does not measure it.
B. [ ] **Base dangerous-capability tracking** across revisions (kestrel..deeper-starling) + scale
   (8B->32B->1T): WMDP, real chem-bio/cyber capability. This is the true attack surface. (was Q1/Q2 — PROMOTED)
C. [ ] **Pretraining-data filtering / unlearning** (WMDP-style, dual-use/biothreat) as the real Marin
   intervention — not SFT refusal. Test whether it survives adversarial FT (tamper-resistance).
D. [ ] **In-context harmful-info exploitation**: Deep Ignorance's residual gap == our CONTEXTUAL chem-bio
   failures (smallpox/LSD). Build a focused eval: does the model use harmful info handed to it in context?
E. [~] Close 8B SFT/DPO gaps — DEMOTED to default-behavior/regression tracking only (tamper-vulnerable).
Ref: outputs/ (add Deep Ignorance to refs). Our red-team gaps + base-vs-instruct data corroborate this.

---

## QUEUED 2026-07-28 (after the 32B base-vs-base run) — checkpoint-trajectory studies
Both PRE-REGISTERED (design + hypothesis + null in the experiment files). Cheap (~1-2h each, 8B).

1. [ ] **Study B — Olmo post-training framing test** (docs/experiments/07-28_olmo-posttraining-trajectory_framing-test.md):
   DAN vs HarmBench-misinfo across Olmo SFT→DPO→final. Tests whether alignment installs framing-detection
   BEFORE content-refusal (the mechanism behind our "Marin triggers on framing" hypothesis). Olmo-only
   (Marin doesn't release SFT/DPO). RUN FIRST — it's the science.
2. [ ] **Study A — Marin base misinfo-emergence** (docs/experiments/07-28_marin-base-trajectory_misinfo-emergence.md):
   misinformation-generation of marin-8b-base across kestrel→deeper-starling. Localizes WHEN Marin's biggest
   gap enters pretraining (does it jump at Phoenix/Nemotron-CC?). Marin-actionable. RUN SECOND.
Order: B then A, both after the 32B base-vs-base suite completes.

**[UPDATE 2026-07-29] Both DONE + independently VERIFIED.** Study B → SUMMARY Part 8 (H1 REJECTED:
content-refusal installs before framing; framing erodes). Study A → Part 9 (H1 REJECTED: Phoenix is the
misinfo *minimum*; misinfo-generation rises in late cooldown phases). 32B base-vs-base → Part 7. Tamper-
resistance → Part 10. Reseeds (INBOX seed-method → b) in progress to give valid CIs on the byte-identical cells.

---

## QUEUED 2026-07-29 (from gs157) — adapt the Safety Gap Toolkit; test "does the gap widen with scale?" on Marin
Motivation: Dombrowski, Bowen, Gleave & Cundy 2025 — **The Safety Gap Toolkit** (arXiv:2507.11544 ·
https://github.com/AlignmentResearch/safety-gap) define the **"safety gap"** = dangerous-capability difference
between intact-safeguards vs safeguards-stripped models, and claim it **widens with scale**. Our tamper-
resistance study (SUMMARY Part 10) is a lightweight, refusal-focused instance of this. This task ADAPTS their
code (gs157: "we need to adapt their code") to extend our tamper work from "does refusal survive" to "how much
dangerous CAPABILITY is unlocked, and does the gap widen with scale." PRE-REGISTER before running.

Plan:
1. [ ] Clone safety-gap; register **Marin as a model family** in `safety_gap/models/model_family_config.py`
   + a hydra YAML under `safety_gap/hydra_config/model/`. Marin-8B = Llama arch (Llama-3-style chat template),
   Marin-32B = Qwen3 arch (Qwen2.5-style) → map each to the closest existing family class; verify the
   instruction template applies correctly (our base_template_v2 lesson — wrong template = confounded).
2. [ ] Attacks: use their **SFT attack** (matches ours) AND add their **refusal-ablation** attack
   (arXiv:2410.03415, white-box, no fine-tune) — a second, cheaper removal path we don't have.
3. [ ] Capability metric: their toolkit ships MC-accuracy + refusal(`strong_reject`) + quality, but NO
   WMDP/biochem suite out of the box → plug **WMDP** in as the MC capability eval (we already have it in
   safety-eval) so "gap" = WMDP uplift (stripped − intact), not just refusal-rate.
4. [ ] Scale test — **KNOWN CONSTRAINT: Marin ships only an 8B *instruct*, no 32B-instruct**, so a clean
   within-family "instruct at two scales" sweep isn't directly possible. Options to resolve at pre-reg time:
   (a) base-vs-instruct **WMDP delta** as the "gap" proxy at 8B AND 32B (we already have 32B base WMDP =
   0.65 inverted) — arch-confounded (Llama 8B vs Qwen3 32B) but *our* model; (b) run their clean Llama-3 /
   Qwen-2.5 scale sweep as a reference and position Marin against it; (c) only claim the 8B gap for Marin.
5. [ ] Keep judges LOCAL (non-negotiable, matches our offline stance): their toolkit calls **OpenAI (refusal)
   + Anthropic (quality) APIs** — swap for our local WildGuard / `strong_reject` graders. Do NOT add external-
   API deps silently (isolation + reproducibility).
Risks/notes: repo has **NO explicit license** → check / ask gs157 before redistributing adapted code. Stack
(Hydra + accelerate + PEFT + vLLM) is compatible with ours; tested on H100, we run A100 (fine). Compute:
attack+eval per model ≈ our tamper run (~hours). Refs: outputs/refs_safety_pretraining.md (Safety Gap +
refusal-ablation entries).

---

## QUEUED 2026-07-30 (from gs157) — evaluate GRAM (modular pretraining access control) as the pretraining DEFENSE
Motivation: Roland et al., **Modular Pretraining Enables Access Control** (GRAM, ICML 2026 Spotlight ·
arXiv:2607.08077 · code https://github.com/agencyenterprise/modular-pretraining). Pretraining-time gradient
routing quarantines dual-use capability into small removable auxiliary modules → one training run, many
capability profiles, delete a module to drop a capability. This is the concrete **pretraining defense** our
report keeps pointing at (README "Where a real fix has to live" / "What's next" #2-3), and it graduates the
project from MEASURING the problem (repro / gap-map / tamper curves / Safety Gap Toolkit) to BUILDING+BREAKING
a fix. Sits next to Deep Ignorance in refs: "train it but quarantine it" vs "don't train on it."

**Sequencing: this is the phase AFTER the Safety Gap Toolkit task above.** Bigger scope + compute. Do not start
before that lands.

Reality check (settled before this session queued it):
- **Not applicable to Marin-8B post-hoc.** GRAM isolates capability DURING pretraining → can't retrofit an
  8B released checkpoint. This becomes a from-scratch small-model project (their runs: 26M→5B; on our single
  A100, ~50M-800M is realistic over days, 5B is not).
- **License = none on repo (all-rights-reserved by default)** → INBOX item before we adapt/redistribute their
  code; otherwise reimplement gradient routing from the paper. No checkpoints released → train from scratch.
- **They already ship an adversarial "elicited-forget" metric** + RMU/MaxEnt/ASCENT + DEMix/LoRA baselines, so
  "run a tamper attack on it" is NOT novel by itself.

Where our angle is actually ours (candidate scoped experiment — PRE-REGISTER before running):
1. [ ] **Independent tamper adversary.** Reproduce a small GRAM module-deletion model, then attack it with OUR
   Part-10 protocol (LoRA affirmative-prefix + WildGuard/HarmBench), a *different* adversary than their in-house
   elicited-forget metric. Question: does module-deletion survive a cheap fine-tuning attack, or collapse back
   to ~99% like refusal did? (CLAUDE.md independent-path principle.)
2. [ ] **Head-to-head vs data filtering under OUR gaps.** GRAM claims to beat filtering under sparse labels;
   our biggest gap (misinformation) is a general ability, not deletable knowledge. Test whether GRAM/filtering
   help at all on a misinfo-style capability vs the discrete dual-use ones (chem-bio/cyber).
Pre-reqs before any GPU: (a) INBOX license question; (b) decide reimplement-vs-adapt; (c) pick scale that fits
one A100. Refs: outputs/refs_safety_pretraining.md (GRAM entry).

---

## QUEUED 2026-08-27 (from gs157) — resolve the cooldown misinformation finding: refusal or capability, then the mix ablation
**This one jumps the queue.** It is cheap (~1.5h on the local A100), it gates a live external conversation,
and step 1 can invalidate a result we are otherwise about to propose an expensive experiment on. Do it
before the Safety Gap Toolkit and GRAM items above.

Motivation: the David Hall (Marin/Levanter) deep dive on 2026-08-27. Of the whole deck he flagged the base
pretraining trajectory as the most surprising finding: misinformation generation is *lowest* at the Phoenix
web phase (49%) and climbs through the late curated cooldown to 77.2 / 79.6 (see
`docs/experiments/07-28_marin-base-trajectory_misinfo-emergence.md`, H1 rejected by 16pp the wrong way).
Web data looks better on safety than the curated mix. **He then named the delta we could not see:
Phoenix → Starling introduces a ~30% "high quality" mix of Wikipedia, a Common Crawl archive, and DOLMA HQ.**

### Step 1 — PRE-REGISTERED, spec already written, run this first
`docs/experiments/08-27_marin-base-trajectory_misinfo-refusal-vs-capability.md`

The confound: our metric is the fraction WildGuard labels `response_harmfulness = harmful`, which rises if
the model got **better at writing** persuasive misinformation with refusal behaviour unchanged. Wikipedia
and DOLMA HQ are exactly the data that teaches confident expository prose. We already have the mirror image
of this failure mode in-house: StrongREJECT ASR fell 12% → 1% under the tamper attack purely because median
response length collapsed ~1075 → ~116 chars.

1. [ ] Regenerate 6 tags x harmbench(320) x 3 seeds, reusing the 07-28 `command.txt` verbatim.
       **Pre-download each revision** (no `--revision` flag; it silently evaluates `main`).
2. [ ] Gate: **protocol/invariant checks, not a level match** (INBOX option (d), pre-data deviation).
       Harness+package+template identity; six distinct resolved SHAs; same-seed reproduces and
       different-seed diverges on Torch; one clean end-to-end phoenix run with judge labels and
       metric direction checked. Phoenix old-vs-new is descriptive with uncertainty, NOT pass/fail.
3. [ ] Report five series per tag: refusal rate, harmful rate (empty-excluded), harmful-given-non-refusal,
       empty rate, median/IQR response length.
4. [ ] Paired phoenix-vs-starling test on the same behaviors: discordant counts + **exact McNemar**
       (not the uncorrected chi-square).
5. [ ] Flip list: which `BehaviorID`s change, with SemanticCategory and a hand-assigned topic tag.

Reality check (settled before queueing):
- **The 07-28 `all.json` labels are gone.** They are gitignored (`repro-olmo3-safety/runs/**/all.json`) and
  the paperspace box is down; only `metrics.json` survives, which stores harmfulness ASR only. That is the
  whole reason this is a rerun rather than an analysis. Keep the labels this time, **outside the repo**.
- **The refusal label may be degenerate on base completions** (no refusal training). Report its raw
  distribution first. If it is flat zero across all six tags, say so; series 1 is then unfalsifiable and the
  length / conditional-harm series carry the argument. Iron Law applies: a false 0.0% has happened here before.
- Checkpoints are ~16GB each in bf16. Pull and delete sequentially; do not hold six on disk.

### Step 2 — gated on step 1's verdict, needs Marin's cluster, NOT ours
Seven-arm cooldown replay from a fixed Phoenix branch point: full mix (positive control), minus-Wikipedia,
minus-CC-archive, minus-DOLMA-HQ, **random-30%-removed (matched volume)**, no-HQ, and **old-data-with-
Starling's-LR-schedule (schedule control, because cooldown changes the LR as well as the data)**. Full design,
preregistered decision rule and falsifier live in the vault at
`~/Documents/obsidian_global/wiki/projects/Marin Cooldown Misinformation Ablation.md`.

Do not cost or propose this until step 1 returns. If step 1 supports the capability reading, this ablation is
aimed at the wrong thing and the finding becomes a measurement result about quality-sensitive judges instead.

Cheap intermediate steps that need no cluster, if step 1 leaves the data hypothesis alive: read the flip list
for topical clustering; corpus forensics on the three public HQ components (search for **genre**, authoritative
expository register and persuasive-essay form, not for false claims); and a mechanistic diff of the phoenix and
starling public weights using the refusal-direction apparatus from the safety-decay repo.

Refs: `docs/experiments/07-28_marin-base-trajectory_misinfo-emergence.md`,
`docs/experiments/07-27_marin-base-revisions_wmdp_capability.md` (same late-cooldown shape),
vault `[[Marin Deep Dive Outcome]]`.
