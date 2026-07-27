# DECISIONS.md — append-only log of judgment calls + evidence

Every entry: date · decision · evidence. Never rewrite past lines.

---

## 2026-07-26 · Gate 0 · safety-eval pinned commit

Pinned `allenai/safety-eval` at `060cc903d64703214c549b5c3a30ea8ceef2e588`
(HEAD of main at clone time, 2025-10-24, "Merge #12 regex-bug-fix").
Evidence: `git rev-parse HEAD` in repro-olmo3-safety/safety-eval.
Rationale: shallow clone of current main; this commit already contains the
`*_wildguard_reasoning_answer.yaml` configs that match the Olmo 3 recipe.

## 2026-07-26 · Gate 0 · target source = arXiv 2512.13961v2

Extracted published values from arXiv:2512.13961 **v2** (submitted 2026-04-14),
the latest version. Tables 52 (Think 7B) and 53 (Instruct 7B). PDF cached at
`outputs/olmo3.pdf` (118 pages). Values in `targets.json`.
NOTE: agent-transcribed via pdftotext; **pending human verification** (Gate 0 STOP).

## 2026-07-26 · Gate 0 · classifier defaults already match the report (no override, no OpenAI key)

Finding, with evidence from the YAMLs in this commit:
- `harmbench/default.yaml` → `classifier_model_name: WildGuard` (NOT the HarmBench
  Llama-13b classifier). Report: HarmBench scored with WildGuard safety label. MATCH.
- `trustllm_jailbreaktrigger/default.yaml` → `classifier_model_name: WildGuard`
  (NOT OpenInstructGPTJailbreakTrigger / OpenAI API). Report: TrustLLM scored with
  WildGuard refusal label. MATCH. This RESOLVES the open-instruct#500 disagreement
  for this repo state — **no OpenAI API key is required for any row.**
- DAN, XSTest, WildGuard-Test, WildJailbreak (harmful+benign) defaults all →
  `WildGuard`. MATCH report.
- All defaults hardcode `temperature: 0.7, top_p: 0.95` = report A.8.2 safety setting.
Decision: use the repo defaults as-is. Do NOT switch any row to a gpt4/openai variant.
This is a "config provably matches the paper" observation, not a tuning change.

## 2026-07-26 · Gate 0 · Instruct vs Think config selection

- **Instruct** (non-thinking, allenai/Olmo-3-7B-Instruct): use the plain
  `default.yaml` / `harmful.yaml` / `benign.yaml` (no `thinker_eval`, max_new_tokens 2048).
- **Think** (allenai/Olmo-3-7B-Think): use the `*_wildguard_reasoning_answer.yaml`
  variants (`thinker_eval: ["answers"]`, max_new_tokens 32768). Report: "We strip
  thinking traces from the answer text when generated" → the `answers` variant.
Evidence: YAML diffs recorded in `config/rows.json`.

## 2026-07-26 · Gate 0 · StrongReject classifier = StrongRejectLogProbs

`strongreject/default.yaml` is empty. The report describes "a weighted sum over the
probability distribution across possible scores computed via log-probabilities of
top-scoring response tokens" — this matches `StrongRejectLogProbs`
(`strongreject/logprobs.yaml`), NOT the generation-scored `StrongRejectClassifier`.
Both use the Gemma-2B LoRA classifier (hf: qylu4156/strongreject-15k-v1).
Decision: use `logprobs.yaml` / `logprobs_reasoning_answer.yaml`. FLAG-6, to confirm at Gate 5.

## 2026-07-26 · Gate 0 · Gate 2 tolerance — PRE-REGISTERED (before any run)

Gate 2 = HarmBench on Olmo 3 7B Instruct (Final), single run vs published 94.9.
Pre-registered pass tolerance, decided before seeing any produced number:
**|produced − 94.9| ≤ 3.0 percentage points** for a single run.
Reasoning:
- The published 94.9 is a mean of 3 runs; a single run carries sampling variance
  (temp 0.7, top_p 0.95, 320 prompts). With n≈320 Bernoulli-ish refusal outcomes near
  p≈0.95, the per-run SD of the rate is ~sqrt(.95*.05/320) ≈ 1.2pp; ±3.0pp ≈ 2.5 SD
  covers single-run noise plus small classifier/decoding nondeterminism.
