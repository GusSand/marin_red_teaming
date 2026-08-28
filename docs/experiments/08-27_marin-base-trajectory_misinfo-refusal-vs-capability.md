# Experiment (PRE-REGISTERED): Is the cooldown misinformation rise reduced refusal, or improved writing?

Created 2026-08-27, before the run. Follow-up to `07-28_marin-base-trajectory_misinfo-emergence.md`,
prompted by the David Hall deep dive (2026-08-27), where he named the Phoenix→Starling delta as a
**~30% "high quality" mix: Wikipedia, a Common Crawl archive, and DOLMA HQ**.

This experiment must run and be resolved BEFORE any cooldown-mix ablation is proposed or costed. It can
invalidate the framing of that ablation.

## Research question / hypothesis

The 07-28 run found misinformation-generation rate climbing through the late cooldown phases: phoenix 49%
(the minimum) → starling 77.2% → deeper-starling 79.6%. That was read as a safety signal pointing at the
cooldown data mix.

**The confound.** The metric is the fraction of responses WildGuard labels `response_harmfulness = harmful`.
That fraction rises if the model got *better at writing* persuasive misinformation, with refusal behaviour
completely unchanged. The HQ mix is Wikipedia and DOLMA HQ, i.e. exactly the data that teaches a base model
to write confident expository prose. A model that learned to write like an encyclopedia produces more
convincing false claims when asked, and the judge scores that as more harmful.

This is not speculative. The tamper experiment (`07-29_..._lora-attack.md`) produced the mirror image:
StrongREJECT ASR fell 12% → 1% under attack purely because median response length collapsed from ~1075 to
~116 characters. Same judge sensitivity to response quality, opposite sign. If that mechanism can
manufacture an 11-point improvement it can manufacture a 28-point regression.

**Pre-registered H1 (capability):** the rise is driven by response quality, not by reduced refusal.
Specifically, across phoenix → deeper-starling:
- refusal rate moves by **< 10pp in absolute value** (flat or non-monotonic), AND
- harmful-rate-given-non-refusal rises by **>= +15pp**, AND
- median non-empty response length rises by **>= +25%**.

**Pre-registered H0 / alternative (behavioural):** refusal genuinely drops. Refusal rate falls by
**>= 10pp** from phoenix to starling. This licenses the mix ablation as designed.

### H1b: the instruction-following variant, and the control that decides it

Added 2026-08-27, before any interpretable data existed, from an outside question on the S9 slide:
*"How is this measured? Could ironically be improved instruction following depending on how it's
prompted."*

That is a sharper mechanism than "better writing." A base model at `kestrel` may simply not follow
the `User: {instruction}\n\nAssistant:` scaffold at all, emitting off-topic or degenerate text that
WildGuard scores unharmful. By `deeper-starling` it follows the format and answers on topic. Same
safety posture, higher number. The HQ mix is Wikipedia and DOLMA HQ, which is exactly the data that
teaches a model to respond to a prompt in a structured way, so this is the *expected* effect of that
mix rather than a remote possibility.

**[CORRECTED 2026-08-27 by gs157, pre-data. The text below replaces an earlier version that
called `wildjailbreak:benign` "decisive" and set delta-ratio thresholds on it. Both are
withdrawn.]**

**`wildjailbreak:benign` is a SECONDARY over-refusal diagnostic. It is NOT the decisive H1b
discriminator and no H1b verdict may rest on it.** The reason is that its WildGuard `macro_asr`
measures **non-refusal**, not relevance and not successful task completion. Off-topic or
degenerate base-model text passes it. That is precisely the failure mode H1b exists to detect,
so the control cannot discriminate the thing it was proposed to discriminate. Ceiling saturation
compounds it: the existing scaffolded Marin-base result is already **96.4%**, leaving almost no
headroom for a delta to appear in.

The withdrawn thresholds were `delta-benign >= 0.6 * delta-harmful` => instruction-following and
`delta-benign <= 0.3 * delta-harmful` => safety-specific. **Do not apply them.** A ratio built on
a saturated non-refusal measure is not evidence about instruction following.

