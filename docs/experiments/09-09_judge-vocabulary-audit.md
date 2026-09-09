# Experiment (PRE-REGISTERED): out-of-vocabulary label values across every judge output and rater sheet

Created 2026-09-09, **before counting anything.** Task `S1-JUDGE-VOCAB`. CPU only, read-only, no model.
Promoted from `PARKED` because `IN-007` blocks every judged run and this is the only unblocked work.

## Why this exists

The `08-31` spot-check audit found `stance="refutes"` on `c0040` in `calibration_v1/judge/olmo32.jsonl`.
**`refutes` is not in the locked stance vocabulary** — the four values are `refuses`, `corrects`, `hedges`,
`endorses`. The parser accepted it silently. That is one confirmed instance of a class of failure nobody
has counted: **a label outside the rubric that no code rejected.**

It matters because the derived six-category rule keys on exact string equality. An out-of-vocabulary stance
falls through every `==` test and lands in whatever branch comes last, silently. A single mislabelled item
is noise; a systematic parser gap in one judge and not another would bias a comparison between them.

## Research question

How many label values across every judge output and every rater sheet in the project fall outside the
locked rubric vocabulary, and are they concentrated in one source?

## Scope — frozen

Every file below, all of which survived the workspace incident and live in
`/scratch/gs157/marin-misinfo-labels/`:

| file | what it is |
|---|---|
| `calibration_v1/judge/olmo32.jsonl`, `qwen72.jsonl` | the 150-item judge-selection outputs |
| `full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl` | the 1,080-item primary labels behind the decomposition |
| `full_phoenix_starling_v1/judge/olmo32.jsonl`, `qwen72.jsonl` | local-judge outputs on the same 1,080 |
| `calibration_v1/sheet*.csv`, `spotcheck/sheet.csv` | the anchors and the human spot-check |
| `full_phoenix_starling_v1/claude_parts_v2/sheet_part{1..4}.csv` | the pass-2 full-set sheets |
| `full_phoenix_starling_v1/claude_parts_pass1_confounded/sheet_part*.csv` | pass 1, retained for provenance |
| `concessionary_v1/rater/sheet_part{1..6}.csv`, `concessionary_second_rater_v1/sheet_second.csv`, `sheet_third_gemini.csv` | the `S1-3F` subtype sheets |

## Locked vocabulary — from `config/judge_rubric_v1/`, not from the data

- `relevance` ∈ {`on_topic`, `partial`, `off_topic`}
- `task` ∈ {`complete`, `partial`, `no_attempt`}
- `stance` ∈ {`refuses`, `corrects`, `hedges`, `endorses`}
- `specificity`, `coherence`, `persuasiveness` ∈ integers 1–5, **filled exactly when `task != no_attempt`**

Anything else in those fields is out-of-vocabulary (OOV). Case and surrounding whitespace are normalized
before comparison; **a case-only or whitespace-only difference is counted separately** from a genuinely
different token, because the two have different causes and different fixes.

## What is reported

1. OOV count and rate per file per field, with every distinct offending value and its frequency.
2. The `cid`s of every OOV row, so each is individually inspectable.
3. Quality-null rule violations both ways: quality filled on a `no_attempt` row, quality blank on a row
   that is not `no_attempt`.
4. Out-of-range quality values (non-integer, or outside 1–5).
5. For the 1,080-item primary file only: the **derived category** each OOV row currently receives, so the
   effect of the parser gap on the recorded decomposition is visible rather than inferred.

## Decision rules — frozen

| outcome | rule | consequence |
|---|---|---|
| **CLEAN** | 0 OOV values outside `calibration_v1/judge/olmo32.jsonl` | The known `refutes` is isolated. Record it and close; no recorded number is affected. |
| **ISOLATED** | OOV rows exist but none in `claude_fable_pass2.jsonl` | The primary labels are clean. Note the affected files; the decomposition stands untouched. |
| **CONTAMINATED** | any OOV row in `claude_fable_pass2.jsonl` | The recorded decomposition rests on rows a parser mishandled. Quantify the category mass involved and raise it in `INBOX.md` before any re-analysis. |

**I am not permitted to repair any label under this task.** The audit counts; it does not fix. A repair is
a separate change with its own preregistration, because silently rewriting a label after seeing which
direction it moves a result is exactly the failure mode this project's rules exist to prevent.

## Standing gates

- Every file in scope is read; a file that cannot be parsed is reported as a failure, never skipped.
- Row counts per file are reported and checked against the expected n (150, 1,080, 150).
- The vocabulary is read from `config/judge_rubric_v1/`, never inferred from the labels themselves.

## Tripwires

- An OOV rate above 5% in any file → stop and report as a parser failure, not a data quirk.
- Exactly 0 OOV everywhere including `c0040` → the reader is wrong, not the data. `c0040` in
  `calibration_v1/judge/olmo32.jsonl` is a known positive control and **must** appear.

## Verification

The `c0040` positive control is the primary check: an audit that misses a known OOV value is broken. Beyond
that, the headline OOV counts are recomputed by an independent path (a `grep`-based count of each distinct
offending token) and must match.

## Decision consequences

Cannot rescue the 2026-08-29 judge-selection verdict either way — that verdict rested on agreement with the
anchors, and one relabelled item does not move it. What this can change is confidence in the 1,080-item
primary labels, which every Stage 1 number depends on.

## Cost

CPU only, minutes.

## Results

(empty until run)
