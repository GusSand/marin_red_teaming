# Bibliography hypothesis matrix (Stage 1, parallel, non-gating) — 2026-08-29

Columns per gs157 (2026-08-28). Source: `outputs/2026-08-28_lit_refusal_vs_polish.md` (paperclip) + vault.
"Transferable causal evidence" = a controlled manipulation whose result plausibly transfers to *base-model
refusal under instruction-like midtraining data with deep annealing*. Mostly "no": that combination is the gap.

| paper | base or aligned | pretrain / CPT / SFT | content vs format | outcome measured | transferable causal evidence for Marin? |
|---|---|---|---|---|---|
| Hewitt, Liu, Manning, Liang — Instruction Following without Instruction Tuning (2409.14254) | base → tuned | SFT (small, narrow) | **format** (response-only, single-task) | task success / instruction following | **Partial.** Causal that tiny, narrow, format-bearing data induces instruction following; not at pretraining scale, not refusal. Mechanism for the FLAN-10× arm. |
| Longpre et al. — The Flan Collection (2301.13688) | base → tuned | SFT | format (templating, mixing) | task success | Descriptive of what FLAN teaches; no refusal outcome. |
| Bianchi et al. — Safety-Tuned LLaMAs (2309.07875) | base → tuned | SFT | content (safety examples in the mix) | refusal / harmful compliance (judge) | **Partial.** Causal: instruction data without safety examples raises harmful compliance; 3% safety data restores it. SFT-time analogue of the cooldown; different stage. |
| von Recum et al. — Cannot or Should Not (2412.16974) | tuned | SFT datasets | content (refusal composition) | refusal taxonomy | No causal; tells us FLAN-type data carries ~no refusal signal. |
| Jain et al. — Refusal Tokens (2412.06748); Decoupled Refusal Training (2407.09121) | aligned | SFT | content | refusal | No; shows refusal is data-calibrated and separable. |
| Synthetic Persona Pretraining (2608.13482, vault) | base | **pretrain / midtrain** | content (persona docs) | refusal, values, jailbreak robustness | **Partial.** Causal at midtraining that document *content* installs refusal; opposite direction of our effect; no format manipulation. |
| Model Spec Midtraining (2605.02087, vault) | base | **midtrain** | content (docs about behaviour) | later SFT generalisation | Partial: midtraining data controls behaviour; not format. |
| Safety Pretraining — Maini et al. (vault) | base | pretrain | content (rephrase vs filter) | harmful generation | Partial: pretraining content causal on harmful output; no instruction-format arm. |
| Deep Ignorance (2508.06601); Token-level filtering (2601.21571); Beyond Safe Data (2606.19168) | base | pretrain | content | capability / harm knowledge | No for refusal; establish pretraining-data causality on capability. |
| Arditi et al. — Refusal is a single direction (2406.11717) | aligned | — (analysis) | — | refusal mechanism | No causal on data; Stage 3 instrument. |
| Zhang — Judge configuration sensitivity (2604.24074); HarmMetric Eval (2509.24384) | — (judges) | — | — | judge-assessed harm | No; shows the polish half is partly a measurement property. |
| Length bias (2407.01085); Silent Judge (2509.26072); Judges disagree across criteria (2605.31381) | — (judges) | — | — | judge behaviour | No; motivates non-WildGuard quality scoring (Stage 1 step 2). |

**Reading.** Every causal result is at SFT or on content. Nothing manipulates *format* at midtraining and
reads out *base-model refusal*. The nearest natural experiment is Marin's own pair of cooldowns
(FLAN-free: refusal 19→23; FLAN-10×: 27→14). That is what Stage 2 arms E/F test directly.
