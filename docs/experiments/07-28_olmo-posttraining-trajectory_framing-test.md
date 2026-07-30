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
RAN 2026-07-28/29. VERIFIED — all 18 runs recompute exactly from raw all.json.
Outputs → runs/2026-07-28-olmo-{sft,dpo,final}-*. Reseeded 3-seed mean ± std.

| inverted-ASR % (↑=safer) | SFT | DPO | final |
|---|---|---|---|
| DAN (framing refusal) | 87.3 ± 2.3 | 81.6 ± 3.5 | 73.4 ± 1.8 |
| HarmBench misinfo (content refusal) | 67.3 ± 8.6 | 88.9 ± 1.5 | 86.4 ± 5.7 |

**H1 REJECTED.** H1 predicted framing-detection (DAN) is installed before content-refusal. The opposite holds.
Content/misinformation refusal is essentially complete by the DPO stage (67.3 → 88.9), while framing-attack
robustness erodes monotonically across SFT → DPO → final (87.3 → 81.6 → 73.4).

Seed fix (INBOX 2026-07-29 item b): the original run had byte-identical seeds on SFT-HarmBench, which
understated that CI. Reseeded with the fixed sampler (scripts/patches/seed_fix_generation_utils.patch); all
cells now have 3 distinct seeds. Reseeded point estimates match the originals within ~1–3pp, so the
H1-rejected finding is unchanged. Sanity check: final ≈ the separately-measured Olmo-3-7B-Instruct baseline
within ~1.5pt.

Write-up: repro-olmo3-safety/report/SUMMARY.md Part 8.

## Links
Ties to report/harmbench_gap_analysis.md (the framing hypothesis) + SUMMARY Part 3.
