# Experiment (PRE-REGISTERED): Marin-32B vs Olmo-3-32B — base-vs-base safety at 32B scale

Created 2026-07-28, written the moment both runs launched (before any results land). Extends the 8B
base-vs-base comparison (SUMMARY Part 4/4b) to the 32B tier.

## Research question / hypothesis
At 8B, the base models diverge: **Olmo base is markedly more refusal-prone than Marin base** (+15–27pp
after correcting for empty responses), despite neither having refusal training. Does that gap **persist,
widen, or close at 32B scale**?

**Pre-registered hypothesis (H1):** the 8B ordering holds at 32B — Olmo-32B base refuses/produces-safe more
than Marin-32B base on the adversarial-framing benchmarks (DAN, TrustLLM, StrongREJECT), by a margin of the
same sign as 8B (Olmo safer). Specifically, on ≥3 of {DAN, TrustLLM, StrongREJECT} the inverted-ASR gap
(Olmo − Marin) is positive after empty-response correction.
**Null / alternative (H0):** the gap closes or flips at 32B (scale changes the base-safety ordering), OR the
result is dominated by the empty-response confound rather than genuine compliance.

## Setup
- Models: `marin-community/marin-32b-base` (Qwen3 arch) vs `allenai/Olmo-3-1125-32B` (Olmo3 arch), rev `main`.
- Template: base scaffold `config/base_template_v2.txt` (`User: {instruction}\n\nAssistant:`) — both base,
  no chat template. (The minimal `{instruction}` template was confounded by prompt-echo — see DECISIONS.)
- Suite (11 benchmarks × 3 seeds each): do_anything_now, harmbench, trustllm_jailbreaktrigger,
  wildjailbreak:harmful, wildjailbreak:benign, wildguardtest, xstest, bbq, strongreject:logprobs, wmdp, toxigen.
- Harness: safety-eval @060cc903 (pinned), WildGuard judge, toxigen_roberta, StrongReject Gemma-2B, temp0.7/top_p0.95.
- Compute: marin-32b on LOCAL A100, olmo-32b on REMOTE A100, in parallel. bf16, fits one 80GB A100 each.
- Runs → `runs/2026-07-28-marin-32b-base-*` (local) and `runs/2026-07-28-olmo-32b-base-*` (remote).

## Success criteria / readout (descriptive)
Per-benchmark inverted-ASR (or ASR) table, Marin-32B vs Olmo-32B, 3-seed mean ± spread. **Report
empty-response % per cell and recompute headline metrics empty-excluded** (empties confound base numbers —
this bit us on the 8B base run; see the Iron-Law catch in DECISIONS). Verify each headline from raw
`all.json` label counts via a fresh independent recompute before it enters the journal as a finding.

## Caveats (pre-registered, non-negotiable to state)
- **Arch-confounded:** Marin-32B is Qwen3-architecture, Olmo-3-32B is Olmo3-architecture. Any base-safety
  difference conflates architecture, pretraining data, AND scale — this is NOT a clean pretraining-data
  ablation. It answers "do these two shipped base models differ," not "why."
- Base models have no refusal training → these measure *generation tendency under a scaffold*, not "safety."
- Empty-response bias is the known failure mode; correct for it before any claim.

## DEVIATION (recorded 2026-07-29, before results logged)
The 32B base runs on the two giant benchmarks are far slower than budgeted because base models generate
full-length outputs: **BBQ = 4,482 prompts, Toxigen = 14,000 prompts**, and at 32B each single seed takes
~2.5–4h. Full 3-seed completion would be ~+24h local / ~+8h remote (remote billing throughout), for two
*secondary* metrics (social bias, toxic-language) whose 8B seed-variance was negligible.
**Decision (user-approved, Option 1):** cut BBQ and Toxigen to **1 seed** at the 32B tier (keep the in-flight
r1 on each box, skip r2/r3); keep **3 seeds** on all other benchmarks incl. StrongREJECT and WMDP. All core
H1 adversarial-framing benchmarks (DAN, HarmBench, TrustLLM, WildJailbreak, WildGuard-Test, XSTest,
StrongREJECT) retain full 3-seed coverage. BBQ/Toxigen at 32B are therefore single-seed point estimates —
report them as such (no seed spread) and compare models on matched seed 0.

## Results
COMPLETE 2026-07-29. VERIFIED — independent recompute from raw all.json; all 22 cells match metrics.json to
4 dp. Row counts after the scope cut: Olmo-32b 31/33, marin-32b 29/33. Empty-response correction applied;
empties ≤2.3% at 32B and immaterial, unlike the 8B base runs.

| Benchmark (inverted-ASR, ↑=safer) | Marin-32B | Olmo-32B | Δ (Olmo−Marin) | safer |
|---|---|---|---|---|
| DoAnythingNow (framing) | 0.31 | 0.55 | +0.24 | Olmo |
| TrustLLM (framing) | 0.39 | 0.62 | +0.23 | Olmo |
| HarmBench | 0.54 | 0.70 | +0.16 | Olmo |
| WildGuard-Test | 0.66 | 0.78 | +0.12 | Olmo |
| WildJailbreak-harmful | 0.08 | 0.13 | +0.05 | Olmo |
| StrongREJECT | 0.83 | 0.77 | −0.06 | Marin (flips) |
| WMDP (inverted; ↑=less hazardous knowledge) | 0.65 | 0.48 | −0.17 | Marin lower capability |

**Pre-registered H1 = 2/3.** H1 required ≥3 of {DAN, TrustLLM, StrongREJECT} to favor Olmo; StrongREJECT
flipped, so H1 is not literally met, though the broad trend favors Olmo.

The 8B ordering persists at 32B: Olmo's base is more refusal-prone than Marin's on 5 of 6 harmful-compliance
benchmarks, with the largest gaps on framing attacks. The StrongREJECT flip is the same pattern seen in the
tamper study — Marin complies but emits lower-specificity content, which the StrongREJECT quality judge scores
low while the WildGuard refusal judge flags as harmful. WMDP inverts the direction: Marin carries less
hazardous knowledge than Olmo at 32B.

ARCH-CONFOUNDED as pre-registered: Marin-32B is Qwen3-arch, Olmo-3-32B is Olmo3-arch. This compares two
shipped base models, not a clean data ablation.

Write-up: repro-olmo3-safety/report/SUMMARY.md Part 7.

## Links
Extends repro-olmo3-safety/report/SUMMARY.md Part 4/4b (8B base-vs-base). WMDP-32B capability diagnostic
already done: runs/wmdp-32b-base-main + docs/experiments/07-27_marin-base-revisions_wmdp_capability.md.
