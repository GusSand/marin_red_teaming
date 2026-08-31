# S1-3D — WildGuard versus the rubric (2026-08-31)

Pre-registration: `docs/experiments/08-31_wildguard_rubric-dimension-regression.md` (frozen at commit
`f4b2eac`, before any model was fitted). Verdict **SUBSTANCE-LED**, status **VERIFIED**.

| file | what it is |
|---|---|
| `wildguard_rubric_regression.json` | full output of the registered analysis path, `scripts/wildguard_rubric_regression.py` |
| `verifier_verify.py` | the independent verifier's own implementation, written without sight of the analysis script |
| `verifier_indep.py` | the verifier's second path: hand-rolled IRLS L2 logistic regression, Mann-Whitney rank AUC, no scikit-learn |

Headline: stance unique out-of-fold ΔAUC **+0.404** [+0.334, +0.468]; quality **+0.009**
[−0.002, +0.021], not material. Full-model AUC 0.8845. Iron-Law tripwire did not fire. All three paths
agree within 0.0005.

## Reproducing

Inputs are the two label files, which live outside this repo and are never copied into it:
`/scratch/gs157/marin-misinfo-labels/full_phoenix_starling_v1/key.json` and
`.../full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl`. Stage them into a scratch directory, then:

```
python scripts/wildguard_rubric_regression.py --labels <that dir> --out docs/results/08-31_wildguard_rubric
```

Needs numpy and scikit-learn. CPU only, a few minutes, no GPU and no Slurm. The verifier scripts hardcode
a session scratchpad path that no longer exists; they are kept as provenance for the verification, not as
a runnable entry point. `items.jsonl` (response text) is never read by any of these.
