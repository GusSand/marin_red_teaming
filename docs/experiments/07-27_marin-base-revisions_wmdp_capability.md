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

## Results (2026-07-27) — VERIFIED
WMDP logprob-MC across base revisions (chance=25%; bio n=1273, chem 408, cyber 1987):
| phase | bio | chem | cyber |
|---|---|---|---|
| kestrel | 23.9 | 23.5 | 49.1 |
| ocelot | 24.8 | 22.5 | 48.0 |
| jellyfish | 28.8 | 28.2 | 49.9 |
| phoenix (+Nemotron-CC) | 26.1 | 26.2 | 48.4 |
| starling | 30.3 | 27.9 | 49.7 |
| deeper-starling | 29.5 | 27.9 | 50.1 |
Verification: deeper-starling bio independently recomputed from preds.jsonl = 29.5% (MATCH). Cyber >> chance
confirms the scorer is valid.

**Verdict: pre-registered hypothesis REJECTED.** Bio does NOT jump at Phoenix (Nemotron-CC): phoenix bio (26.1)
< preceding jellyfish (28.8). Bio/chem knowledge rises at the SCIENTIFIC/high-quality COOLDOWN phases
(jellyfish: peS2o+ArXiv+FineMath; starling), not at the raw-web Nemotron-CC introduction. Cyber is flat ~49%
(well above chance) from kestrel — it comes from code (StarCoder), present from the start. Bio/chem are weak
overall (~28-30% vs 25% chance) → 8B base holds little hazardous bio/chem knowledge.
**Implication (revises proposal):** bio/chem filtering target = scientific-paper streams (peS2o/ArXiv/FineMath),
NOT Nemotron-CC; cyber = code (StarCoder), filter early. Caveat: bio/chem deltas small/near-chance (partly noisy);
pattern consistent across bio+chem.

## Scale extension (2026-07-27) — marin-32b-base main, VERIFIED
WMDP (chance 25): bio 8B=29.5 -> 32B=33.4 (+3.8); chem 27.9 -> 29.4 (+1.5); cyber 50.1 -> 52.3 (+2.2).
Verify: 32B bio recompute from preds = 33.4 (MATCH). CAVEAT: 8B=Llama lineage, 32B=Qwen3 arch — the delta
conflates scale + architecture, NOT a clean scale ablation.
**Read:** dual-use knowledge scales GENTLY (+2-4pp), not a cliff. Even at 32B, bio/chem remain modest
(33/29% vs 25% chance) — Marin base holds limited bio/chem hazard knowledge at these scales; cyber ~52%
(code-derived) both sizes. For the 1T question: the 8B->32B trend is gentle, so no explosive dual-use
capability jump expected at frontier from this trajectory — but a controlled same-recipe scale sweep (and 1T
itself) would be needed to confirm; the arch confound here limits the claim.
