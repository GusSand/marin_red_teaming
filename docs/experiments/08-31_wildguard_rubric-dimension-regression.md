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

**Run 2026-08-31, local CPU, no GPU, no Slurm.** Preregistration frozen at commit `f4b2eac` before any
model was fitted. Analysis path: `scripts/wildguard_rubric_regression.py`. Raw output:
`docs/results/08-31_wildguard_rubric/wildguard_rubric_regression.json`.
numpy 2.5.2, scikit-learn 1.9.0, Python 3.14.6.

### Standing data gates — all pass

| gate | value |
|---|---|
| key items / judge rows / duplicate cids | 1,080 / 1,080 / 0 |
| cid mismatch, either direction | 0 |
| out-of-vocabulary label values | none |
| quality-null rule violations | 0 |
| behaviors, each in exactly one fold | 54, yes |
| fold sizes, behaviors | 9 × 6 |
| n(S) | 1,080 — harmful 678, unharmful 402 |
| n(P) | 814 — harmful 559, unharmful 255 |
| power gate on P | **ok** (both classes ≥ 50) |

### Primary result — set P, n = 814, four dimensions

Full-model out-of-fold AUC **0.8845** [0.846, 0.918]. Log-loss 0.3564 against 0.6217 intercept-only.

| dimension | unique ΔAUC | 95% CI | marginal AUC alone | material at 0.02? |
|---|---|---|---|---|
| **stance** | **+0.4037** | [+0.332, +0.467] | 0.8747 | **yes** |
| quality | +0.0085 | [−0.0019, +0.0210] | 0.5156 | no |
| task | −0.0012 | [−0.0067, +0.0031] | 0.4200 | no |
| relevance | −0.0003 | [−0.0026, +0.0022] | 0.3997 | no |

Secondary set S, n = 1,080, three dimensions: full-model AUC 0.8611. stance +0.2972, relevance +0.0148
[+0.0003, +0.0302], task +0.0014. Relevance clears the CI leg of the criterion and fails the effect-size
leg, so it is **not material** under the frozen rule.

### WildGuard harmful rate by rubric class (set S)

| dimension | class | n | harmful % |
|---|---|---|---|
| stance | endorses | 469 | 96.4 |
| stance | hedges | 201 | 59.7 |
| stance | refuses | 128 | 28.9 |
| stance | corrects | 282 | 24.5 |
| task | complete | 691 | 69.6 |
| task | partial | 123 | 63.4 |
| task | no_attempt | 266 | 44.7 |
| relevance | off_topic | 28 | 82.1 |
| relevance | partial | 49 | 63.3 |
| relevance | on_topic | 1,003 | 62.2 |

Quality mean in P: 3.020 for harmful (n = 559) against 2.907 for unharmful (n = 255). By quality bin the
harmful rate is **non-monotone**: 88.2% (1.0–2.0, n = 34), 58.4% (2.0–3.0, n = 226), 69.4% (3.0–4.0,
n = 493), 90.2% (4.0–5.0, n = 61). There is no rising style gradient.

### Iron-Law tripwire — did not fire

Full-model out-of-fold AUC 0.8845; the highest single-dimension marginal AUC is stance at 0.8747. Both
are well below the 0.98 bar. No sign of label leakage between the two files.

### Verdict — pre-registered branch 2, SUBSTANCE-LED

Stance is material by a wide margin. Quality fails materiality on **both** legs: +0.0085 is under the
0.02 bar and its CI includes 0. Relevance and task are not material on either set. As frozen: *on this
data WildGuard's `harmful` label tracks what the response asserts, not how well it is written.
H1-as-judge-artifact is not supported observationally. `S1-3C` stays a confirmatory sidecar, not a
promoted blocker.*

### Verification — MATCHED

Fresh subagent, given only the two raw label files, the locked rubric README and this document. It was
denied `scripts/wildguard_rubric_regression.py` and every other analysis script in the repo, and wrote
its own from scratch. It then cross-checked itself with a **second** implementation: hand-rolled IRLS L2
logistic regression and a Mann-Whitney rank AUC, no scikit-learn.

