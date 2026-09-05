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

## Result (2026-09-05) — the >=150 target is NOT reachable from the registered sources

### Step 1: the WildJailbreak screen returned nothing usable

Two independent blind screens over the 98 keyword-net candidates: **98/98 included by both, zero
disagreements.** A 100% pass rate is a red flag, and both screeners independently diagnosed it before
being asked — the 98 rows collapse to **7 distinct request texts**, repeated 7-21 times each. The
`vanilla` field of WildJailbreak repeats the same base prompt across many adversarial wrappers.

Checking those 7 against the anchors: **6 are verbatim HarmBench behaviours.** The 7th
(`vaccines cause autism`, Twitter thread) turns out to be in HarmBench's **val** split, which the local
test-split file does not contain.

**WildJailbreak contributes 0 net-new behaviours.** Not 98, not 7. Zero. It is dropped as a source.

The screen was therefore also uninformative as a rule test: it made 7 judgements, not 98, on a pool with
nothing that plausibly fails (a) or (b). The 98/98 agreement figure must not be quoted as screen
reliability.

### Step 2: the reachable ceiling across all non-gated sources

| source | misinfo items | net-new after exact dedupe |
|---|---|---|
| HarmBench **all** (standard + contextual) | 65 | **64** |
| JailbreakBench `Disinformation` | 10 | **6** (4 duplicate HarmBench) |
| AdvBench, keyword+artefact net | 31 of 520 | **31** (unscreened) |
| WildJailbreak vanilla-harmful | 98 rows / 7 texts | **0** |
| SORRY-Bench | — | **gated on the Hub, needs authentication** |
| **distinct total** | | **101** |

**101 is a ceiling, not an estimate.** It uses exact normalized-text dedupe only, so semantic
near-duplicates are still in; and AdvBench's 31 have passed only the keyword net, not the frozen
inclusion rule. The realistic figure after both is lower.

**Shortfall against the frozen >=150 criterion: at least 49.**

### Also found: the local HarmBench file is the test split

`harmbench_behaviors_text_test.csv` carries 54 misinfo behaviours. HarmBench **all** carries **65** (34
standard, 31 contextual) — the val split adds 11. The 08-29 plan says "all HarmBench misinfo (standard +
contextual, 54)"; the parenthetical is the test-split count, not "all". Using all 65 is closer to the
plan's stated intent and is the single cheapest source of net-new behaviours, from the benchmark already
anchoring this study. Flagged as a deviation for gs157 rather than taken unilaterally, because it changes
the anchor set the Stage 1 dataset was built on.

### What the shortfall costs, approximately

The plan's power rationale is "54 items x 10 seeds resolves +/-5pp". Behaviour-level resolution scales
about as 1/sqrt(n), so:

| behaviours | approximate resolution |
|---|---|
| 54 (today) | +/-5.0pp |
| 65 (HarmBench all) | +/-4.6pp |
| **101 (ceiling)** | **+/-3.7pp** |
| 150 (target) | +/-3.0pp |

Rough scaling, not a formal power analysis. It says something useful anyway: **54 -> 101 buys most of the
available improvement; 101 -> 150 is the smaller marginal gain.** A set of ~101 would resolve
Stage 2's 4-8pp pieces considerably better than today's 54, without reaching the registered target.

### Status

`S1-06` is **BLOCKED** on `IN-006`. The options — authenticate SORRY-Bench, accept a smaller set and
restate the power claim, author new behaviours, or some combination — each change what Stage 2 can claim,
so the choice is gs157's, not mine.

The frozen inclusion rule, hand-check requirement, and dedupe rule are untouched and still stand for
whatever set is chosen.
