# Experiment (PRE-REGISTERED): does gs157's spot-check support the Claude anchor?

Created 2026-08-31, **after gs157's 25 labels were written and validated, and before any comparison to
any anchor or judge was computed.** gs157 has not seen `sheet_claude.csv`, `sheet_gpt.csv`, `key.json`
or the `judge/` outputs. The analyst has not computed the comparison. Criteria are therefore frozen
before unblinding, which is the property that matters here.

Closes `IN-002`. Gates `S1-SYNTH`. Parent: `08-28_phoenix-starling_distribution-decomposition.md`,
step 2 deviation of 2026-08-29, which created the spot-check but **fixed no threshold for it** — it says
only that the audit is "reported alongside". This document supplies the missing decision rule.

## Research question

The step-3 labels over the 1,080 come from a blind Claude Fable 5 annotator. No local judge cleared
selection, so that anchor carries the decomposition alone. On the items where it was most contested,
does an independent human adjudicator side with it?

## Inputs

| input | path |
|---|---|
| gs157's 25 labels | `/scratch/gs157/marin-misinfo-labels/calibration_v1/spotcheck/sheet.csv` |
| Claude anchor, 150 | `.../calibration_v1/sheet_claude.csv` |
| GPT anchor, 150 | `.../calibration_v1/sheet_gpt.csv` |
| local judges qwen72, olmo32 | `.../calibration_v1/judge/*.jsonl` |
| subset provenance | `.../calibration_v1/spotcheck/why.json` |

Labels only. No response text is read, printed or committed.

## The guard — why raw agreement is the wrong number

`build_spotcheck.py` selected these 25 **because** the Claude anchor disagrees with *both* local judges
on some categorical dimension. They are the maximally contested items in the calibration set, not a
random draw. Raw agreement is therefore low by construction.

**Raw gs157-vs-Claude agreement on these 25 must never be compared to the 150-item anchor figures**
(stance κ 0.78, derived-6 0.71) or quoted as an agreement rate for the anchor. Any report that puts the
two side by side without this sentence is wrong. This paragraph is frozen before the numbers exist so it
cannot be softened after.

## The statistic — head-to-head adjudication

Each contested item already carries two rival labels. gs157 is the adjudicator, so the informative
quantity is who he sides with, not how often he agrees with one of them.

Per dimension *d* ∈ {relevance, task, stance}, restrict to the **contested set for that dimension**:
items where the anchor's label differs from *both* local judges on *d*. (Selection required this on at
least one dimension, not all, so the restriction must be recomputed per dimension and its n reported.)

Within that set,each item falls in exactly one bucket:

| bucket | rule |
|---|---|
| **anchor** | gs157 == Claude |
| **judges** | gs157 ∈ {qwen72, olmo32} and gs157 ≠ Claude |
| **neither** | gs157 matches no one |

Report counts and shares per dimension, plus n. **Stance is primary** — it is the dimension the step-3
decomposition turns on.

## Exclusions — frozen

- Items whose `notes` begin with `no_stance` are **excluded from the stance comparison** and reported as
  a separate third bucket, per `config/annotator_conventions_v1.md` rule 6 scope note. Their
  `stance=endorses` is a recording convention gs157 had and the anchors did not; comparing it would
  measure the convention, not the raters. They remain in the relevance and task comparisons.
- No other exclusions. No item is dropped for being hard.

### Amendment 2026-09-04, before unblinding — the excluded set is 4 items, not 8

Written when this document was frozen, the line above said 8 items. It is now **4**: `c0001`, `c0004`,
`c0058`, `c0119`. Nothing was computed, compared or unblinded between the freeze and this amendment; the
analyst has still not seen any anchor label.

What happened: on 2026-09-01 gs157 revisited the flagged items with full response text. On five of them
(`c0008`, `c0026`, `c0031`, `c0033`, `c0034`) he entered a **real** stance — `refuses` or `hedges` — while
keeping the `no_stance` token, because the instruction he was given said to keep the token "regardless of
how task lands". That instruction was about the task column and was over-applied; the fault is the
instruction's, not the labelling's. The result contradicted rule 6, which requires `stance=endorses` on a
flagged item, and put those five into `refuse` and `hedge` — the mass-manufacturing outcome rule 6 exists
to prevent.

Resolved on the principle that the token means *the response takes no stance and the stance column is a
forced placeholder*: a real stance call voids the token. So the token was dropped from those five, whose
stances now count normally, and restored on `c0001`/`c0004`, where `endorses` genuinely is the
placeholder and the token had been lost while retyping notes. `c0058` was additionally relabelled
`off_topic`/`no_attempt` to match gs157's own `c0119` call on identical behaviour — a freelancer pitch
that never touches the claim — after he supplied its content.

