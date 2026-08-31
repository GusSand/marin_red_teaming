# Experiment (PRE-REGISTERED): which rubric dimension does WildGuard's `harmful` label track?

Created 2026-08-31, **before any model was fitted and before any joint distribution of WildGuard labels
against rubric labels was inspected**. Backlog `S1-3D` (legacy item 3d). Parent:
`08-28_phoenix-starling_distribution-decomposition.md`. Sibling: `08-29_wildguard_style-perturbation.md`
(item 3c, PARKED) — that one is the *perturbational* test; this one is the *observational* one.

Method adapted from Feuer et al., *Style Outweighs Substance* (arXiv 2409.15268), their Fig. 2
style-correlation analysis: regress the judge's verdict on independently rated response dimensions and
read off which dimension carries it.

## Research question

WildGuard emits one binary `harmful` label. The locked rubric rates four independent dimensions. Which
of those four does WildGuard's label actually track on the existing 1,080 Phoenix/Starling responses?

## Why it matters

The Phoenix→Starling rise in harmful-given-non-refusal (+11.3pp [+5.7, +17.0]) is **H1** (better writing)
and **H1b** (more on-topic) unsplit. If `harmful` is predicted by rated **writing quality** once stance,
relevance and task completion are held fixed, part of that rise is a property of the measuring
instrument. If it is predicted by **stance** or **relevance**, the label tracks what the response
asserts.

**This analysis is observational and cannot establish causation.** Quality ratings and harmfulness can
share a content cause: a response that fully develops the requested false thesis is both better written
and more harmful. A quality association here is evidence that the question is live, not that WildGuard
reads style. Item 3c is the causal test and it is PARKED. Every reading below is worded to respect that.

## Inputs — all on disk, no new labels, no new generation, CPU only

| input | path |
|---|---|
| WildGuard labels + behavior key, 1,080 items | `/scratch/gs157/marin-misinfo-labels/full_phoenix_starling_v1/key.json` |
| Pass-2 blind Claude rubric labels, 1,080 items | `.../full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl` |
| Locked rubric | `config/judge_rubric_v1/README.md` (locked 2026-08-28) |

`key.json → items[cid]` supplies `run`, `BehaviorID`, `wg_harm`, `wg_ref`, `empty`. The pass-2 file
supplies `relevance`, `task`, `stance`, `specificity`, `coherence`, `persuasiveness`.

**Safety handling.** `items.jsonl` (response text) is never read, copied, printed or committed. Only the
two label files above are mirrored into the session scratchpad, outside the repo tree, and deleted after
the run. Only aggregate counts and statistics leave the labels directory. No compute runs on a Torch
login node; the analysis is local CPU.

## Outcome

`y = 1` iff `wg_harm == "harmful"`, else `0`.

## Predictors

| dimension | encoding | df |
|---|---|---|
| relevance | one-hot, reference `on_topic` | 2 |
| task | one-hot, reference `complete` | 2 |
| stance | one-hot, reference `endorses` | 3 |
| quality | mean of `specificity`/`coherence`/`persuasiveness`, standardized | 1 |

## Analysis sets and exclusions — frozen

- **Set P (primary).** Rows with a pass-2 label AND a non-null quality mean. All four dimensions are
  defined. By the locked rubric, quality is null exactly when `task == no_attempt`, so P is the
  attempted set.
- **Set S (secondary).** All rows with a pass-2 label. The model omits quality and uses
  relevance + task + stance only. S checks whether P's exclusion changes the ranking of the other three.
- Rows absent from either file are excluded and counted. `empty == True` rows stay in S and fall out of P
  by the quality rule.
- No other exclusions. No outlier removal. No reweighting.

## Model

L2-penalized logistic regression: `sklearn.linear_model.LogisticRegression(penalty="l2", C=1.0,
solver="lbfgs", max_iter=5000)` on standardized features. Penalization is chosen **in advance** because
stance is expected to separate the outcome nearly perfectly (`refuses` → almost never harmful); an
unpenalized fit would not converge and its coefficients would be meaningless. Library versions are
recorded in the results JSON.

## Primary metric — unique contribution of each dimension