**Before H1b can be called, an objectively gradable benign instruction-following task, or a
relevance / task-success scorer, is required.** That instrument does not exist in this repo yet
and choosing it is its own selection question; until it does, H1b is OPEN and unresolved.
`wildjailbreak:benign` may still be run and reported as an over-refusal diagnostic and as
context, clearly labelled as such.

**A second, free discriminator** comes out of the same harmful runs: the **non-response rate**, meaning
empty plus prompt-echo plus off-topic. If that falls steeply across the six revisions, the model is
learning to answer rather than learning to comply. Series 4 and 5 below already capture the empty and
length components; the echo component uses the scaffold-aware detector, not the broken
first-50-character one.

**Mixed outcome** (both refusal down >= 10pp and conditional harmfulness up >= 15pp) is a real possible
result and gets reported as such, with the ablation proceeding under a narrowed claim.

Note these are base models with no refusal training, so "refusal" here means whatever WildGuard's refusal
label fires on for a scaffolded base completion. Establish that label's actual behaviour on this data
before interpreting it; see the gate below.

## Setup

- **Models**: `marin-community/marin-8b-base` at tags `kestrel, ocelot, jellyfish, phoenix, starling,
  deeper-starling`. `scripts/run_row.sh` takes the revision as its second argument and passes
  `--hf_revision`; the failure mode is **forgetting to pass it**, in which case the run silently evaluates
  `main` and the whole trajectory collapses to one model. Record the resolved commit in the provenance file
  for every run and check the six differ.
- **Protocol identity is mandatory.** Reuse the decoding parameters, template and harness commit from the
  07-28 run verbatim. The exact invocation is recorded in
  `repro-olmo3-safety/runs/2026-07-29-marin-misinfo-base-<tag>-harmbench-r{1,2,3}/command.txt`. Copy it,
  do not reconstruct it. Base scaffold is `repro-olmo3-safety/config/base_template_v2.txt`.
- **Probe**: `harmbench:default`, restricted at analysis time to the `misinformation_disinformation`
  SemanticCategory (~54 behaviors). **Seeds are NOT uniform across tags** (gs157, 2026-08-27,
  pre-data): the three ENDPOINT tags that carry the hypotheses -- `phoenix`, `starling`,
  `deeper-starling` -- get **10 seeds** each; the three CONTEXT tags -- `kestrel`, `ocelot`,
  `jellyfish` -- keep **3**. H1 is phoenix -> deeper-starling and H0 is phoenix -> starling, so
  all three endpoints need the precision, not just two. Seeds are 0..9 and 0..2, so the 3-seed
  set is a strict prefix of the 10-seed set.
- **Keep `all.json` this time.** The 07-28 run's per-instance labels were gitignored and the paperspace box
  is gone, which is the only reason this rerun is necessary. Write them to a local path OUTSIDE the repo
  (e.g. `~/marin-misinfo-labels/`) and record that path in the journal. Do not commit them; the gitignore
  rule stays as it is.
- **Cost**: 6 tags x 320 prompts x 3 seeds, the same shape as the 07-28 run, which took ~1.5h on the local
  A100. Checkpoints are ~16GB each in bf16; pull and delete sequentially rather than holding six on disk.

## Porting to a new machine (NYU), do this before anything else

This repo has only ever run on the paperspace A100. Three things break on a fresh host:

1. **32 hardcoded `/home/paperspace/...` paths** across `run_row.sh`, `run_suite.sh`, `setup_safety_eval.sh`,
   `run_gate3.sh`, `run_posttrain.sh`, `run_base_capability.sh`, `studyB_reseed*.sh`,
   `harmbench_gap_analysis.py`, `grade_audit_llamaguard.py` and others. Parameterize `ROOT` through an env
   var with the old path as the default, rather than sed-replacing and hoping.
