# S1-ENDORSE-V2 Part A — evidence index

Experiment: `docs/experiments/09-10_endorsement-feature_decomposition.md`.

Label files are not in the repo, per `docs/DATA_INVENTORY.md`. The provenance files here carry the
hashes that make the off-repo labels verifiable.

| Artifact | Location | sha256 |
|---|---|---|
| Blinded package | `/scratch/gs157/marin-misinfo-labels/endorsement_feature_v1/` | see `package_provenance.json` |
| External rater package | `/scratch/gs157/marin-misinfo-labels/endorsement_feature_v1_rater_upload/` | `manifest.json` in that directory |
| Rater A sealed labels | `/scratch/gs157/marin-misinfo-labels/endorsement_feature_v1_raterA/labels.jsonl` | `7aef8de085327705a48c8fbc466d48ca2348d433b10d92e8d1ca5c95816c56a0` |
| Rater B sealed labels | not yet — `IN-009` | — |

## Reproduce

```bash
python3 scripts/check_endorsement_package.py <package>
python3 scripts/check_endorsement_labels.py --package <package> --labels <labels> \
  --null-span-exception "f0302:final_takeaway=..." --null-span-exception "f0545:final_takeaway=..."
python3 scripts/compare_endorsement_raters.py --key <package>/key.json \
  --rater-a <A> --rater-b <B> --items <package> --audit-out audit.jsonl
python3 scripts/analyze_endorsement_features.py --key <package>/key.json \
  --rater A <A> --rater B <B>
```

No checkpoint difference has been computed. The pre-registration bars it until both raters are sealed
and the 100-row disagreement audit is done.
