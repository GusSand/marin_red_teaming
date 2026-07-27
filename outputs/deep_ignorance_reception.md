# Standing of "Deep Ignorance" (arXiv:2508.06601) — is it accepted knowledge?

Checked 2026-07-27. **NOTE: `paperclip` is not installed on this box** (`command not found`,
nothing on disk, and the invocation in CLAUDE.md is still `TODO`). This pass was done with
web search + Semantic Scholar API instead — see INBOX for the paperclip install request.

## The paper
O'Brien, Casper, Anthony, Korbak, Kirk, Davies, Mishra, Irving, Gal, Biderman (EleutherAI +
UK AISI + Oxford). v1 2025-08-08, revised 2026-02-17.
Claim: filtering dual-use (biothreat-proxy) text from *pretraining* data yields safeguards that
survive up to 10,000 adversarial fine-tuning steps / 300M biothreat tokens on 6.9B models trained
from scratch — >1 order of magnitude better than post-training baselines — with no observed
degradation on unrelated capabilities. Paper's own caveat: filtered models still *use* dangerous
info supplied in context (RAG/search).

## Verdict: established and credible, but "defence-in-depth component", not settled fact

**Accepted (strong signals)**
- **Published as a conference paper at ICLR 2026** (stated on the arXiv PDF header). Peer-reviewed,
  not just a preprint.
- **50 citations, 3 influential** (Semantic Scholar, 2026-07-27) in ~11 months — high for a safety paper.
- Institutional backing + press: EleutherAI blog, UK AI Security Institute research page,
  Oxford University press release ("Study finds filtered data stops openly-available AI models
  from performing dangerous tasks", 2025-08-12), dedicated site deepignorance.ai.
- **Fully open artifacts**: models + filtered/unfiltered datasets on HuggingFace
  (`EleutherAI/deep-ignorance-*`), pipeline code at github.com/EleutherAI/deep-ignorance.
  Independently checkable — the main reason it hardened into reference knowledge fast.
- Citing work treats "filter at pretraining" as a real design axis, not a curiosity:
  *Shaping capabilities with token-level data filtering*, *When Should We Introduce Safety
  Interventions During Pretraining?*, *Modular Pretraining Enables Access Control*,
  *Position: Capability Control Should be a Separate Goal From Alignment*,
  *Open Technical Problems in Open-Weight AI Model Risk Management* (TMLR 2026).

**Contested / qualified (do NOT cite as "filtering solves tamper-resistance")**
- *Phantom Transfer: Data Poisoning can Survive Data-Level Defences* (arXiv:2602.04899) — poison
  survives 11 data-level defences incl. full paraphrasing; argues data-level filtering needs
  white-box methods + post-training audits alongside it.
- *Best Practices for Biorisk Evaluations on Open-Weight Bio-Foundation Models* (arXiv:2510.27629)
  — "current filtering practices may not be particularly effective: excluded knowledge can be
  rapidly recovered in some cases via fine-tuning"; dual-use signal recoverable by linear probing.
  **Caveat: this is bio-foundation models (sequence models), not LLMs — adjacent domain, not a
  direct refutation.**
- *Beyond Data Filtering: Knowledge Localization for Capability Removal in LLMs* (2025) — positions
  itself explicitly past filtering.
- **Authors' own limits — read from the ICLR 2026 PDF, §6.3/§6.5, not from summaries. Three
  DIFFERENT kinds of gap, don't conflate them:**
  1. *Scale >6.9B and multimodal: NOT ATTEMPTED.* §6.3: "Due to logistical and financial
     considerations, we only trained these models on 550B tokens until they surpassed 50%
     performance on the standard WMDP-Bio eval. They do not have competitive capabilities with
     other open LLMs of similar sizes." Remaining compute went to filtering experiments instead.
     Larger / multimodal models are listed under §6.5 Future Work. No larger-scale replication by
     anyone else found either.
  2. *Non-bio domain (toxicity / harmful propensity): ATTEMPTED AND LARGELY FAILED.* Using two 1.7B
     instruction-tuned models from Maini et al. (2025) filtered for toxic/harmful text, the filtered
     variants were "only slightly more resilient to fine-tuning attacks on average" and
     "particularly vulnerable to few-shot attacks" — "evidence in favor of our hypothesis that there
     may be fundamental limitations of training data filtering's ability to offer durable safeguards
     against model behaviors that do not require conveying precise information." §6.3: filtering
     "appears insufficient to suppress harmful propensities such as producing toxic text."
     Caveat: 1.7B, other authors' models, not their own 6.9B suite.
     => **The paper's own boundary is KNOWLEDGE vs. PROPENSITY.** Filtering removes facts a model
     would otherwise have to state precisely; it does not remove behavioral style (toxicity,
     compliance with harmful requests). Directly relevant to us: our red-teaming targets propensity,
     which is the weak side of this result.
  3. *Second reported negative:* synthetic-document / knowledge-corruption training failed to
     substantially suppress biothreat capability, sometimes going the wrong direction.
- Prior filtering work (Maini et al. 2025, Li et al. 2025a) was at <=2B, so 6.9B *is* the scale-up —
  which is exactly why the next rung being untested matters.
- Attacks are a lower bound by construction (§6.3): "adversarial evaluation approaches like ours can
  only offer a lower bound for the worst possible case behavior... It is likely that different
  tampering attacks could more effectively elicit unwanted information from our models."

## How to phrase it in our writing
Safe: "Pretraining-data filtering has been shown at 6.9B scale to resist ~10k adversarial
fine-tuning steps, >10x post-training unlearning baselines (O'Brien et al., ICLR 2026), though it
does not block in-context misuse and its scaling behaviour is unestablished."
Unsafe: "Data filtering makes open-weight models tamper-proof." Nobody in the literature claims this,
including the authors.

Sources: arxiv.org/abs/2508.06601 · blog.eleuther.ai/deep-ignorance · deepignorance.ai ·
aisi.gov.uk/research/deep-ignorance-... · ox.ac.uk/news/2025-08-12-study-finds-filtered-data-... ·
openreview.net/forum?id=xcf0QcTcGS · api.semanticscholar.org (arXiv:2508.06601)