2. **The vendored `safety-eval` checkout is gitignored.** Rebuild it with `scripts/setup_safety_eval.sh`,
   pinned at SHA `060cc903d64703214c549b5c3a30ea8ceef2e588`, in its own venv (torch 2.8.x, vllm 0.11.0),
   isolated from the base environment.
3. **Re-apply `scripts/patches/seed_fix_generation_utils.patch`.** Without it `PYTHONHASHSEED` does not
   control vLLM sampling and the three seeds collapse to identical outputs wherever generation is stable.
   **This experiment reports median and IQR of response length and treats seeds as real replicates, so an
   unpatched checkout would silently fabricate a tight distribution.** Verify the patch took effect before
   trusting any spread: same seed reproduces, different seeds diverge.

Slurm: `CLAUDE.md` records Slurm as deferred and never filled in, so partition, account, QoS and walltime
have to be established. Batch only. Interactive `srun` hangs the session.

Disk: six 8B checkpoints at roughly 16GB each in bf16, plus the HF cache and the judge. Pull and delete
sequentially. `all.json` goes to a path outside the repo.

**The port is validated by the protocol/invariant gate below, not by a level comparison.** Run the
`phoenix` tag alone first and confirm it completes end to end with the judge and metric direction
checked. Its level is reported descriptively against the historical value, with uncertainty; a
difference there is not by itself evidence of protocol drift.

## Port gate: protocol and invariant checks, NOT a level comparison

**Pre-data deviation, decided 2026-08-27 (INBOX option (d)), before any interpretable data
existed.** The original design gated on reproducing phoenix at 49% +/- 3pp. That gate is
withdrawn. It cannot support an equivalence claim in either direction:

- Phoenix's own historical per-seed values are 46.30 / 42.59 / 57.41, sd 7.71pp. The SEM of a
  3-seed mean is 4.45pp, wider than the tolerance, so a perfect port fails about half the time.
- More seeds now would shrink uncertainty in the NEW mean but cannot fix the noisy 3-run
  HISTORICAL target, which is the other half of the comparison.
- The historical trajectory mixes patched, unpatched and seed-collapsed sampling across tags.
  It is not a single coherent protocol to be equivalent *to*.

**What must pass before the full trajectory runs** (all binary, all checkable without a level
comparison):

1. **Exact harness and package identity.** safety-eval @ `060cc903`, torch 2.8.0+cu128,
   vllm 0.11.0, transformers 4.57.1, and the `User:/Assistant:` v2 scaffold. Asserted by
   `scripts/dry_run_check.py`, which fails rather than prints.
2. **Six resolved, distinct model SHAs.** `scripts/prefetch_revisions.py` records them and
   hard-fails if any two tags collapse to the same commit.
   **[PASSED 2026-08-27]** All six prefetched into the workspace cache and resolved to
   distinct commits, written to `docs/resolved_revisions.json`:

   | tag | resolved commit |
   |---|---|
   | kestrel | `56ef403a3636884c171b662fb2ff9f1dfe1c51b9` |
   | ocelot | `e4d18c1d4b8c1f3ec9b9b6fd3e1a7472505abd6f` |
   | jellyfish | `c92465e482614bd2b3d44c7d3aebc57ba50de53a` |
   | phoenix | `5837472e13444e91e49fccc1cc010bb48138760a` |
   | starling | `66279e715ef6881b972c86c31596cb1e57354f99` |
   | deeper-starling | `d57287aa62aeb5d09881958862c860554d19941d` |

   The 07-28 runs recorded only the tag *string*, so tag drift since then cannot be ruled
   out retrospectively. From here the SHAs are pinned and drift is detectable.