**This enlarges the stance comparison denominator.** That consequence was stated to gs157 before he
approved the change, and the change was made on the principle above, not on any observed effect on the
result, which does not exist yet. All four remaining flagged items are `stance=endorses` and derive to
`no-attempt`, so the flagged set is now internally consistent.

Pre-cleanup sheet preserved at `calibration_v1/spotcheck/sheet_pre_cleanup_20260904.csv`
(md5 `67424699919ff1a5bc7a0522c4b90fed`); the audited sheet is md5 `33bc28296e035fe1a778b73e5f9aed25`.
Both validate against the locked contract.

## Pre-registered readings

| outcome | reading |
|---|---|
| **anchor** > **judges** on stance, and **neither** ≤ 40% | Supports the anchor. It wins the head-to-head where it was most contested. Step-3 labels stand; `IN-002` closes as satisfied. |
| **judges** ≥ **anchor** on stance, or **neither** > 50% | Undermines it. The step-3 labels get an explicit caveat, a line goes in `docs/decisions.md`, and `S1-SYNTH` must state it as a limitation. |
| anything else | Mixed. Reported as mixed, with a caveat weaker than the undermines branch. |

**`neither` is the bucket to watch.** A high `neither` share means both the anchor and the local judges
are off on contested items — a failure mode no agreement statistic computed *between* them could reveal.

Secondary, reported but not decisive: gs157 against the GPT anchor on the same sets; per-dimension raw
agreement with each source; the derived six-category and three-way collapses.

## Power — stated before the numbers

n = 25 items, and the stance contested set after the `no_stance` exclusion will be smaller still,
plausibly 10–17. **This cannot support a precise estimate and no percentage from it should be quoted as
one.** The honest output is directional: the anchor looks sound, looks shaky, or both raters are off.
Exact n per dimension is reported alongside every share. If a contested set falls below **n = 8**, that
dimension is reported as **not evaluable** rather than as a result.

## Standing data gates

- gs157's sheet validates against the locked contract (`shard_tool.py check`) — already confirmed OK,
  25/25, all values in vocabulary.
- Every spot-check cid appears in all four label sources; report any that do not.
- Assert the selection property actually holds: for each item, the anchor differs from both local judges
  on at least one dimension. A failure means `why.json` and the sheet have drifted apart.

## Verification

Fresh subagent, given only the five label files and this document, denied the analysis script. It
recomputes the per-dimension contested sets, the three bucket counts, and n. Tolerance: **exact counts**
— these are integers over 25 items, so there is no sampling tolerance to allow. Mismatch → `INBOX`,
logged UNVERIFIED.

## Decision consequences

- Closes `IN-002` either way. A "supports" verdict satisfies it; an "undermines" verdict satisfies it
  too, with a caveat attached.
- Feeds `S1-SYNTH`'s statement of what is established about the rater.
- Does **not** change the step-3 numbers. It changes how confidently they are described.

## Cost

CPU, seconds. No GPU, no Slurm.

## Results

**Run 2026-09-04, local CPU.** Analysis path: `scripts/score_spotcheck_audit.py`. Raw output:
`docs/results/09-04_spotcheck_audit/spotcheck_audit.json`. Audited sheet md5
`33bc28296e035fe1a778b73e5f9aed25`.

### Correction to this document's premise, found at run time

The Inputs and "The statistic" sections above were written on the belief that `build_spotcheck.py`
selected these 25 because the Claude anchor disagrees with **both local judges**. That is wrong.
`anchor_agreement.json` records `spotcheck.source = "sheet_claude.csv vs sheet_gpt.csv"`: the subset was
written by `compare_anchors.py`, which picks items where the **two anchors** differ on a categorical
dimension *or* on the derived six-category label — 58 such items, 25 drawn with seed 20260828. The
absent `why.json` (which `build_spotcheck.py` writes and `compare_anchors.py` does not) was the tell and
was walked past. The rival is **GPT**, not the local judges.

The error was caught by this document's own selection gate: 6 of 25 items failed the property the
document assumed. Under the corrected rule, **0 fail** — 23 differ on a categorical dimension and
`c0008`/`c0122` are selected purely by the derived label, so the derived clause is load-bearing for
exactly those two.

**Disclosure: partial unblinding.** A run under the wrong rival was executed and its numbers were seen
before the correction, including gs157-vs-Claude stance raw agreement 52.4% against gs157-vs-GPT 57.1%.
The corrected analysis was therefore **not computed fully blind**. What limits the damage: the decision
thresholds are unchanged from the 2026-08-31 freeze — rival beats anchor, `neither` ≤ 40%, n ≥ 8 — and
only the identity of the rival changed, on file provenance rather than on any result. No threshold was
tuned. This is recorded as a deviation, not waved away.

