# Experiment (PRE-REGISTERED): Marin base pretraining trajectory — when does misinformation-generation emerge?

Created 2026-07-28, before the run. Queued to run AFTER the 32B base-vs-base run (and Study B).

## Research question / hypothesis
Marin's single biggest instruct-level safety gap is misinformation (HarmBench misinfo ASR 30.2 vs Olmo 15.4).
The raw material for that must enter during pretraining. This localizes WHEN, across Marin's base phases —
directly actionable (which data/phase to change), and complements the WMDP base-revision diagnostic (which
found dual-use knowledge tracks scientific-cooldown data, NOT the Nemotron-CC web switch).

**Pre-registered hypothesis (H1):** the base model's tendency to *produce persuasive misinformation* on demand
increases across pretraining and JUMPS at the phase that adds the most web text (Phoenix, +Nemotron-CC), i.e.
misinfo-generation(phoenix) − misinfo-generation(jellyfish) ≥ +5pp.
**Null:** flat or non-monotonic / not concentrated at Phoenix (as happened for WMDP bio/chem — a real possibility;
misinfo-generation may track a different phase or none cleanly).

## Setup
- Model: marin-8b-base @ tags kestrel, ocelot, jellyfish, phoenix, starling, deeper-starling.
- Probe: harmbench:default (scaffold-prompted base), restricted to the misinformation SemanticCategory (~54
  behaviors), measuring fraction of responses WildGuard labels HARMFUL = "produced persuasive misinformation."
  (Capability probe — base has no refusal training, so measure generation tendency, not refusal.)
- 3 seeds/tag. CONTENT-SAFE (counts only). Report empty-response % per tag (empties confound; exclude them:
  misinfo-rate among NON-empty responses).
- Cost: 6 tags × harmbench(320) × 3 seeds ≈ 18 runs, ~1.5h (8B base, fast).

## Success criteria / readout (descriptive)
Plot misinfo-generation rate (empty-excluded) vs pretraining phase. Report whether H1's Phoenix-jump holds or
is rejected (like the WMDP hypothesis was). Verify from raw label counts. Cross-check: does the trajectory
track a web-data phase (Nemotron-CC at Phoenix) or a curated/cooldown phase (Jellyfish/Starling)?

## Results
NOT RUN (queued). Outputs → runs/misinfo-base-<tag>.

## Caveats
Base numbers confounded by empties + no refusal training; this is a generation-capability probe, not "safety."
Arch is fixed (8B Llama) across tags → cleaner than the 8B→32B arch-confounded comparison.

## Links
Complements docs/experiments/07-27_marin-base-revisions_wmdp_capability.md; feeds outputs/marin_pretraining_safety_proposal.md.
