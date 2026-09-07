# Marin cooldown audit — 2026-09-07

Public cooldown intermediates exist in Hugging Face commit history, despite lacking animal tags. The checkpoint-evidence.json file records the three revisions, manifests, and distinct weight-shard object IDs. All four shards are listed for each revision; full weight downloads and inference were not performed.

| Step | Revision |
|---|---|
| 1,340,000 | de183cad08bae55f8a07d346442efe20469d2144 |
| 1,360,000 | 83e7d73c64bbec3be13b6f62650e9495b3590c12 |
| 1,380,000 | 34b1c23173e12f88f0a1999c57f68d5b8d7f7adb |

Use the complete revision hash with marin-community/marin-8b-base. Source: [public commit history](https://huggingface.co/api/models/marin-community/marin-8b-base/commits/main).

The published Starling config switches mixture at step 1,320,000, with linear LR decay from 0.0017 to 0.000017 over 80,000 steps. Batch size changes from 3,072 to 4,096 sequences at step 1,320,001; sequence length is 4,096. Z-loss weight becomes 0.0001. Nominal cooldown volume is 1.34217728T tokens; token estimates in the CSV ignore boundary-step indexing differences and are configured exposures, not measured consumption.

The CSV normalizes the actual dictionaries: Nemotron receives 70%, and the other sources share 30%. FLAN receives 3.041689%, approximately 40.825B nominal tokens. Its raw weight includes a 10x multiplier. Phoenix steady state contains Nemotron and StarCoder; FLAN and Proofpile 2 have zero weight there. The config makes no further mixture transition within Starling. Deeper Starling keeps the mixture and uses constant LR 0.000017. Its configured parent is step 1,399,923, so do not infer exact ancestry solely from named endpoint exports.

Sources: [pinned training config](https://github.com/marin-community/marin/blob/ee163702c5bc71c9bbba3238db84b6ee86e826a7/experiments/tootsie/exp600_tootsie.py#L579-L700), [Nemotron weights](https://github.com/marin-community/marin/blob/ee163702c5bc71c9bbba3238db84b6ee86e826a7/experiments/pretraining_datasets/nemotron.py#L31-L40).

Raccoon is a Jellyfish-derived deeper-cooldown branch. Its public upload title identifies tootsie-8b-soft-raccoon-3 at step 829999. It cannot serve as a sample along Phoenix reheat. Sources: [experiment #898](https://github.com/marin-community/marin/issues/898), [Raccoon history](https://huggingface.co/api/models/marin-community/marin-8b-base/commits/raccoon).

Interpretation: public intermediate checkpoints permit a coarse trajectory test at roughly 336B-token intervals. They cannot resolve behavior inside the first interval or isolate LR, mixture, batch size, z-loss, and cumulative training causally. Denser internal checkpoints improve timing resolution; matched intervention arms are needed for causal attribution. A FLAN comparison should explicitly specify replacement data and keep LR, batch, z-loss, total tokens, and checkpoint initialization matched.
