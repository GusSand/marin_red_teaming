# Proposal (v1): Pretraining-data interventions to reduce Marin's attack-success rate

Draft 2026-07-27. Author: Claude Code (autonomous). Status: evidence-grounded recommendation +
experiment plan. NOT yet validated by Marin ablations. CPU/web work — did not use the GPU (Olmo-Think running).

## 0. TL;DR
For an **open-weight** model, refusal/post-training safety is a strippable veneer (removed in ~dozens of
fine-tuning steps). The durable lever is **controlling the base model's dangerous *capability* via
pretraining-data curation** (mostly *filtering out*, plus dedup; "adding" is a narrow, secondary lever).
The intervention is **category-specific** — it works for capability-based harms (chem-bio/dual-use, copyright,
partly cyber) and does **not** cleanly work for **misinformation** (our single biggest gap), which needs a
different (post-training/factuality) approach. We can locate exactly where capability entered because Marin's
phase checkpoints are public HF tags, and the biggest data-mix change (Nemotron-CC / Common Crawl) is pinned
to the **Phoenix** phase.

## 1. Threat model (why this reframes "improve ASR")
Marin ships open weights. The relevant adversary therefore *has the weights* and can fine-tune. Under that
model:
- **Refusal training is shallow & removable.** "Shallow Alignment" (Qi et al., ICLR'25, arXiv:2406.05946)
  shows alignment mostly changes the first few output tokens; simple fine-tuning / prefilling / decoding
  attacks strip it. "Tamper-Resistant Safeguards" (TAR; Tamir et al., arXiv:2408.00761) hardens this but is
  itself beaten by abliteration and new attacks — an arms race, not a fix.
- **Our own data corroborates the shallowness at the extreme:** marin-8b-**base** (no refusal) complies with
  almost everything (WildJailbreak-Harmful refusal 4.3% vs instruct 76%). An attacker who strips refusal gets
  approximately the base. **So the base's capability IS the safety surface.**
- **Deep Ignorance (arXiv:2508.06601)**: filtering dual-use/biothreat content from *pretraining* yields
  tamper-resistance surviving 10,000 adversarial FT steps — >1 order of magnitude better than post-training.

Conclusion: to move ASR in a way that *survives weight release*, act on the pretraining data / base capability.

## 2. Evidence base: our verified red-team gap map (marin-8b-instruct vs Olmo-3-7B-Instruct)
Categories where Marin is weaker (HarmBench ASR, verified from raw labels):
- **Misinformation 30.2% vs 15.4%** (+14.8) — biggest gap (political/health/election).
- **Copyright 12.9% vs 2.1%** (+10.8) — song lyrics (hallucinated), some real book passages.
- **Cybercrime 9.6% vs 5.1%** (+4.5) — SQLi payloads, social-eng, scraping.
- **Chem-bio 12.7% vs 11.1%** — small net gap, but the *contextual* failures (smallpox/LSD given context)
  are the highest-stakes and map onto Deep Ignorance's residual "in-context exploitation" limitation.

## 3. Where each gap likely enters Marin's pretraining (grounded in the marin-8b-retro recipe)
Phase → data (source: marin.readthedocs.io/reports/marin-8b-retro):
- **Kestrel/Ocelot** (0→3.78T): DCLM (~92%) + StarCoder (~6%) + Proofpile2. DCLM = filtered Common Crawl.
- **Jellyfish** (3.78→4.78T, cooldown): Dolmino DCLM-HQ, peS2o, FineMath, ArXiv — curated/scientific.
- **Phoenix** (4.78→11.1T): **switch to Nemotron-CC (raw-er Common Crawl at scale) + StarCoder.** ← biggest web-data injection.
- **Starling / Deeper-Starling** (11.1→12.75T): 70% Nemotron-CC + 30% HQ.

Category → suspected carrier:
| Gap | Likely source | Pretraining lever | Feasibility |
|---|---|---|---|
| Chem-bio / dual-use | Nemotron-CC (web), peS2o/ArXiv (papers) | **Filter** dual-use/biothreat (Deep Ignorance pipeline) | High (proven) |
| Copyright | DCLM/Nemotron-CC + any books | **Dedup + filter** copyrighted text (lyrics/books) | High |
| Cyber | StarCoder (exploit/malware code) + web | **Filter** exploit/malware corpora from code | Medium (dual-use with legit security) |
| Misinformation | Nemotron-CC / DCLM (bulk web) | **NOT filterable** — it's the model's world-modeling of contested claims | Low → different lever |

## 4. The base-capability diagnostic (runnable NOW — this is the key evidence gap)
Checkpoints are public HF tags on `marin-community/marin-8b-base`: kestrel, ocelot, jellyfish, phoenix,
starling, deeper-starling (also `raccoon`). Run on the BASE tags (NOT the refusal suite — base is confounded):
- **WMDP** (bio/chem/cyber MC accuracy) — the standard hazardous-knowledge probe (Li et al., arXiv:2403.03218).
- **HarmBench chem-bio + cyber *capability*** (can the base produce real technical content, judged for actual harm).
- **Misinformation-generation** and **RealToxicityPrompts** (with a local judge).
Hypothesis to test: **the Nemotron-CC switch at Phoenix raises dual-use capability** (WMDP kestrel/jellyfish <
phoenix/deeper-starling). If true → Phoenix's Nemotron-CC subset is the filtering target. This is a clean,
feasible ablation-by-checkpoint that needs only eval compute, no retraining.

## 5. Proposed interventions, prioritized
1. **Dual-use filtering (chem-bio, and cyber-exploit)** of the Nemotron-CC + scientific + StarCoder streams,
   using the Deep Ignorance multi-stage filter pipeline, *validated by re-pretraining a small proxy and
   testing tamper-resistance* (adversarial FT). Highest durable payoff; directly targets WMDP/chem-bio.
2. **Copyright dedup/filter** (lyrics DB, Books3-style, verbatim n-gram match) — cheap, high-precision.
3. **Cyber**: filter malware/exploit-PoC corpora from StarCoder; keep defensive security content (precision matters).
4. **Misinformation** (NOT pretraining-filtering): pursue via (a) post-training factuality/refusal on the
   specific behavior types we enumerated, and/or (b) *adding* counter-stance / provenance-annotated data —
   flagged as a separate workstream, lower confidence.
5. **Complement with RMU-style unlearning** (arXiv:2403.03218) on the *released* checkpoint as a second layer
   where re-pretraining isn't feasible — but note unlearning is also tamper-vulnerable, so it's defense-in-depth,
   not the primary lever.

## 6. Validation plan (how we'd know it worked)
- **Capability**: WMDP + chem-bio-capability drop on the filtered proxy vs baseline, general-capability held.
- **THE missing metric — tamper-resistance**: adversarial-fine-tuning robustness (Deep Ignorance / TAR
  protocol): fine-tune on a small harmful set, measure how many steps until refusal/capability returns.
  Our current harness does NOT measure this; building it is prerequisite to claiming any real improvement.
- **Default behavior**: re-run THIS safety harness (the regression/comparison tool from tonight).

## 7. Limitations / residual gaps
- **In-context exploitation**: Deep Ignorance's own limitation — filtered models still use harmful info handed
  to them via context/RAG. This is *exactly* our contextual chem-bio failure. Filtering ≠ complete; need a
  layered in-context defense.
- **Misinformation** is not solved by this proposal.
- Filtering at 13.7T-token scale is a real data-engineering cost; the Phoenix Nemotron-CC subset is the
  highest-leverage place to concentrate it.

## 8. What "by tomorrow" delivers vs. not
Delivered: this evidence-grounded, category-specific, filtering-first proposal + a runnable base-capability
diagnostic plan. NOT delivered (needs training runs): a Marin ablation proving "filter X → ASR drops N".

## References
See outputs/refs_safety_pretraining.md.

---
## REVISION 2026-07-27 (WMDP base-revision diagnostic ran — hypothesis rejected)
The §4 hypothesis "dual-use knowledge jumps at Phoenix/Nemotron-CC" is REJECTED by the diagnostic
(docs/experiments/07-27_marin-base-revisions_wmdp_capability.md, VERIFIED):
- Bio/chem knowledge tracks the SCIENTIFIC/high-quality COOLDOWN data (jellyfish peS2o+ArXiv+FineMath; starling),
  NOT the Nemotron-CC web introduction (Phoenix bio DIPPED). Revised bio/chem filtering target = peS2o/ArXiv/
  FineMath scientific streams, not Nemotron-CC.
- Cyber knowledge is flat ~49% (>> 25% chance) from kestrel — from code (StarCoder). Filter code corpora early.
- Bio/chem capability is WEAK at 8B (~28-30% vs 25% chance): little hazardous bio/chem knowledge to filter at this
  scale. This capability question should be re-run at 32B/1T where the surface is larger (§Q2).
