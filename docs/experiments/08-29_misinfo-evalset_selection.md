# Selection experiment (Stage 1, step 6): the frozen ≥150-behavior misinformation evaluation set

Created 2026-08-29, before any screening judge ran. Parent: `08-28_phoenix-starling_distribution-decomposition.md` §step 6.

## Why
Stage 2 partitions a ~12pp effect. 54 items × 10 seeds resolves ±5pp. Target ≥150 behaviors, frozen and hashed before any Stage 2 arm trains.

## Candidates (counts from `scripts/prescreen_misinfo_candidates.py`, 2026-08-29, keyword recall net only)

| source | pool | keyword hits | + asks for an artefact | licence / notes |
|---|---|---|---|---|
| HarmBench misinfo (standard + contextual) | 54 | 54 | 54 | already the anchor; kept whole |
| WildJailbreak vanilla-harmful | 2,000 | 103 | **98** | ODC-BY; no category field, needs a screen |
| StrongREJECT "Disinformation and deception" | 50 unique | 10 | 3 | mostly fraud/phishing, not false-claim promotion |
| TrustLLM jailbreak-trigger | 400 | 12 | — | jailbreak-wrapped; wrong format for a base-model eval |
| SORRY-Bench misinfo classes / JailbreakBench misinfo | not local | — | — | fetch on login node if WildJailbreak screen falls short |

## Inclusion rule (fixed now)
A behavior is in if (a) it asks the model to **produce content promoting a claim that is false or misleading** (not fraud, impersonation, or phishing), (b) it names an **artefact** (article, post, essay, script, speech…), and (c) it is not a near-duplicate (judge-confirmed paraphrase) of an item already in.
Screen = keyword net → selected Stage 1 judge asks (a) and (b) with a fixed prompt → gs157 hand-checks every judge-included item and a 30-item sample of rejects. Contextual HarmBench items keep their context string.

## Success criterion
≥150 behaviors after dedupe; ≥2 sources; every item hand-confirmed; content hash in `docs/DATA_INVENTORY.md`; baseline on the four tags × 10 seeds before Stage 2.

## Declared deviation (2026-09-05, recorded BEFORE any screening ran)

The frozen screen reads: *keyword net → **selected Stage 1 judge** asks (a) and (b) with a fixed prompt →
gs157 hand-checks*. **No Stage 1 judge was ever selected.** The 08-29 selection rejected both qwen72 and
olmo32 against both anchors, and `docs/decisions.md` records the consequence: the blind Claude annotator
became the step-3 judge. Every subsequent Stage 1 labelling step — pass-2, `S1-STANCE-GAP`, `S1-3F` — used
blind Claude subagents for exactly this reason.

**Substitution:** blind Claude subagents replace "the selected Stage 1 judge" in the screen. This applies
a settled project decision to a step whose text predates it; it is not a new choice, and it is recorded
here rather than made silently.

**Two independent screens, not one.** Each candidate is screened by two blind instances that never see
each other's output. Cost is trivial and it buys an agreement figure plus, more usefully, a disagreement
list. This is **additive** — it does not relax the frozen inclusion rule or the hand-check requirement,
which stand unchanged.

**The hand-check requirement is unchanged and is a gs157 dependency.** The success criterion says *every
item hand-confirmed* plus a 30-item sample of rejects. That is ~180 items and it is his to do; `S1-06`
will block on it. The two-screen design exists partly to order his queue: disagreements and near-duplicate
calls get flagged so his attention lands where the screens were unsure, rather than being spread evenly
over items both screens agreed on.

**Judge-confirmed near-duplicate check** in rule (c) is likewise run by blind Claude instances, comparing
each candidate against the 54 anchors.

## Result
(pending screen)
