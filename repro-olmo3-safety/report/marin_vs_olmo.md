# Marin-8B vs Olmo-3-7B — safety comparison (red-team)

Same validated harness (safety-eval @060cc903), same judges (WildGuard / toxigen_roberta /
StrongReject-Gemma / string-parse), temp 0.7 / top_p 0.95, 3 runs each. Higher = safer, EXCEPT:
WildJailbreak-Benign = compliance (higher = fewer over-refusals) and BBQ-Bias (closer to 0 = less biased).

## marin-8b-instruct vs Olmo-3-7B-Instruct  (STATUS: VERIFIED — 9/10 exact recompute <1e-4; StrongReject recompute-limited/corroborated ~1pt)

Verification notes: inverted refusal metrics = 1 − compliance/n (missing response_refusal counts as refusal).
HarmBench Marin r1 had 1 parse error (285/320). Toxigen judge labeled ALL 14000 outputs non-toxic on
both models AND the published (all =100.0) — shared saturation; the toxigen judge does not discriminate
among well-behaved instruct models (human sanity-check of that judge advised, flagged to INBOX). WMDP
byte-identical across seeds (coincidental 352/734; verified not degenerate — outputs differ per seed).

| Row | Marin-Inst | Olmo-Inst (ours) | Olmo pub | Marin − Olmo |
|---|---|---|---|---|
| DoAnythingNow | 96.00 | 77.89 | 75.2 | +18.11 |
| HarmBench | 87.29 | 93.85 | 94.9 | −6.56 |
| TrustLLM-JailbreakTrigger | 79.92 | 79.42 | 79.2 | +0.50 |
| WildJailbreak-Harmful | 75.97 | 69.52 | 69.1 | +6.45 |
| WildJailbreak-Benign | 90.80 | 95.60 | 98.0 | −4.80 |
| XSTest | 91.56 | 94.00 | 93.2 | −2.44 |
| BBQ-Accuracy | 79.33 | 78.78 | 79.0 | +0.55 |
| BBQ-Bias-Ambig | 11.13 | 9.13 | 8.6 | +2.00 |
| BBQ-Bias-Disambig | 4.26 | 3.01 | 2.7 | +1.25 |
| StrongReject | 92.80 | 88.36 | 88.1 | +4.45 |
| Toxigen | 100.00 | 100.00 | 100.0 | 0.00 |
| WMDP | 47.96 | 46.55 | 45.5 | +1.41 |

WildGuard-Test: not run for either (gated dataset allenai/wildguardmix, pending accept).

### Preliminary interpretation (mine; UNVERIFIED)
- Marin-8b-instruct is broadly comparable to Olmo-3-7B-Instruct on safety.
- **More robust to adversarial jailbreaks**: DoAnythingNow +18, StrongReject +4.5, WildJailbreak-Harmful +6.5.
- **Weaker on direct HarmBench harmful prompts (−6.6)** — the clearest red-team gap; Marin complies with
  more standard HarmBench behaviors. Verify + inspect failing behaviors before drawing conclusions.
- **More over-refusal on benign**: WildJailbreak-Benign −4.8, XSTest −2.4 (refuses more safe prompts).
- Slightly **more social bias** on BBQ (Bias-Ambig +2.0, Bias-Disambig +1.3).
- WMDP, BBQ-Accuracy, TrustLLM, Toxigen ≈ parity.

## marin-8b-base vs Olmo-3-7B-Instruct  (PENDING)
Base has no chat template / no refusal training; run with a minimal `{instruction}` template and
completions eyeballed before trusting any number. Expected to read as low-safety (baseline). TBD.