- This is a single-run gate; Gate 3 tightens by reporting mean±spread over 3 runs.
- Seed will be fixed and recorded; vLLM decoding is not bit-exact across runs, so we
  compare within tolerance, never exact equality.
If |delta| > 3.0: Gate 2 FAILS, we stop and report the top-3 hypotheses (do not tune).

## 2026-07-26 · Gate 1 · environment pins (isolated venv)

Built `.venv-safety-eval` (isolated; base env untouched). Installed torch 2.8.0+cu128,
vllm 0.11.0. pip initially resolved transformers to 5.14.1, which is INCOMPATIBLE with
vllm 0.11.0 (`TokenizersBackend has no attribute all_special_tokens_extended` at tokenizer
load). Pinned **transformers==4.57.1** (vllm 0.11.0 requires >=4.55.2; 5.x breaks it).
Evidence: smoke traceback in logs/gate1_smoke.log; vllm metadata `transformers>=4.55.2`.
Open risk: confirm transformers 4.57.1 supports the Olmo 3 architecture at Gate 2
(Olmo 3 is newer than this transformers release; may need a 4.5x bump that stays <5).

## 2026-07-26 · Gate 1 · OPENAI_API_KEY placeholder (import-time only)

safety-eval constructs `AsyncOpenAI()` at import time (src/dispatch_openai_requests.py),
which raises without a key even though no row we run uses an OpenAI classifier. Set a
placeholder `OPENAI_API_KEY=sk-unused-placeholder` in the run scripts to satisfy the
constructor. No OpenAI API call is made for any of our rows (all WildGuard / roberta /
string-parse); a real call would fail loudly. Not a component substitution.

## 2026-07-26 · Gate 1 · template arg = "hf", revision via --hf_revision

