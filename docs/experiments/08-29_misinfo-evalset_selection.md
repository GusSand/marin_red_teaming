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

## Result
(pending judge selection)