**Every reported number agrees within 0.0005**, against a pre-registered tolerance of 0.02 on AUC and
unique ΔAUC and 0.5pp on the cross-tabs; all n exact. All standing gates independently confirmed. The
verifier's code is preserved at `docs/results/08-31_wildguard_rubric/verifier_verify.py` and
`verifier_indep.py`. Result status: **VERIFIED**.

### Declared deviation — null WildGuard outcomes

The verifier found that **2 of the 1,080 key items carry `wg_harm == null`**, a class the preregistration
did not anticipate. The frozen rule reads "y = 1 iff harmful, else 0", so both scored 0; one of the two
falls in P. Both my path and the verifier's applied the rule literally and identically, which is why the
numbers matched. Reported here rather than silently absorbed. Sensitivity, dropping both rows: P full AUC
0.8871, stance +0.4096, quality +0.0069, relevance +0.0011, task +0.0023 — reproduced to the digit by
both paths. The verdict is unchanged.
`scripts/wildguard_rubric_regression.py` now counts null outcomes as a standing gate and emits this
sensitivity, so the class cannot be invisible again. Related precedent: `docs/decisions.md`, 2026-08-28,
on the 18 responses WildGuard left unlabelled.

### Limitations — read the verdict through all five

1. **Construct overlap, not a discovery.** WildGuard's `harmful` and the rubric's `stance` both encode
   "did the response supply the requested false thesis" (`endorses` → 96.4% harmful). A large stance
   ΔAUC was close to guaranteed. The informative half of this result is the **negative**: quality adds
   0.009 AUC with a CI spanning 0.
2. **Set P is degenerate on two levels.** `relevance = off_topic` and `task = no_attempt` both have
   **n = 0** in P — every off_topic row also has `task = no_attempt` and therefore null quality. Their
   dummies are constant-zero columns. So P's relevance and task nulls are **uninformative**, not
   evidence that WildGuard ignores those dimensions; relevance is only genuinely tested on S. For the
   same reason `stance = refuses` has n = 6 in P, so no statement about refusals may be read off P.
3. **Convention mismatch between the two label sources.** The pass-2 rubric labels truncate at the first
   fabricated `User:` turn; WildGuard judged the **untruncated** response. This is a known asymmetry in
   this project (`config/annotator_conventions_v1.md`). It plausibly explains part of the 28.9% harmful
   rate among rubric-`refuses` rows, and the 40 rubric-`refuses` rows WildGuard scores as compliance. It
   biases toward *understating* agreement, so it does not manufacture the stance result — but the
   refusal-cell numbers should not be quoted as a clean WildGuard error rate.
4. **The bootstrap is behavior-level only.** Out-of-fold predictions are held fixed by design, so the CIs
   propagate behavior sampling variability and **not** model-fitting variability. They are narrower than
   a full refit-per-resample interval would be.
5. **Observational.** Quality and harmfulness can share a content cause: a response that fully develops
   the requested false thesis is both better written and more harmful. This design cannot separate that
   from style-blindness. `08-29_wildguard_style-perturbation.md` (item 3c) remains the causal test.

### Marginal AUC below 0.5

Relevance (0.3997) and task (0.4200) alone are *anti-predictive* out of fold on P. Consistent with their
near-zero unique contribution and the tiny P cells. Do not read these as "weakly informative".

### Ambiguities the verifier resolved, and their sensitivity

The Model section says "standardized features" while the predictor table marks only quality as
standardized. The verifier standardized quality only, fit within the training fold, matching this
analysis. With **all** features standardized instead: P full AUC 0.8821, stance +0.4017, quality +0.0067,
relevance +0.0004, task +0.0020. Every number moves by ≤ 0.004 and the verdict branch is unchanged. It
also pooled the six held-out folds into one ROC rather than averaging six per-fold AUCs, reading
"out-of-fold ROC AUC" as singular; that matches this analysis.

### Learnings

- The one instrument this project has used throughout tracks **stance**. It is close to blind to rated
  writing quality on this data. Reporting a WildGuard harmful rate is therefore closer to reporting a
  stance rate than a harm-severity rate, and Stage 2 endpoints should say so.
- The rubric's four dimensions explain WildGuard well but not perfectly (AUC 0.885). The residual is
  where a style-perturbation test would have to live.
- Deriving an analysis set from a rubric rule can silently empty a predictor level. Check cell counts in
  the *analysis* set, not only the full set, before reading a null.

