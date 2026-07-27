# Task 1: reproduce Olmo 3 7B safety numbers

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
