# Experiment: dangerous-capability (WMDP) across Marin-8b-base revisions

Created 2026-07-27, before the run. Pre-registered.

## Research question / hypothesis
Does the base model's hazardous knowledge (WMDP bio/chem/cyber) increase across Marin's pretraining
phases, and specifically **does it jump at Phoenix**, where Nemotron-CC (Common Crawl at scale) is
introduced? If yes, the Phoenix Nemotron-CC subset is the highest-leverage filtering target for the
pretraining-safety proposal (outputs/marin_pretraining_safety_proposal.md).

## Why base, why logprob-MC (methodology correction)
- BASE models, not instruct: capability is a base property; refusal (instruct) is a separate, strippable layer.
- **Logprob-based MC scoring, NOT generate+regex.** safety-eval's WMDP is generation+parse, which under-counts
  base models that can't emit "the answer is X" format (we saw Marin-base WMDP err 64% > instruct 48% — a format
  artifact, not less knowledge). Logprob-MC = pick argmax over the 4 choices' continuation logprob given the
  question. Pure knowledge probe, format-independent.

## Setup
- Model: `marin-community/marin-8b-base` at tags: kestrel, ocelot, jellyfish, phoenix, starling, deeper-starling
  (also raccoon). Data recipe (marin-8b-retro): Kestrel/Ocelot=DCLM+StarCoder+Proofpile2; Jellyfish=Dolmino/FineMath;
  **Phoenix=+Nemotron-CC**; Starling/Deeper-Starling=70% Nemotron-CC.
- Data: cais/wmdp {wmdp-bio 1273, wmdp-chem 408, wmdp-cyber 1987}.
- Metric: accuracy (argmax choice-logprob) and length-normalized acc_norm, per subject + overall. Chance=25%.
- Runs after Olmo-Think (shares the A100). Download→eval→delete each revision to manage disk (~16G each).
- Deterministic (logprob scoring, no sampling); seed not applicable.

## Success criteria (pre-registered — these are descriptive, not pass/fail)
- Primary readout: WMDP-bio/chem/cyber accuracy vs pretraining phase.
- Hypothesis PRE-REGISTERED: Phoenix (post-Nemotron-CC) shows a higher WMDP-bio than Jellyfish/Kestrel
  (pre-Nemotron), Δ ≥ 3pp, and deeper-starling ≥ phoenix. If confirmed → Nemotron-CC is a filtering target.
  If flat across revisions → dangerous knowledge is not concentrated in the Nemotron-CC switch (reject hypothesis).
- Sanity gate: kestrel accuracy should be well above chance (25%) or the logprob-MC harness is broken.

## Verification
- Recompute overall accuracy a 2nd way (independent count from saved per-item predictions) before logging.
- Cross-check one revision's WMDP-bio against a published Marin/DCLM number if available.

## Results
NOT RUN (staged to launch after Olmo-Think). Outputs → runs/wmdp-base-<tag>/.

## Links
- Proposal: outputs/marin_pretraining_safety_proposal.md
- Scripts: scripts/base_capability_wmdp.py, scripts/run_base_capability.sh
