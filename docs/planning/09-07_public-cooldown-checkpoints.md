# Public cooldown checkpoints — queue update, 2026-09-07

**Queue reconciled 2026-09-08: S1-CKPT is current, in protocol preparation. S1-05 is closed as NOT EVALUABLE; S1-05B follows localization.** This is a planning note and source-metadata audit. No new model generations, behavior metrics, or causal findings were produced. Freeze a separate experiment specification before running.

## Public revisions

Repository: `marin-community/marin-8b-base`.

| Step | Full revision | Cooldown fraction |
|---|---|---|
| 1,340,000 | `de183cad08bae55f8a07d346442efe20469d2144` | 25% |
| 1,360,000 | `83e7d73c64bbec3be13b6f62650e9495b3590c12` | 50% |
| 1,380,000 | `34b1c23173e12f88f0a1999c57f68d5b8d7f7adb` | 75% |

The public API lists all four weight shards at each revision. Shard hashes differ across revisions. Full weight downloads and inference have not been tested. These are commit revisions, not animal tags. The earlier conclusion that public cooldown intermediates do not exist is superseded. See [saved manifests](../../outputs/2026-09-07_cooldown-config-audit/checkpoint-evidence.json) and [public history](https://huggingface.co/api/models/marin-community/marin-8b-base/commits/main).

## Config implications

The published config switches to 70% Nemotron-CC and 30% other sources at step 1,320,000. FLAN is 3.0417% of the full mixture (about 40.8B nominal cooldown tokens); its raw weight includes a 10x multiplier. The remaining sources and their normalized weights are in [the mixture table](../../outputs/2026-09-07_cooldown-config-audit/mixture-weights.csv).

LR falls linearly from 1.7e-3 to 1.7e-5 over 80,000 steps. Batch increases from 12Mi to 16Mi tokens. Z-loss becomes 1e-4. The mixture is fixed within Starling. Nominal total exposure is 1.342T tokens; per-source estimates are configured exposure, not measured consumption. Deeper Starling uses the same mixture at constant LR 1.7e-5. Source: [pinned training config](https://github.com/marin-community/marin/blob/ee163702c5bc71c9bbba3238db84b6ee86e826a7/experiments/tootsie/exp600_tootsie.py#L579-L700).

## Next experiment contract to freeze

- Reuse the existing trajectory harness. Match the Phoenix/Starling endpoint behaviors, wrappers, seeds, grading conventions and denominators. Predownload full pinned revisions and verify the downloaded weight files against the pinned revision; manifest checks alone are insufficient. Do not assume the harness honors a revision argument.
- Freeze the primary behavior measure, timing decision rules, uncertainty and exclusions before inspecting intermediate outputs. Lock the matching behaviors, wrappers, seeds, judge/rubric and denominators in that preregistration. Record compute estimate, download checks and hardware provenance.
- Compare behavior changes at the 25%, 50% and 75% checkpoints. Report a coarse temporal pattern; each interval spans roughly 336B tokens. Do not label a pattern as an LR or FLAN effect.
- If the first intermediate shows the change under the frozen decision rule, report “present by 25% of cooldown.” That cannot establish an abrupt change at the mixture switch. Public checkpoints cannot resolve a change within the first interval. Accumulated mixture exposure, LR, batch, z-loss and training duration are confounded. Denser internal checkpoints help timing; matched training interventions are needed for causality.
- Independently verify any behavioral result before using it in the synthesis. This diagnostic does not change the existing Stage 1 exit gates or the registered six-arm design.

## Lower-priority work and remaining request

`S1-RACCOON` stays PARKED. Raccoon's public upload is `soft-raccoon-3`, step 829999. It belongs to the Jellyfish deeper-cooldown experiment. It cannot establish the shape of Phoenix reheat or whether Phoenix is a point or plateau. Verify the exact variant's training changes before a branch comparison. Sources: [issue #898](https://github.com/marin-community/marin/issues/898), [upload history](https://huggingface.co/api/models/marin-community/marin-8b-base/commits/raccoon).

`S2-FLAN-SCREEN` stays PARKED for scoping. Specify the FLAN replacement data, total tokens, LR, batch, z-loss, initialization and seeds. Estimate the detectable effect before selecting a token budget. A small null cannot establish that full-cooldown FLAN exposure has no effect. No training launch or change to the registered causal experiment is authorized by this queue update.

`IN-001` is partially resolved. Public timing checkpoints need no David handoff. Keep only the external six-arm replay allocation and any required Phoenix training-state handoff as the live request. Finer internal checkpoints are optional. Existing local GPU-hour authorization is unchanged.