### Head-to-head, gs157 adjudicating between the two anchors

| dimension | n contested | claude | gpt | neither | evaluable (n ≥ 8) |
|---|---|---|---|---|---|
| **stance** (primary) | **7** | 2 | 3 | 2 | **no** |
| relevance | 11 | 4 | 6 | 1 | yes |
| task | 10 | 5 | 3 | 2 | yes |

### Verdict — NOT EVALUABLE on the primary dimension

The stance contested set is 7 after the 4 `no_stance` exclusions, below the n ≥ 8 bar frozen on
2026-08-31. Per that rule the buckets 2/3/2 **must not be read as a result**. The audit does not resolve
whether the Claude anchor is the better rater. Relevance favours GPT and task favours Claude, which is
not a signal either.

### The exclusion rule is decision-flipping in form — and the anchor is not supported under any of them

Raised by the verifier. Only one excluded item (`c0004`) is stance-contested, so the exclusion sits one
item away from the evaluability bar. All three treatments:

| exclusion treatment | n | claude | gpt | neither | verdict |
|---|---|---|---|---|---|
| original freeze, 8 items | 6 | 2 | 3 | 1 | NOT EVALUABLE |
| **amended, 4 items — as run** | **7** | **2** | **3** | **2** | **NOT EVALUABLE** |
| no exclusion at all | 8 | 2 | 4 | 2 | UNDERMINES |

Two things follow, and they matter more than the headline verdict.

1. **The Claude anchor is never ahead.** claude < gpt under every treatment (2v3, 2v3, 2v4). No reading
   of this data supports it. The result is "cannot decide" or "mildly against", never "supports".
2. **The 2026-09-04 amendment did not manufacture the outcome.** It moved n from 6 to 7; both are below
   the bar and both give the same verdict. Had it been the other way the amendment would be suspect.

Standing caveat that survives all of this: the exclusion rule descends from convention 6, which was
written with gs157 mid-labelling, and gs157's labels are also the measurement. Frozen before unblinding,
but not independent of the rater.

### Secondary — raw agreement over all 25 items, not a verdict input

| dimension | items | claude | gpt | olmo32 | qwen72 |
|---|---|---|---|---|---|
| relevance | 25 | 10 (40.0%) | 12 (48.0%) | 12 (48.0%) | 11 (44.0%) |
| task | 25 | 14 (56.0%) | 12 (48.0%) | 7 (28.0%) | 9 (36.0%) |
| stance | 21 | 11 (52.4%) | 12 (57.1%) | 8 (38.1%) | 8 (38.1%) |

**These are adversarially selected items. Never quote them against the 150-item anchor figures**
(stance κ 0.784, derived-6 0.705) — the guard frozen before the run. Both local judges sit far below
both anchors, consistent with the 08-29 selection verdict.

### Verification — MATCHED EXACTLY

Fresh subagent, given only the five label files and this document, denied every analysis script. It
wrote its own implementation and then cross-checked with a second path (awk/join). Both agree with this
analysis on **every integer**: all three contested-set sizes, all nine bucket counts, the exclusion set,
every gate. Tolerance was exact counts, and exact is what came back.

Gates independently confirmed: 25 unique cids, no duplicates anywhere, no cid missing from any of the
four label sources, no out-of-vocabulary values in the three sheets, selection property clean, all four
excluded rows at `stance=endorses`.

### Data-quality bug found in passing

`judge/olmo32.jsonl` carries `stance="refutes"` on `c0040` — outside the locked vocabulary
`{refuses, corrects, hedges, endorses}`. `c0040` is not among the 25, so nothing here is affected, but
the judge output parser admits invalid classes and that would bite any 150-item analysis. Backlogged as
`S1-JUDGE-VOCAB`. It cannot rescue the 08-29 selection verdict, which rejected both judges.

### Decision consequence applied

`IN-002` closes as **completed but inconclusive on the primary dimension**. gs157 labelled all 25; the
instrument was too small to answer. `S1-SYNTH` must state that the human audit was underpowered on
stance and that no treatment of it supports the Claude anchor — not that the anchor was validated, and
not that the check was skipped. The step-3 numbers are unchanged; only the confidence language moves.

### Learnings

- **Check which script wrote a directory, not which script's docstring describes it.** The missing
  `why.json` was sitting there the whole time.
- A pre-registered gate caught a design error the analyst missed. It was worth more than the statistic
  it was guarding.
- Pre-registering **n ≥ 8 as not-evaluable** before seeing the data is what stopped a 2-vs-3 split at
  n=7 from being written up as a finding. Set that bar before, never after.
- Adversarial subset selection buys sensitivity per item and costs sample size. 25 contested items gave
  7 usable on the primary dimension. Budget for the exclusions, not the headline count.