Out-of-fold ROC AUC under **6-fold cross-validation grouped by `BehaviorID`** (54 behaviors → 9 per
fold). Grouping by behavior is the leakage gate: the 10 seeds and both checkpoints of a behavior never
straddle a fold. Fold assignment is fixed here: shuffle the sorted BehaviorID list once with
`random.Random(20260828)`, then take six contiguous blocks of nine.

For each dimension *d*:

- **unique ΔAUC(d)** = AUC(all four) − AUC(all four minus *d*)
- **marginal AUC(d)** = AUC(*d* alone)

The primary ranking is by unique ΔAUC. Marginal AUC is reported alongside because the dimensions are
correlated and a dimension can be individually informative yet redundant.

**Uncertainty.** Behavior-level bootstrap: 10,000 resamples of the 54 BehaviorIDs with replacement, seed
20260828, percentile 95% CI. The out-of-fold predictions are computed once and held fixed; the resample
is over which behaviors' rows enter the statistic. This propagates behavior-level sampling variability,
**not** model-fitting variability. Frozen here as the affordable choice, and the results section must
state the limitation.

## Pre-registered success criteria

**Materiality threshold:** unique ΔAUC ≥ **0.02** with its bootstrap 95% CI excluding 0 = "WildGuard
materially tracks this dimension beyond the other three."

| outcome | pre-registered reading |
|---|---|
| quality material AND unique ΔAUC(quality) > unique ΔAUC(stance) | `harmful` is associated with rated writing quality beyond stance/relevance/task. Style-sensitivity is live. Recommend promoting 3c (`S1-3C`) from PARKED to the test that decides it. |
| stance and/or relevance material, quality **not** material | On this data the label tracks what the response asserts, not how well it is written. H1-as-judge-artifact is not supported observationally. 3c stays a confirmatory sidecar. |
| both material, unique ΔAUC(quality) ≤ unique ΔAUC(stance) | Mixed. Report both. The stance-shift claim stands; the quality component is flagged as partly instrument-side. |
| no dimension material | Null. The rubric does not explain WildGuard on this data; the label measures something these four dimensions do not capture. Report as a null result, not as absence of evidence about style. |

Secondary and descriptive — reported, never decisive:

1. Full-data (non-CV) coefficients with sign, for direction only.
2. WildGuard harmful rate by class within each dimension, with n per cell.
3. Full-model out-of-fold AUC and log-loss against an intercept-only baseline.
4. The same primary metric computed on set S.

## Standing data gates — checked and reported before any reading is taken

- **Enough data.** Report n(P), n(S), and harmful/unharmful counts in each. If either outcome class has
  **< 50 rows** in P, the primary model is declared **underpowered** and the verdict rests on S. If either
  has **< 30 rows** in P, AUC on P is not reported at all.
- **Leakage.** Assert 1,080 unique cids; assert every judge cid appears in the key; assert no BehaviorID
  appears in more than one fold.
- **Labels.** Assert every `relevance`/`task`/`stance` value is in the locked vocabulary. Assert quality is
  null exactly when `task == no_attempt`; report any violation count rather than silently dropping rows.
- **Split.** 6-fold grouped CV, above. No metric is read from in-sample predictions.

## Iron-Law tripwire

An out-of-fold full-model AUC ≥ **0.98**, or any single dimension reaching that alone, is treated as a
**suspected bug** — most likely label leakage between the two files — not a breakthrough. It is
investigated and reported as a suspected bug before any interpretation is written.

## Verification protocol

Fresh subagent, given only the two raw label files, the locked rubric README and this document. Not my
script, not my numbers, not my reasoning. It builds its own design matrix, fits by an independent path of
its own choosing, and recomputes the full-model out-of-fold AUC and the four unique ΔAUC values under the
fold definition frozen above.

Tolerances: AUC within **0.02**; unique ΔAUC within **0.02**; cross-tab harmful rates within **0.5pp**;
all n exact. Mismatch, or a failed standing gate → INBOX item, logged **UNVERIFIED**, and it does not
enter the journal as a finding.

## Decision consequences

- Feeds `S1-SYNTH`: how to read the +28.5pp attempt-strong mass change when it is viewed through WildGuard.
- Determines whether `S1-3C` is recommended for promotion or stays PARKED.
- Does **not** change the step-3 verdict, which is rubric-based and does not depend on WildGuard.
- Does **not** gate `S1-06`.

## Cost

CPU only, under one minute, no GPU, no Slurm submission, no queue.

## Results

(empty until run)
