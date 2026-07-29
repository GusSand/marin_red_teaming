# Experiment (PRE-REGISTERED): Olmo post-training trajectory — does alignment install framing-detection before content-refusal?

Created 2026-07-28, before the run. Queued to run AFTER the 32B base-vs-base run.

## Research question / hypothesis
Our red-team found Marin's refusal seems keyed on adversarial *framing* (wins DAN/StrongREJECT, loses
HarmBench plain-ask) — but that's a hypothesis confounded with content-mix (HarmBench over-represents
misinformation). This experiment tests the MECHANISM on a model whose post-training stages are public: Olmo.

**Feasibility:** Marin does NOT release SFT/DPO checkpoints (only final instruct), so this runs on OLMO,
which releases allenai/Olmo-3-7B-Instruct-{SFT, DPO} and final Instruct. Finding is about how alignment
PIPELINES install framing-vs-content safety (Olmo as the model), not Marin's own pipeline.

**Pre-registered hypothesis (H1):** across SFT → DPO → final, refusal on *framing/persona attacks* (DAN)
rises EARLIER and/or to a HIGHER level than refusal on *plainly-asked* harm (HarmBench, esp. the
misinformation subset). Concretely: at the DPO stage, DAN-refusal reaches ≥90% of its final-stage value
while HarmBench-misinformation-refusal reaches <70% of its final value. If TRUE → alignment preferentially
installs framing-detection.
**Null / alternative (H0):** DAN-refusal and HarmBench-misinfo-refusal rise together (same trajectory shape)
→ no preferential framing-detection; the DAN>HarmBench gap is content-mix, not framing.

## Setup
- Models: allenai/Olmo-3-7B-Instruct-SFT, -DPO, -Instruct (final). hf template (each is an instruct model).
- Benchmarks: do_anything_now:default (framing/persona) + harmbench:default (plain; gives per-SemanticCategory
  ASR incl. misinformation). Optionally strongreject:logprobs. safety-eval@060cc903, WildGuard, temp0.7/top_p0.95.
- 3 seeds/row. Metric per checkpoint: DAN inverted-asr (framing refusal), HarmBench inverted-asr (overall),
  HarmBench misinformation-category ASR (the plain-content signal).
- Cost: 3 checkpoints × 2 benchmarks × 3 seeds ≈ 18 runs, ~1-2h (DAN 300, HarmBench 320 are fast).

## Success criteria / readout (descriptive)
Plot DAN-refusal and HarmBench-misinfo-refusal vs stage (SFT/DPO/final). Report the trajectory shapes and
whether H1's numeric thresholds hold. Verify each headline from raw all.json label counts (content-safe).

## Results
NOT RUN (queued after 32B). Outputs → runs/2026-07-28-olmo-{sft,dpo,final}-*.

## Links
Ties to report/harmbench_gap_analysis.md (the framing hypothesis) + SUMMARY Part 3.