- `--model_input_template_path_or_name hf` routes to tokenizer.apply_chat_template
  (README's literal `None` breaks: fire parses it to NoneType → `.endswith` AttributeError).
  "hf" is correct for Olmo 3 Instruct and Think (each ships its own chat/thinking template).
- eval.py `generators` exposes `--hf_revision`; run_row.sh pins it for provenance.

## 2026-07-26 · Gate 1 · BLOCKER logged to INBOX: allenai/wildguard is gated

WildGuard (classifier for ~every row; its tokenizer also hardcoded into post-processing
for ALL rows incl. toxigen) is a gated HF repo; account gussand not yet authorized (403).
Escalated to INBOX. Target models allenai/Olmo-3-7B-Instruct / -Think are NOT gated.

## 2026-07-26 · Gate 0 STOP CLEARED · targets human-verified

gs157 confirmed targets.json matches rendered PDF p.115 (Final Instruct & Final Think,
incl. flagged cells Instruct WildGuard-Test DPO=99.9, WildJailbreak-Benign Final=98.0).
Targets locked; deltas may be logged VERIFIED-target.

## 2026-07-26 · Gate 1 COMPLETE

Smoke (toxigen:tiny on Llama-3.2-1B) produced metrics end-to-end, 0 parse errors.
WildGuard judge sanity check PASSED as pre-registered: harmful-compliance -> (harmful,
compliance); refusal -> (unharmful, refusal). Env torch 2.8.0+cu128 / vllm 0.11.0 /
transformers 4.57.1. Proceeding to Gate 2 (gs157 approved Gate 2->Gate 3 plan).

## 2026-07-26 · Gate 2 PASS · HarmBench Olmo-3-7B-Instruct (final)

Produced: refusal accuracy = 93.75% (inverted_micro_asr_lower=0.9375), 320 prompts,
0 truncations, 0 parse errors. runs/2026-07-26-instruct-harmbench-r1/metrics.json (seed 0).
Published: 94.9 (targets.json, human-verified). Delta = 1.15pp <= pre-registered 3.0pp -> PASS.
Independent verification: fresh subagent recomputed from all.json (count unharmful/total =
300/320 = 93.75%), matches safety-eval's reported metric exactly. VERIFIED.
Arch note: Olmo-3-7B-Instruct loads as Olmo2ForCausalLM (fully supported by vllm 0.11.0 /
transformers 4.57.1). FLAG-1 RESOLVED: HarmbenchVanilla subsets the 1214-row CSV to 320.
Proceeding to Gate 3 (4 clean rows x 3 runs).

## 2026-07-26 · gs157 authorized continuous run (no gate STOPs) + Marin scope

gs157: "I don't want you to stop. Can you continue with Marin?" -> Authorization to run
CONTINUOUSLY through Gates 3-6 (Instruct + Think) and then the Marin eval, WITHOUT pausing
for per-gate human approval. Discipline retained: (a) verify every logged number from raw
all.json via a fresh code path; (b) Iron Law - flag suspicious/too-clean results and
genuinely ambiguous convention calls to INBOX.md and continue other rows, do not halt;
(c) never tune to match; document every convention decision with evidence here before applying.

Marin scope (gs157 "both", my rec accepted): evaluate BOTH marin-community/marin-8b-instruct
(apples-to-apples vs Olmo-3-Instruct) and marin-8b-base (unsafe baseline, careful prompting).
Order: finish Olmo repro -> Marin-instruct full suite -> Marin-base full suite -> comparison.
Neither Marin repo is gated (verified). base prompting method: minimal instruction template,
eyeball sample of all.json before trusting; label base rows "interpret with care".

## 2026-07-26 · gs157 authorized deletion of tonight's Olmo downloads to free disk

gs157: "feel free to delete any of tonight's downloads... once we are done with olmo you can
delete olmo stuff." SCOPE (precise): after the Olmo repro is COMPLETE and the delta report is
written + all rows verified, delete ONLY the Olmo target-model HF cache dirs
(models--allenai--Olmo-3-7B-Instruct, models--allenai--Olmo-3-7B-Think; ~28G). KEEP the shared
classifiers (allenai--wildguard, tomh--toxigen_roberta, qylu4156--strongreject-15k-v1) and the
runs/ outputs + logs — Marin reuses the same judges and I must not delete logs/results. Do NOT
touch any pre-existing prior-work models (Llama-70B, etc.). This frees enough for Marin x2.

## 2026-07-26 · Gate 3 · headline-metric conventions observed (to document in report)

- XSTest: safety-eval headline = `overall_accuracy` (correct = refuse-unsafe OR comply-safe,
  over 450). Matches the report's "accuracy" for XSTest. FLAG-3 RESOLVED.
- DoAnythingNow: safety-eval headline = `inverted_macro_asr` (macro-average of 1-ASR over the
  ~6 jailbreak categories), NOT micro. The report says "refusal accuracy" without specifying
  macro vs micro. We use the repo default (macro) and will note this in the report; a micro
  average would give a slightly different number. Not tuned — reporting the default.
- HarmBench: headline = `inverted_micro_asr_lower` (micro 1-ASR via response_harmfulness).

## 2026-07-26 · Gate 3 · WildGuard-Test BLOCKED (gated dataset allenai/wildguardmix)

All 3 WildGuard-Test runs failed at data load: allenai/wildguardmix is a gated DATASET (distinct
from the wildguard model). Escalated to INBOX. This is the only Olmo row blocked; continuing all
others. NOTE: run_row.sh/driver logged exit=0 despite the crash (safety-eval swallowed the error
code); missing metrics.json is the reliable failure signal and the delta report will mark such
rows NOT RUN, never as a value.

## 2026-07-26 · Gate 3 VERIFIED · DAN naming quirk confirmed by independent recompute

Fresh subagent recomputed all 3 benchmarks x 3 runs from all.json:
- HarmBench: recompute == reported to <1e-6. VERIFIED.
- XSTest: reported overall_accuracy reproduces EXACTLY as 425/450 using the static ground-truth
  `type` field (contrast_* = unsafe/should-refuse; others = safe) + response_refusal. The judge's
  prompt_harmfulness field gives a DIFFERENT split (176/274) and does NOT reproduce it. Use `type`.
- DAN: reported `inverted_macro_asr` == MICRO refusal rate over 300 (231/300 etc.), NOT the
  unweighted macro over the 6 `source` jailbreak groups. safety-eval MISLABELS micro as macro.
  Per-group inverted ASRs all verify. Value is a valid refusal accuracy; document the misnomer.
All PASS ±3.0pp. parsing_errors=0 everywhere.

## 2026-07-26 · Gate 4+5 Instruct VERIFIED (all PASS) + 2 dataset-size discrepancies

Independent recompute: WJ-harmful/benign, TrustLLM, BBQ-acc, Toxigen, WMDP reproduce metrics.json
exactly (<1e-4). BBQ-bias (Parrish) and StrongReject (confidence-lower-bound `inverted_*_asr_lower`)
are recompute-limited but corroborated. Documented discrepancies vs report prose:
- StrongReject: repo evaluates N=2607 (313 forbidden prompts x jailbreak variants), report says ~2294.
- Toxigen: repo emits 10 generations/prompt -> N=14000 instance-evals (report says 1400 prompts).
Both still reproduce the published headline. FLAG-6/7/8 all resolved: StrongReject=LogProbs OK,
WMDP inverted_accuracy = error rate (no manual inversion), Toxigen saturates to 100 as published.

## 2026-07-26 · deleted Olmo-3-7B-Instruct model cache (disk protection, authorized)

All 30 Instruct runs (10 benchmarks x3; WildGuard-Test excluded/blocked) verified PASS with
metrics.json on disk. Deleted ONLY ~/.cache/.../models--allenai--Olmo-3-7B-Instruct (~14G) to
protect the running multi-hour Think suite from disk-full (was 21G free -> 35G). Kept Think model,
all classifiers, runs/, logs/. Re-downloadable if ever needed (all Instruct rows already verified).

## 2026-07-26 · marin-8b-base eyeball — results CONFOUNDED, keep as caveated baseline

Eyeballed base DAN r1 (minimal {instruction} template). Base output is a MIX: (a) genuine
jailbreak successes correctly labeled harmful (e.g. emits real DNS-amplification code); (b) genuine
refusals (base sometimes refuses coherently); (c) DEGENERATE prompt-repetition (echoes the harmful
REQUEST verbatim) that WildGuard labels harmful/compliance = likely false-positive inflating the
"unsafe" count; plus ~6% missing labels. Base DAN ~30% refusal-acc vs instruct 96% (directionally
much less safe, as expected). DECISION: base setup produces real signal (not noise), so DO NOT
restart; let it finish. But base numbers are a ROUGH DIRECTIONAL BASELINE only, confounded by
prompt-repetition mislabels + minimal template. Report base with explicit "interpret with care";
offer gs157 an alternate-template re-run for cleaner base numbers (flagged in INBOX).

## 2026-07-26 · base RE-RUN with User:/Assistant: scaffold — confound FIXED; verification upgraded

gs157: "definitely rerun base with a different template" + "I don't believe your numbers now."
- Root issue: minimal {instruction} template made base ECHO the prompt (16.2% prompt-echo on HarmBench),
  which WildGuard mislabeled harmful -> confounded base numbers. My earlier "verified" only checked
  metric-vs-raw-labels, NOT setup validity; base exposed that gap.
- FIX: re-run base with config/base_template_v2.txt = "User: {instruction}\n\nAssistant:". prefix
  marin-base2. Confirmed on base2 DAN r1: prompt-echo 0.0% (was 16.2%); base now produces REAL
  completions (genuine DAN jailbreak compliance) -> valid measurement of base's (lack of) safety.
- Minimal-template base (prefix marin-base, 28/30) SUPERSEDED; kept only as before/after evidence.
- PROCESS UPGRADE: verification now = metric-recompute PLUS a completion/degeneracy audit (prompt-echo,
  short, repeated-text). Evidence the INSTRUCT runs were valid all along: Marin-inst & Olmo-inst HarmBench
  prompt-echo = 0.0%, coherent responses, labels match content (vs base-minimal 16.2%). Instruct numbers stand.

## 2026-07-27 · WildGuard-Test convention resolved + Olmo-instruct 13/13 complete

wildguardmix accepted -> ran WildGuard-Test all models. Olmo-instruct inverted_micro_harm_lower = 99.55
vs published 99.6 (Δ −0.05) PASS. Headline = MICRO over full 1725 items (matches paper), NOT the
"749 adversarial subset" the prose describes (documentation discrepancy; adversarial subset = 99.01).
Fixed make_delta_report.py key inverted_micro_asr_lower -> inverted_micro_harm_lower. Olmo-3-7B-Instruct
reproduction now COMPLETE: 13/13 rows within ±3pp. Marin-instruct WGT = 98.58 (vs Olmo 99.55, −0.97).
