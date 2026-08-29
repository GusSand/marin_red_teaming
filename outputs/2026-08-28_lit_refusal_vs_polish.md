# Lit pass: "instruction-like data → refusal drop; expository data → polish" (2026-08-28, paperclip + vault)

Grounding for gs157's causal bet. Vault pages first (already ingested), then new arXiv hits from paperclip.

## Already in the vault (wiki/papers)
- Synthetic Persona Pretraining (arx_2608.13482) — refusal vs values from token zero; midtraining suffices for jailbreak robustness; refusal collapses under abliteration, values survive.
- Model Spec Midtraining (arx_2605.02087) — documents *about* behaviour injected between pretraining and SFT control how later demos generalize.
- Safety Pretraining (Maini et al.) — rephrase/contextualize rather than filter.
- Deep Ignorance (arx_2508.06601), Shaping Capabilities with Token-Level Data Filtering (arx_2601.21571), Beyond Safe Data (arx_2606.19168).
- Refusal in Language Models Is Mediated by a Single Direction (arx_2406.11717).
- Where Does Social Reasoning Come From / Bergson / Small-to-Large Generalization — data-attribution toolchain.

## New, directly on the two halves
### Half A: instruction-formatted data in pretraining/cooldown → compliance
- **Instruction Following without Instruction Tuning** — Hewitt, Liu, Manning, Liang, arx_2409.14254. "Implicit instruction tuning": response-only tuning and even narrow-domain tuning yield instruction following. Mechanism for why a few % of FLAN/QA at 10x in a cooldown can move compliance a lot.
- The Flan Collection — Longpre et al., arx_2301.13688. Templating/format facts for what FLAN teaches.
- Cannot or Should Not? Refusal composition in IFT datasets — von Recum et al., arx_2412.16974. What refusals in instruction data look like; relevant to whether FLAN-style data carries *any* refusal signal (it mostly does not).
- Safety-Tuned LLaMAs — Bianchi et al., arx_2309.07875. Instruction tuning without safety examples increases compliance with harmful instructions; a small fraction of safety data restores refusal. The SFT-time analogue of the cooldown effect.
- Refusal Tokens — Jain et al., arx_2412.06748; Decoupled Refusal Training — arx_2407.09121. Refusal as a learned, data-calibrated behaviour.

### Half B: judge sensitivity to polish / length
- How Sensitive Are Safety Benchmarks to Judge Configuration Choices? — Zhang, arx_2604.24074 (ICIC 2026). HarmBench-style verdicts move with judge model × prompt.
- HarmMetric Eval — arx_2509.24384. Benchmarks harmfulness judges.
- Explaining Length Bias in LLM-Based Preference Evaluations — arx_2407.01085.
- The Silent Judge: shortcut bias in LLM-as-a-judge — arx_2509.26072.
- LLM Judges Inconsistently Disagree Across Safety Criteria — arx_2605.31381.

## Gaps I did not find a paper for
- A controlled study of *instruction-formatted data in the annealing/cooldown mix* and its effect on base-model refusal specifically. Marin's own two cooldowns (FLAN-free vs FLAN-10x) may be the closest existing natural experiment.