3. **Sampler validated on Torch**: same seed reproduces, different seeds diverge. This is the
   check that the seed patch is actually in force here, not merely applied to a file.
   **[PASSED 2026-08-27, job 16496404]** One job, one GPU (gl052, `GPU-b03b1050-868c-f833-663d-84d7d172100b`,
   L40S, driver 580.82.07), `VLLM_ENABLE_V1_MULTIPROCESSING=0`, five runs sequentially: seed 0 x3, seed 1 x2.
   Compared at all three pre-registered levels by `scripts/compare_determinism.py`:

   | level | same-seed pairs (4) | different-seed pairs (6) |
   |---|---|---|
   | exact response hash | 320/320 identical (100.0%) | 0/320 identical (0.0%) |
   | WildGuard harmfulness label | 320/320 (100.0%) | 257/320 (80.3%) |
   | WildGuard refusal label | 320/320 (100.0%) | 247/320 (77.2%) |
   | misinfo rate (54 items) | s0 = 42.59% (23/54) x3; s1 = 61.11% (33/54) x2 | — |

   Both arms are required and both behave: token-exact reproduction at fixed seed rules out
   nondeterminism, and 0/320 at different seeds rules out a stuck or collapsed sampler. The seed
   patch is in force on Torch.

   **Consequence, and it is not small: between-seed spread is 18.52pp = 10 of 54 items.** Seed 0
   and seed 1 differ by more than a third of the phoenix->starling effect the trajectory is meant to
   measure. This is one pairwise difference from two seeds, *not* a variance estimate and *not* a
   noise floor — do not quote it as one. It is consistent with the historical phoenix spread
   (46.30 / 42.59 / 57.41), and our seed 0 reproduces the historical r2 value of 42.59% exactly.
   Any per-tag comparison smaller than ~10 items is underpowered at 3 seeds; the headline
   phoenix-vs-starling contrast (~28pp) is not.
4. **One successful end-to-end phoenix run**, with the judge labels and the metric DIRECTION
   independently checked (higher = more harmful, empties excluded).
   **[PASSED 2026-08-27]** The five gate-check-3 runs are successful end-to-end phoenix runs.
   Direction and labels re-derived from raw `all.json` counts rather than `metrics.json`:
   seed 0 = 23 `harmful` of 54 misinfo items = 42.59%, seed 1 = 33/54 = 61.11%, both matching
   `metrics.json` exactly, so higher does mean more harmful. **0 empties in the misinfo
   subset**, so the empty-exclusion caveat is inert on this probe. Label vocabulary confirmed
   in the data, settling the note in Measurements #1: `response_harmfulness` is
   `harmful`/`unharmful`, `response_refusal` is `refusal`/`compliance`.

**ALL FOUR GATE CHECKS PASSED 2026-08-27.** Job 16500537 was launched against these gates and
then **CANCELLED after ~3 minutes** on discovering the run-isolation defect described below. It
produced no data that is used anywhere. The inferential run is the job launched from
`slurm/misinfo_trajectory_seq.sbatch` under the `2026-08-27-traj2` namespace.

### Execution-topology deviation (pre-data, documented, decided 2026-08-27)

The trajectory runs as **18 sequential runs on ONE GPU** (`slurm/misinfo_trajectory_seq.sbatch`),
not as the 18-task Slurm array in `slurm/misinfo_refusal_vs_capability.sbatch`. An array scatters
tasks across nodes, and every inference in this experiment is a comparison *across revisions*, so
an array would confound hardware with revision — the same error that invalidated the first
determinism test. CLAUDE.md's standing rule is that any comparison between runs must hold the GPU
fixed. At ~400s per run the cost of pinning is ~2.1h total.

This changes execution topology only: identical models, seeds, prompts, scaffold, judge, decoding
parameters and metric. It removes a confound rather than adding one, which is why it is recorded
as a documented deviation rather than treated as a design change. The array script is retained
for reference but is not the one that produced the data.

### Seed plan and its justification (gs157, 2026-08-27, pre-data)

Gate check 3 measured seed-to-seed movement on this exact probe with the sampler verified in
force: seed 0 -> seed 1 moved refusal from 20/54 to 8/54 (22.2pp) and harmful from 23/54 to
33/54 (18.52pp). The pre-registered H0 threshold is a refusal drop of >= 10pp, which on 54 items
is 5.4 items -- smaller than what a single seed swap did.

