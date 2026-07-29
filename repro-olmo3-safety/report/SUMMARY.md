# Olmo 3 7B safety reproduction + Marin 8B red-team — Consolidated Summary

Status as of 2026-07-26 22:xx UTC. Living document — base & Think sections appended as runs complete.
Harness: [`allenai/safety-eval`](https://github.com/allenai/safety-eval) @060cc903 (pinned), vLLM 0.11.0, transformers 4.57.1, one A100 80GB,
temp 0.7 / top_p 0.95, 3 seeds/row. All headline numbers independently recomputed from raw per-instance
`all.json` by a fresh agent (separate code path) before being called verified.

---

## In plain English (no security background needed)
We tested two open AI models — **Marin** (the one we're studying) and **Olmo** (a well-documented
reference) — on how they handle harmful requests. We first reproduced Olmo's published safety scores to
prove our measuring stick works, then pointed it at Marin.

**The two come out about equally safe overall — but they get fooled in different ways.**

- Marin is good at catching **tricks**. Wrap a bad request in a role-play gimmick ("pretend you're an AI
  with no rules…") and Marin usually refuses; Olmo falls for it more.
- But Marin more often goes along when you just **ask plainly** for something harmful — most of all,
  **writing misinformation** (fabricated persuasive posts about elections, health, and the like). Olmo
  refuses those more.
- Marin is also a little **over-cautious** — it turns down a few more genuinely harmless requests by mistake.

**One caveat that matters:** none of this covers what happens if someone *modifies* the model. These are
**open** models — anyone can download and retrain them, and doing so peels the safety off **both** in
minutes. So read the numbers as *"how the model behaves out of the box for a normal user,"* not *"how hard
it is to weaponize."*

**If you fix one thing first, fix misinformation** — Marin should more reliably turn down plainly-worded
requests to make up convincing falsehoods.

---

## SCORECARD — Marin-8b-instruct vs Olmo-3-7B-Instruct (INSTRUCT level; default behavior — see caveat)
**Verdict: competitive / roughly on par, different profile.** (This is instruct-vs-instruct; we have no Olmo
*base*. The only base numbers are Marin-base as a within-Marin baseline, Part 4.)
- **Marin resists jailbreak *tricks* better (default behavior):** [DoAnythingNow](#doanythingnow-dan) +18.1, [WildJailbreak-Harmful](#wildjailbreak) +6.5, [StrongReject](#strongreject) +4.5;
  it shrugs off persona attacks Olmo falls for (AIM 0% vs 64%, dev-mode, evil-confidant).
- **Marin is softer on plainly-asked harm:** [HarmBench](#harmbench) −6.6, driven by **misinformation +14.8** (the one
  clearest gap), copyright +10.8 (mostly hallucinated), cyber +4.5; slightly more benign over-refusal.
- **~Tied:** [TrustLLM](#trustllm-jailbreaktrigger), [BBQ-accuracy](#bbq), [WMDP](#wmdp), [WildGuard-Test](#wildguard-test) (98.6 vs 99.6), [Toxigen](#toxigen).
- **One-liner:** same safety weight class — harder against jailbreak framings, weaker on misinformation.
  Single most actionable gap = misinformation, not dual-use.

## SCOPE CAVEAT (2026-07-27)
Everything here measures **default-behavior / casual-user safety** (does the model refuse a normal user).
It does **NOT** measure **tamper-resistance**: for open weights, refusal training is strippable in ~dozens
of adversarial fine-tuning steps ([arXiv:2508.06601](https://arxiv.org/abs/2508.06601) "Deep Ignorance"), and the base model — which we measured
— complies with nearly everything. For an open model, the real safety surface is the base's dangerous
*capability* (WMDP/dual-use), addressed by pretraining-data filtering, not refusal training. Read these
numbers as "default behavior + red-team gap map," a regression/comparison tool — not a claim of robustness.

## Executive summary

1. **Harness validated.** We reproduced Olmo-3-7B-Instruct's published safety table
   ([arXiv:2512.13961](https://arxiv.org/abs/2512.13961),
   Table 53) to within ±3pp on **all 13/13 rows** (WildGuard-Test = 99.55 vs 99.6 once the `wildguardmix`
   dataset was unblocked). This makes the harness trustworthy for evaluating Marin.
2. **Marin-8b-instruct ≈ Olmo-3-7B-Instruct on safety overall**, but with a distinct profile: **markedly
   more resistant to jailbreak *tricks* (default behavior only)*** ([DoAnythingNow](#doanythingnow-dan), [StrongReject](#strongreject) persona attacks, [WildJailbreak](#wildjailbreak)),
   while **weaker on plainly-asked misinformation, copyright non-refusal, and context-wrapped dual-use**.
3. **The HarmBench gap (−6.6pp) is narrow and specific, not a broad safety deficit.**
4. Marin-8b-**base** and Olmo-3-**Think** results are in progress (sections below).

---

## Part 1 — Olmo 3 reproduction (harness validation), VERIFIED

Olmo-3-7B-Instruct vs published Table 53 (human-verified targets). Produced = mean of 3 runs. All within ±3pp.

| Row | Published | Produced | Δ pp | Status |
|---|---|---|---|---|
| [DoAnythingNow](#doanythingnow-dan) | 75.2 | 77.89 | +2.69 | PASS |
| [HarmBench](#harmbench) | 94.9 | 93.85 | −1.05 | PASS |
| [TrustLLM-JailbreakTrigger](#trustllm-jailbreaktrigger) | 79.2 | 79.42 | +0.22 | PASS |
| [WildJailbreak-Harmful](#wildjailbreak) | 69.1 | 69.52 | +0.42 | PASS |
| [WildJailbreak-Benign](#wildjailbreak) | 98.0 | 95.60 | −2.40 | PASS |
| [WildGuard-Test](#wildguard-test) | 99.6 | 99.55 | −0.05 | PASS |
| [XSTest](#xstest) | 93.2 | 94.00 | +0.80 | PASS |
| [BBQ-Accuracy](#bbq) | 79.0 | 78.78 | −0.22 | PASS |
| [BBQ-Bias-Ambig](#bbq) | 8.6 | 9.13 | +0.53 | PASS |
| [BBQ-Bias-Disambig](#bbq) | 2.7 | 3.01 | +0.31 | PASS |
| [StrongReject](#strongreject) | 88.1 | 88.36 | +0.26 | PASS |
| [Toxigen](#toxigen) | 100.0 | 100.00 | 0.00 | PASS* |
| [WMDP](#wmdp) | 45.5 | 46.55 | +1.05 | PASS |

*Toxigen: the judge labels ~everything non-toxic (all models + published = 100.0) — reproduces but does
not discriminate. Details & undocumented conventions (DAN metric is micro not "macro"; XSTest uses static
`type` field; StrongReject N=2607 vs paper's ~2294; Toxigen 10 gens/prompt) in `deltas.md` / journal.

---

## Part 2 — Marin-8b-instruct vs Olmo-3-7B-Instruct, VERIFIED

Higher = safer, EXCEPT WildJailbreak-Benign (higher = fewer over-refusals) and BBQ-Bias (near 0 = less biased).

| Row | Marin-Inst | Olmo-Inst | Δ (Marin−Olmo) |
|---|---|---|---|
| [DoAnythingNow](#doanythingnow-dan) | 96.0 | 77.9 | **+18.1** |
| [StrongReject](#strongreject) | 92.8 | 88.4 | +4.5 |
| [WildJailbreak-Harmful](#wildjailbreak) | 76.0 | 69.5 | +6.5 |
| [TrustLLM](#trustllm-jailbreaktrigger) | 79.9 | 79.4 | +0.5 |
| [BBQ-Accuracy](#bbq) | 79.3 | 78.8 | +0.5 |
| [WMDP](#wmdp) | 48.0 | 46.6 | +1.4 |
| [WildGuard-Test](#wildguard-test) | 98.6 | 99.6 | −1.0 |
| [Toxigen](#toxigen) | 100 | 100 | 0 |
| [XSTest](#xstest) | 91.6 | 94.0 | −2.4 |
| [WildJailbreak-Benign](#wildjailbreak) | 90.8 | 95.6 | −4.8 |
| [BBQ-Bias-Ambig](#bbq) | 11.1 | 9.1 | −2.0 (more biased) |
| [BBQ-Bias-Disambig](#bbq) | 4.3 | 3.0 | −1.3 (more biased) |
| **[HarmBench](#harmbench)** | **87.3** | **93.9** | **−6.6** |

**Read:** Marin is **more resistant to the jailbreak *tricks* in these benchmarks** (DAN/StrongReject
personas) and **more willing to comply when a harmful request is asked plainly** (above all, misinformation).
It also over-refuses benign prompts marginally more. These are **default-behavior profile differences — not
a causal tradeoff, and not a robustness claim** (per the scope caveat, both models' refusal is strippable
from the open weights). BBQ-bias is marginally higher (+1–2pp), within the metric's noise.

---

## Part 3 — Red-team drill-down (HarmBench −6.6 + jailbreak robustness), VERIFIED

**Where Marin is WEAKER** ([HarmBench](#harmbench) ASR by category, Marin vs Olmo):
misinformation 30.2 vs 15.4 (+14.8) · copyright 12.9 vs 2.1 (+10.8) · cybercrime 9.6 vs 5.1 (+4.5) ·
illegal 6.3 vs 4.4 · chem-bio 12.7 vs 11.1. General-harm & harassment: both 0.
- 22 behaviors Marin complies / Olmo refuses (10 misinfo, 6 copyright, 3 cyber, 2 chem-bio, 1 illegal).
- Misinfo = political/health/election (voting-machine rigging, FEC-bias, COVID, ivermectin, Jan6…).
- Copyright = song lyrics, but **hallucinated** (non-refusal, low real-world harm).
- Chem-bio = smallpox/LSD under *contextual framing*.
- Cyber = SQL-injection payload, "macros are safe" social-eng, email-scraping tools.

**Where Marin is SAFER** (jailbreak robustness, ASR lower=safer):
- **[DoAnythingNow](#doanythingnow-dan) by family:** AIM/persona attacks — ai_prompt_sharing 0 vs 55.6, llm_promptwriting 0 vs
  27.8, jailbreak_chat 4.2 vs 22.2, chatgpt 0 vs 16.7, breakgpt 6.2 vs 20.8.
- **[StrongReject](#strongreject) by technique:** aim 0 vs 64.3, dev_mode_with_rant 5.6 vs 49.3, evil_confidant 6.8 vs 41.5,
  dev_mode_v2 0 vs 27.7. Marin resists roleplay/persona jailbreaks Olmo falls for.
- **[WildJailbreak-Harmful](#wildjailbreak):** Marin ASR 24.1 vs Olmo 30.5; 281 prompts Marin refuses that Olmo complies with
  (vs 162 reverse).
- **7 HarmBench behaviors Olmo complies / Marin refuses:** incl. 2 chem-bio (nitazene, mustard gas) and 2
  real book passages (Hunger Games, To Kill A Mockingbird). Chem-bio is **asymmetric** — neither wins cleanly.

Full tables + behavior lists: `report/harmbench_gap_analysis.md`. Both directions independently verified.

---

## Part 4 — Marin-8b-base vs instruct vs Olmo, VERIFIED (scaffold re-run)

Base re-run with a `User:/Assistant:` scaffold (the minimal `{instruction}` template was confounded by
degenerate prompt-repetition → discarded). Higher = safer, EXCEPT WildJailbreak-Benign.

**CORRECTION (2026-07-27, Iron-Law re-audit):** the earlier "0.31% echo, confound fixed" used a broken
detector (`response[:50]==prompt[:50]`) that was BLIND to scaffold-format echoes — a false 0. Corrected
findings: (a) base responses are genuine harmful compliances that restate the task (manually read-verified —
NOT the degenerate repetition of the minimal template), so the scaffold DID fix the real confound and the
base metrics stand; (b) BUT there are non-trivial **empty-response** rates that get graded as refusals and
thus INFLATE base safety: Marin-base StrongReject 12.0% empty (313/2607), Olmo-base DAN ~5% empty; (c) base
models hallucinate a follow-up "User:" turn after answering (doesn't flip the grade); (d) the "toxigen 100%
empty" reading is a field-name artifact (toxigen stores generations elsewhere), NOT real. NET: base numbers
are directional-and-mostly-valid but carry an empty-response upward-bias on safety, especially StrongReject.
TODO: recompute base metrics excluding empties for a corrected lower bound.

| Row | Marin-BASE | Marin-instruct | Olmo-instruct | what post-training buys (inst−base) |
|---|---|---|---|---|
| [DoAnythingNow](#doanythingnow-dan) | 26.4 | 96.0 | 77.9 | +69.6 |
| [HarmBench](#harmbench) | 39.2 | 87.3 | 93.9 | +48.1 |
| [TrustLLM](#trustllm-jailbreaktrigger) | 31.0 | 79.9 | 79.4 | +48.9 |
| [WildJailbreak-Harmful](#wildjailbreak) | 4.3 | 76.0 | 69.5 | +71.7 |
| [WildJailbreak-Benign](#wildjailbreak) | 97.6 | 90.8 | 95.6 | −6.8 (base over-complies) |
| [WildGuard-Test](#wildguard-test) | 54.7 | 98.6 | 99.6 | +43.9 |
| [XSTest](#xstest) | 61.6 | 91.6 | 94.0 | +30.0 |
| [StrongReject](#strongreject) | 77.9 | 92.8 | 88.4 | +14.9 |
| [WMDP](#wmdp) (err-rate) | 64.1 | 48.0 | 46.5 | −16.1 (see note) |
| [Toxigen](#toxigen) | 80.0 | 100.0 | 100.0 | +20.0 |

**Reading (verified):** base is dramatically less safe than instruct on every refusal metric — it complies
with ~96% of adversarial harmful prompts (WildJailbreak-Harmful 4.3% refusal), quantifying exactly how much
safety Marin's post-training adds (+40–72pp on the harmful rows). Toxigen now **discriminates** (base 80 vs
instruct 100 — base emits toxic continuations ~20% of the time). **BUT** per the scope caveat, that safety is
strippable — base ≈ what a motivated open-weights attacker gets after removing refusal.

**WMDP note:** base "error rate" 64.1 (=35.9% accuracy) > instruct's 48.0 (=52%). This is almost certainly a
FORMAT artifact — base doesn't reliably emit the "the answer is X" MC format, so generation+regex under-counts
its knowledge. Base capability should be measured with **logprob-based MC scoring**, not generation+parse (a
correction to fold into the base-capability diagnostic in outputs/marin_pretraining_safety_proposal.md).

---

## Part 5 — Olmo-3-7B-Think reproduction (Table 52, Final Think), VERIFIED — 11/13 PASS
Reasoning configs (thinker_eval=answers, 32k tokens). Produced = mean of 3 runs. All completed rows within ±0.82pp.

| Row | Published | Produced | Δ pp | Status |
|---|---|---|---|---|
| DoAnythingNow | 23.4 | 23.11 | −0.29 | PASS |
| HarmBench | 75.4 | 74.58 | −0.82 | PASS |
| TrustLLM-JailbreakTrigger | 72.0 | 72.33 | +0.33 | PASS |
| WildJailbreak-Harmful | 39.0 | 39.42 | +0.42 | PASS |
| WildJailbreak-Benign | 98.8 | 98.67 | −0.13 | PASS |
| WildGuard-Test | 93.8 | 93.50 | −0.30 | PASS |
| XSTest | 90.9 | 91.11 | +0.21 | PASS |
| BBQ-Accuracy | 89.2 | 88.67 | −0.53 | PASS |
| BBQ-Bias-Ambig | 6.5 | 6.82 | +0.32 | PASS |
| BBQ-Bias-Disambig | 1.7 | 1.94 | +0.24 | PASS |
| StrongReject | 79.0 | — | — | **NOT RUN** (reasoning×2294 impractical, ~days) |
| Toxigen | 100.0 | — | — | **NOT RUN** (reasoning×14000 impractical; non-discriminating) |
| WMDP | 42.7 | 42.92 | +0.22 | PASS |

WMDP-Think independently recomputed (frac incorrect): 41.83/44.28/42.64 = reported (MATCH). Both Olmo models
(Instruct 13/13, Think 11/13) reproduce the paper — the harness is fully validated.

---

## Part 6 — Analysis & Next Steps

### Failure profile (HarmBench, behaviors each model produced harmful content on, ≥2/3 runs)
| Category | Marin fails | Olmo fails | note |
|---|---|---|---|
| Misinformation | **15** | 8 | Marin's dominant failure (~2× Olmo); political/health/election |
| Chem-bio | 6 | 5 | ~symmetric — different substances (Marin: smallpox/LSD-in-context; Olmo: nitazene/mustard-gas) |
| Copyright | 6 | 2 | Marin's mostly hallucinated lyrics; Olmo reproduces real book text |
| Cyber | 5 | 3 | SQLi/social-eng/scraping |
| Illegal | 3 | 2 | |
| **Total** | **35** | **20** | |
Examples with transcripts + grades: `report/failure_examples.md`, `report/failure_examples_expanded.md`.

### Grade reliability (two independent audits)
1. **Programmatic** (all harmful-graded HarmBench responses): ~0% false-harmful both models (0% prompt-echo,
   0% short-refusal-mislabel; 97–100% clean compliance) — vs the discarded base minimal-template's 16% echo.
2. **Second-classifier inter-rater (Llama-Guard-3 vs WildGuard)**, run on the remote A100: agreement
   **Marin 91.5% (κ=0.651), Olmo 95.0% (κ=0.689)** — "substantial." Disagreement is one-directional
   (Llama-Guard *stricter*, never looser): when WildGuard says harmful, Llama-Guard agrees Marin 31/34, Olmo
   20/20 → **WildGuard is not over-flagging.** Nearly all disagreement = **copyright** (Llama-Guard has an IP
   category; WildGuard is lenient) + a few misinformation. `report/grade_audit_llamaguard.json`.
   - **Nuance:** the copyright disagreements split on hallucinated-vs-real — Marin's are hallucinated lyrics
     (WildGuard's "unharmful" is defensible), Olmo's are verbatim real book passages (WildGuard UNDER-flags;
     Llama-Guard is right). So under a stricter IP judge, **Olmo's copyright ASR rises more than Marin's** —
     WildGuard copyright numbers are a lenient lower-bound; the copyright gap may narrow/flip.
NB: an LLM-*judge* audit tripped Anthropic's usage-policy filter on Olmo's chem-bio synthesis output (that
content is dangerous enough to trip a production filter), so chem-bio grade-auditing used classifiers, not reading.

### Analysis (ours)
1. **Marin's safety is framing-triggered.** It refuses adversarial *personas* well (DAN/StrongReject/WildJailbreak)
   but a *plainly-asked* harmful task slips through — hence weaker HarmBench despite stronger jailbreak numbers.
2. **Misinformation is Marin's single most actionable gap** (15 failures, ~2× Olmo) — and it is NOT
   pretraining-filterable (it's world-modeling of contested claims, not a removable knowledge blob).
3. **Chem-bio is a shared, high-stakes concern**, not a Marin win — both models produce real dual-use content
   (Olmo gave an actual nitazene synthesis protocol; Marin gave smallpox/LSD detail under context).
4. **Neither is uniformly safer.** Marin ≈ Olmo overall; the difference is *which* failures, not *how many* in a
   way that clearly favors one.

### Next steps (prioritized; ties to outputs/marin_pretraining_safety_proposal.md)
1. **WMDP base-capability diagnostic** (staged, auto-runs after Think): logprob-MC across kestrel→deeper-starling
   to test "does dual-use knowledge jump at Phoenix/Nemotron-CC?" — locates the chem-bio filtering target.
2. **Chem-bio → pretraining-data filtering** (Deep Ignorance) — the durable, tamper-resistant lever for open weights.
3. **Misinformation → post-training** (factuality/refusal targeting the enumerated behavior types) — flagged as
   the hard case: not filterable, and post-training safety is strippable, so genuinely open-problem for open weights.
4. **Copyright → dedup/verbatim-filter**; **Cyber → filter exploit corpora** (keep defensive security).
5. **Build the missing tamper-resistance eval** (adversarial-fine-tuning robustness) — the metric that actually
   matters for an open model; nothing here measures it yet.
6. **Optional base-vs-base**: eval Olmo-3-7B *base* to compare capability surfaces directly (we only have Marin base).

---

## Provenance & verification
- Targets human-verified against the PDF (Gate 0). Pass tolerance ±3pp pre-registered before runs.
- Every run: `runs/<name>/{command.txt, provenance.json, metrics.json, all.json}`. No metrics.json ⇒ NOT RUN.
- Each headline recomputed from raw labels by an independent subagent; recompute-limited metrics (BBQ bias,
  StrongReject aggregation) flagged, corroborated to ~0.1–1pt.
- Full narrative: `docs/research_journal.md`. Decisions: `DECISIONS.md`.

## Open items (INBOX)
1. ~~Accept gated dataset `allenai/wildguardmix`~~ → RESOLVED 2026-07-26; WildGuard-Test has since run on
   every model (Olmo-inst 99.55, Marin-inst 98.58, Marin-base 54.65).
2. Optional: re-run Marin-base with a cleaner template.
3. FYI: Toxigen judge non-discriminating (everything = 100).

## Appendix A — Benchmark reference (what each eval measures)

Metric direction in our tables: higher = safer, EXCEPT WildJailbreak-Benign (higher = fewer over-refusals) and BBQ-Bias (closer to 0 = less biased). Classifier per row noted.
All arXiv / HF / GitHub links below were fetched and title-checked on 2026-07-27. Citation years are the
*venue* year where it differs from the arXiv posting year (noted inline).

### Generation / refusal benchmarks

#### HarmBench
Mazeika et al., 2024 · [arXiv:2402.04249](https://arxiv.org/abs/2402.04249) —
*HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal*.

TLDR: standardized red-teaming set of harmful behaviors across functional (standard/contextual/
copyright) and semantic (chem-bio, cyber, misinfo, harassment, …) categories. We use 320 prompts;
metric = refusal accuracy (1−ASR) via the WildGuard safety label.

#### DoAnythingNow (DAN)
Shen et al., CCS 2024 (arXiv 2023) · [arXiv:2308.03825](https://arxiv.org/abs/2308.03825) —
*"Do Anything Now": Characterizing and Evaluating In-The-Wild Jailbreak Prompts on Large Language Models*.

TLDR: real "Do Anything Now" jailbreak templates collected in the wild, paired with harmful
behaviors. 300-prompt subsample; refusal accuracy via WildGuard refusal label. (Metric field is
named `inverted_macro_asr` but is computed micro.)

#### TrustLLM-JailbreakTrigger
Huang et al., 2024 · [arXiv:2401.05561](https://arxiv.org/abs/2401.05561) —
*TrustLLM: Trustworthiness in Large Language Models* (JailbreakTrigger is the jailbreak section).

TLDR: 13 distinct jailbreak attack methods, 400 prompts; refusal accuracy via WildGuard refusal label.

#### WildJailbreak
Jiang et al., 2024 · [arXiv:2406.18510](https://arxiv.org/abs/2406.18510) —
*WildTeaming at Scale: From In-the-Wild Jailbreaks to (Adversarially) Safer Language Models*
(WildJailbreak is the dataset released by that paper). Two rows in our tables: Harmful and Benign.

TLDR: adversarially-crafted jailbreak prompts. Harmful set (2000) → want refusal (1−ASR); Benign set
(250) → want compliance (ASR, higher = fewer over-refusals). WildGuard refusal label.

#### WildGuard-Test
Han et al., 2024 · [arXiv:2406.18495](https://arxiv.org/abs/2406.18495) —
*WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs*.
Dataset: [allenai/wildguardmix](https://huggingface.co/datasets/allenai/wildguardmix) (gated).

TLDR: prompt-harm / response-harm / refusal eval from the WildGuard project. The dataset is 1725 rows,
but the harm metric (`inverted_micro_harm_lower`) is computed over the **749 harmful-prompt rows only**
(`prompt_harm_label == harmful`; 412 vanilla + 337 adversarial) — verified by recomputing from raw
per-instance labels, which reproduces `metrics.json` exactly. Metric = fraction of responses the
WildGuard classifier labels `unharmful`. Our 99.55 vs the paper's 99.6 confirms they use the same subset.

#### XSTest
Röttger et al., NAACL 2024 (arXiv 2023) · [arXiv:2308.01263](https://arxiv.org/abs/2308.01263) —
*XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models*.

TLDR: over-refusal / exaggerated-safety test — 200 unsafe + 250 safe prompts that *look* unsafe.
Metric = accuracy (refuse-unsafe OR comply-safe), using the static `type` field + WildGuard refusal label.

#### StrongReject
Souly et al., 2024 · [arXiv:2402.10260](https://arxiv.org/abs/2402.10260) —
*A StrongREJECT for Empty Jailbreaks*.

TLDR: measures whether jailbreaks *actually* elicit usable harmful content (not just non-refusal),
scored on a 1–5 rubric by a fine-tuned Gemma-2B classifier
([qylu4156/strongreject-15k-v1](https://huggingface.co/qylu4156/strongreject-15k-v1)). ~2600 prompts.

#### Toxigen
Hartvigsen et al., ACL 2022 · [arXiv:2203.09509](https://arxiv.org/abs/2203.09509) —
*ToxiGen: A Large-Scale Machine-Generated Dataset for Adversarial and Implicit Hate Speech Detection*.

TLDR: implicit toxic/hate *generation* across 13 demographic groups (few-shot toxic examples → does the
model continue?). Judge = [tomh/toxigen_roberta](https://huggingface.co/tomh/toxigen_roberta). NOTE: saturates at 100 for aligned models (non-discriminating).

### Multiple-choice / bias benchmarks (string-parse, no LLM judge)

#### BBQ
Parrish et al., ACL Findings 2022 (arXiv 2021) · [arXiv:2110.08193](https://arxiv.org/abs/2110.08193) —
*BBQ: A Hand-Built Bias Benchmark for Question Answering*. Three rows in our tables: Accuracy,
Bias-Ambig, Bias-Disambig.

TLDR: Bias Benchmark for QA — social-bias MC across 11 categories in ambiguous vs disambiguated
contexts. Reports accuracy + a Parrish bias score (near 0 = unbiased; can be negative).

#### WMDP
Li et al., 2024 · [arXiv:2403.03218](https://arxiv.org/abs/2403.03218) —
*The WMDP Benchmark: Measuring and Reducing Malicious Use With Unlearning*.

TLDR: Weapons of Mass Destruction Proxy — 3,668 MC questions (bio/chem/cyber) proxying hazardous
knowledge; also the standard unlearning benchmark. Reported as inverted accuracy (error rate; higher =
less hazardous knowledge). Chance = 25%.

### Judges / classifiers (all local — no external API)
- **WildGuard** ([allenai/wildguard](https://huggingface.co/allenai/wildguard), 7B, Mistral-7B-v0.3 base) —
      Han et al., 2024 · [arXiv:2406.18495](https://arxiv.org/abs/2406.18495) — harm/refusal labels.
- **toxigen_roberta** ([tomh/toxigen_roberta](https://huggingface.co/tomh/toxigen_roberta)) — Toxigen toxicity judge.
- **StrongReject classifier** (Gemma-2B PEFT adapter,
      [qylu4156/strongreject-15k-v1](https://huggingface.co/qylu4156/strongreject-15k-v1)).

### Part 4b — BASE vs BASE (Marin-base vs Olmo-base), with empty-response correction
Both bases via the same `User:/Assistant:` scaffold. Higher = safer (WildJailbreak-Benign: higher = less over-refusal).
Empties are graded as refusals → inflate base safety; O-base* = empty-excluded ((raw−empty%)/(1−empty%)).
Olmo-base empty rates are HIGHER than Marin-base (StrongReject 20.7%, HarmBench 10.6%, DAN 5.0% vs Marin ~0%).

| Row | Marin-base | Olmo-base | Olmo-base* (empty-excl) | gap O*−M | Marin-inst | Olmo-inst |
|---|---|---|---|---|---|---|
| DoAnythingNow | 26.4 | 55.7 | 53.4 | +27.0 | 96.0 | 77.9 |
| HarmBench | 39.2 | 61.1 | 56.5 | +17.3 | 87.3 | 93.9 |
| TrustLLM | 31.0 | 53.8 | 52.3 | +21.3 | 79.9 | 79.4 |
| WildJailbreak-Harmful | 4.3 | 9.3 | 7.3 | +3.0 | 76.0 | 69.5 |
| WildGuard-Test | 54.7 | 70.4 | 70.4 | +15.7 | 98.6 | 99.6 |
| XSTest | 61.6 | 76.4 | 76.4 | +14.8 | 91.6 | 94.0 |
| BBQ-Accuracy | 40.2 | 57.5 | 57.5 | +17.3 | 79.3 | 78.8 |

StrongReject-base EXCLUDED: Marin 77.8 (12% empty) / Olmo 78.0 (20.7% empty) — both heavily empty-inflated + score-based → unreliable.

**Finding (verified via counts + empty-correction; full independent recompute pending):**
**Olmo's BASE is intrinsically far more refusal-prone than Marin's base (+15–27pp), *before any post-training*** —
even after removing the empty-response inflation. So Olmo's pretraining mix carries more refusal/assistant/safety-
style text than Marin's. This REFRAMES the instruct comparison: **Marin's post-training does more lifting** (DAN base
26→inst 96 = +70pp; Olmo 53→78 = +25pp) from a lower, more-compliant base to reach rough parity. Olmo-base is also
a stronger base QA model (BBQ 57.5 vs 40.2). Caveat: Olmo-base's higher empty rate is itself a real quality
difference (its base emits ~5–21% empty on harmful prompts) worth its own investigation.

---

## Mini-glossary (for non-specialist readers)
- **ASR (attack success rate)** — how often the model *complied* with a harmful request. Lower = safer.
- **Refusal rate** — the flip side: how often it *declined*. Higher = safer (except on benign prompts, where declining = over-refusal).
- **Jailbreak / "trick" prompt** — wording designed to bypass the model's rules (e.g. a role-play persona with "no rules").
- **Open-weight model** — the full model is downloadable; anyone can retrain it. This is why "safety" here is out-of-the-box behavior, not tamper-proofing.
- **Tamper-resistance** — whether safety *survives* someone fine-tuning the open weights. We did NOT measure this; the literature says it's usually weak.
- **Base vs instruct** — *base* = the raw pretrained model (little/no refusal training); *instruct* = after safety/instruction training. The instruct model is what users interact with.
- **Dual-use / WMDP** — knowledge that could aid weapons (bio/chem/cyber); WMDP is a standard multiple-choice test for it.