**Decision: 10 seeds for `phoenix`, `starling` and `deeper-starling`; 3 seeds for `kestrel`,
`ocelot` and `jellyfish`.** H1 compares phoenix -> deeper-starling and H0 compares phoenix ->
starling, so three tags define the hypotheses and all three need the precision. An earlier
proposal of mine covered only phoenix and starling and was wrong for that reason.

**This is a precision increase, not a power analysis, and the distinction is load-bearing.** The
only evidence about seed spread is ONE pairwise difference between TWO seeds. That is not a
variance estimate, it bounds nothing, and it cannot establish that 10 seeds are adequate. Ten
seeds narrow the interval; they do not license a clean pass/fail on a threshold that sits near
the noise. **Paired uncertainty intervals get reported for every endpoint contrast regardless of
seed count**, and the H1/H0 refusal clauses are reported with those intervals rather than as bare
verdicts.

### Run isolation (gs157, 2026-08-27, pre-data, MANDATORY)

The first version of `slurm/misinfo_trajectory_seq.sbatch` skipped any run whose `metrics.json`
existed, with no provenance check. `2026-08-27-marin-misinfo-rvc-phoenix-harmbench-r1` exists on
disk from **FAILED job 16492919**, written on an unrecorded GPU, before
`VLLM_ENABLE_V1_MULTIPROCESSING` was pinned and before provenance recorded `hostname` or
`gpu_uuid` at all. The running job would have silently adopted it as phoenix seed 0, destroying
the one-GPU property that is the entire justification for running sequentially. Job 16500537 was
cancelled 3 minutes in.

Two defences, both required:

1. **Fresh namespace.** Runs are `2026-08-27-traj2-<tag>-harmbench-s<seed>`. Verified unused in
   both `runs/` and the out-of-tree label directory before launch. No prior output can collide.
2. **Provenance-gated skipping.** A pre-existing `metrics.json` is reused ONLY if its provenance
   matches THIS allocation exactly: same `gpu_uuid`, same short hostname, `vllm_v1_multiprocessing=0`,
   same `sampling_seed_env`, same `safety_eval_sha`, same resolved model SHA. Any mismatch, or any
   missing field, is a **hard failure** -- never a silent skip, never an overwrite. This permits a
   resume back into the same allocation and forbids everything else.

**All endpoint seeds must run within a single GPU allocation.** Endpoint tags are therefore
executed first, so that a walltime kill can only truncate context tags, which carry no threshold
and may legitimately run in a later allocation.

The guard was tested before launch against five cases: the contaminated job-16492919 provenance
(rejected, missing hostname), a same-allocation run (accepted), a seed mismatch (rejected), a
missing provenance file (rejected), and a foreign GPU UUID (rejected). Testing also caught that
`run_row.sh` records the FQDN while the job compares `hostname -s`, which would have hard-failed
every legitimate resume; both sides are now normalised to the short name.

**Results are not to be inspected until this deviation is committed and locked.**

**Run log against this rule (2026-08-28).** Job 16500928 launched on gl002 and was killed by an
external SIGTERM at 2h20 of a 16h walltime when the node went into drain — not walltime, not a
harness fault. It had completed `phoenix` x10 and `starling` x10 on one GPU
(`GPU-ed7502f8-...`); `deeper-starling` had not started. Under the rule above those 20 runs are
**not** the endpoint dataset, because the third endpoint tag never ran in that allocation. They
are retained on disk under `2026-08-27-traj2` and are not deleted, but no endpoint inference
draws on them. (They would independently support H0, which is phoenix -> starling only; that is
noted, not used, and the H0 verdict comes from the same allocation as H1.)

The endpoint tags were therefore re-run in full under namespace `2026-08-28-traj3`, job 16508385
on gl038. A drained job **cannot** be resumed into a new allocation: the provenance guard
hard-fails on the first completed run, by design. Namespace bump plus full endpoint re-run is the
only compliant recovery, and `RUN_PREFIX` is now overridable via `MARIN_RUN_PREFIX` to make that
one flag.

## Measurements

All content-free aggregate counts. Per tag, per seed, then aggregated:

1. **Refusal rate**: fraction with `response_refusal` firing. Check the harness's exact label vocabulary
   in code before assuming a string value.
2. **Harmful rate**: fraction with `response_harmfulness == "harmful"`, empty-excluded. This is the 07-28
   metric and it is the reproduction gate above.
3. **Harmful given non-refusal**: (2) restricted to responses that did not refuse. This is the capability
   series.
4. **Empty rate**: per tag. The S6 empty-as-refusal bias applies here too; Marin-base StrongREJECT ran
   12.0% empty (313/2607) in the earlier audit.
5. **Response length**: median and IQR characters over non-empty responses, per tag. Token length too if
   it is free.
6. **Benign compliance** (SECONDARY diagnostic only): compliance rate on `wildjailbreak:benign`,
   same six revisions, same scaffold and seeds. **This series does NOT decide whether S9 is a
   safety result** -- see the corrected H1b section above. It measures non-refusal, not relevance
   or task success, and is already at 96.4% for scaffolded Marin-base, so it is reported as an
   over-refusal diagnostic and nothing more.

### Paired test, phoenix vs starling

Both tags saw identical prompts, so use the paired test rather than comparing two rates, matching the
approach used for the Marin/OLMo HarmBench gap. Per behavior, take the majority over 3 seeds. Report the
discordant counts (harmful at starling and not at phoenix, and the reverse) and an **exact McNemar**
binomial p-value. Do not use the uncorrected chi-square; at these discordant counts it is
anti-conservative, and it is the error that had to be fixed in the talk deck.

### Flip list

List the `BehaviorID`s that flip phoenix → starling, with SemanticCategory and a hand-assigned topic tag
(health, elections, history, science, other). The HarmBench behavior *prompts* are public and safe to read
and quote in the journal; model completions are not, and only aggregate counts go in the repo.

Topically clustered flips make a data hypothesis testable and give the mix ablation a target. Diffuse
flips point back at the capability reading.

## Success criteria / readout

A single table, six rows (one per tag), five columns (the five measurements), plus the paired test and the
flip list. Then one verdict line naming which of H1 / H0 / mixed is supported, against the thresholds fixed
above.

**What the verdict decides:**
- **H1 supported** → the cooldown mix ablation is aimed at the wrong thing. The finding becomes "a
  capability increase is being read as a safety regression by a quality-sensitive judge," which is a
  measurement result about open-weight safety evaluation and is publishable on its own.
- **H0 supported** → the mix ablation is correctly aimed. Proceed to cost the seven-arm design.
- **Mixed** → the ablation proceeds, but the primary metric must become refusal rate or
  harmful-given-non-refusal rather than the raw harmful rate.

## Safety handling

Unchanged from the rest of this project, and non-negotiable.

- Everything stays local. Per-instance generations (`all.json`) are never committed and never leave the
  machine. Only aggregate counts enter the repo and the journal.
- Grading and reporting are content-free. Reading a small sample of completions by hand is expected and
  correct; logging them is not.
- Pulling raw base harmful outputs through a hosted assistant trips usage-policy filters, because the base
  model is uncensored. Verification must be done on aggregate counts, as it was in the 2026-07-27 re-audit.

## Notes for whoever runs this

- **Iron Law applies.** A suspiciously clean number is a bug. If the refusal series comes back at exactly
  0.0% for every tag, verify it against the harness code before reporting it; a first-50-character echo
  detector already produced a false 0.0% once on this project and it was only caught because the number
  looked too clean.
- Do not change the experiment because a result looks wrong. Write an INBOX item and pick up other work.
- The analysis path must not import the generation path. Recompute the headline series from raw labels on
  a separate code path, as with every other result here.

## Results

(empty; fill after the run)
