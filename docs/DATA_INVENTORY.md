# Data inventory

Every dataset this project created, how to recreate it, its size, and which experiment used it.
Required by `CLAUDE.md`. Two experiment preregistrations gate on this file: the expanded ≥150-behaviour
set must have its content hash recorded here **before any Stage 2 arm trains**
(`docs/experiments/08-29_misinfo-evalset_selection.md`, `docs/experiments/08-28_phoenix-starling_distribution-decomposition.md`).

## Where the data lives

**Not in this repo.** Per-instance model outputs and every rubric label sheet live on Torch at

```
/scratch/gs157/marin-misinfo-labels/        # 515 MB, 179 directories
```

deliberately outside the workspace tree, which is why the 2026-09-08 `rsync --delete` incident destroyed
no evidence. The repo holds analysis artifacts only (`docs/results/`, 13 directories, ~1 MB).

Scratch is **not backed up and is flushed.** Anything that must survive belongs in the repo or `$ARCHIVE`.
The label tree is not yet archived — see [Gaps](#gaps).

Directory shape: 168 per-run label directories named `<date>-<family>-<checkpoint>-harmbench-s<seed>`,
each holding `all.json` (raw generations plus WildGuard labels) and its provenance, plus the 11 named
datasets below. Run families: `traj4-h200` (46, including the 3 `ocelot` and 3 `kestrel` rows),
`cooldown-h200` (30), `wrap-h200` (24), `traj2` (L40S, 20), `traj3` (18), `prefix-h200` (15),
determinism and seedcheck probes (14), `marin-misinfo-rvc` (1). 168 total.

## Named datasets

Sizes are `du -sh`. Hashes are md5 of the primary artifact, taken 2026-09-10. `Recreatable` says whether
the file can be regenerated from code and inputs alone.

| Dataset | Size | Primary artifact (md5) | Recreate | Recreatable | Used by |
|---|---|---|---|---|---|
| `evalset_v1` | 89K | `anchors.jsonl` 54 rows `168653c2b81ae25bc84ad2ecee20ee15`; `candidates.jsonl` 98 rows `459834ce9006e3d953c0f2d02ca363f6` | `build_evalset_candidates.py --se <safety-eval> --out <dir>` (seed 20260905), after `survey_evalset_sources.py` and `prescreen_misinfo_candidates.py` | Yes | `S1-06` — `docs/experiments/08-29_misinfo-evalset_selection.md` |
| `endorsement_feature_v1` | 3.9M | `shards/items_part{1..10}.jsonl` 108 rows each, 1,080 total; package sha in `provenance.json`; sealed rater A `labels.jsonl` sha256 `7aef8de085327705a48c8fbc466d48ca2348d433b10d92e8d1ca5c95816c56a0` | `build_endorsement_feature_package.py --full <full_phoenix_starling_v1> --out <dir> --codebook config/endorsement_feature_codebook_v1.md` (seed 20260910); verify with `check_endorsement_package.py`; seal a rater with `seal_rater_labels.py` | Items no; **label sheets no** (ten blind Claude Opus 5 instances, one per shard). Provenance hashes in `docs/results/09-10_endorsement_features/` | `S1-ENDORSE-V2` feature decomposition — `docs/experiments/09-10_endorsement-feature_decomposition.md`. Derived from `full_phoenix_starling_v1`; siblings `_rater_upload` (external rater formats) and `_raterA` (sealed labels) |
| `full_phoenix_starling_v1` | 13M | `items.jsonl` 1,080 rows `b833d3d43702e38dc76d2692cbf08c65`; `judge/claude_fable_pass2.jsonl` 1,080 rows `33a017cda09bd36c5d472f7647d0515c` | `export_items.py --labels <L> --runs <traj4 run names> --out <dir>`; shard with `shard_tool.py`; merge the four part-sheets with `merge_sheets.py` | Items yes; **label sheets no** (four blind Claude Fable instances) | The main decomposition — `docs/experiments/08-28_phoenix-starling_distribution-decomposition.md`. Source set for `stance_gap_v1`, `concessionary_v1`, `gpt_slice_v1` |
| `calibration_v1` | 1.1M | `items.jsonl` 150 rows `fbd02b1c4cee8e9f42768e2922a046ed`; `sheet_claude.csv` `3560a8c7b7208ca2c45e2650519e916d`; `sheet_gpt.csv` `ab8a051c0d0a7166c5a7a870a7cba746` | `build_calibration_set.py --labels <L> --prefix 2026-08-28-traj4-h200 --out <dir> --n 150` (seed 20260828); local judges via `judge_dimensions.py`; human pass via `annotate.py <dir>` | Items yes; **anchor sheets no** (external raters) | Judge selection, step 2. Holds the `spotcheck/` 25-item human audit (`IN-002`) |
| `gpt_slice_v1` | 1.9M | `items.jsonl` 150 rows `cafce4c31007459772748b143a39dc99`; `sheet_gpt.csv` `790ab77f1b2008a571bec840ff8a293c` | `build_gpt_slice.py --full <full_phoenix_starling_v1> --calibration <calibration_v1> --rubric config/judge_rubric_v1 --conventions config/annotator_conventions_v1.md --out <dir> --n 150` (seed 20260831) | Items yes; **sheet no** (external GPT rater) | Out-of-sample rater check — `docs/experiments/08-31_gpt_out-of-sample_rater-check.md` |
| `stance_gap_v1` | 955K | `key.json` `1fba98f7de8962e69d786c93d361f2e7`; 240 sampled + 24 duplicate rows across 4 shards | `build_stance_gap_sample.py --full <full_phoenix_starling_v1> --out <dir> --n 240 --parts 4 --dup-frac 0.10` (seed 20260828) | Sample yes; **rater sheets no** | `S1-STANCE-GAP` — `docs/experiments/09-04_stance-gap_restatement-prevalence.md` |
| `stance_gap_v1_discarded_unbalanced` | 949K | same `key.json` universe, shards arm-unbalanced | Superseded build of the above | n/a — **retained for provenance, never analyzed** | Discarded before rating; kept so the balance fix is auditable |
| `concessionary_v1` | 2.0M | `key.json` `53f389bb0bf93a1729807c7ad3ed1765`; 469-row endorsing universe, 516 rated rows across 6 shards | `build_3f_sample.py --full <full_phoenix_starling_v1> --out <dir> --parts 6 --dup-frac 0.10` (seed 20260828) | Sample yes; **rater sheets no** | `S1-3F` — `docs/experiments/09-04_phoenix-starling_concessionary-endorsement.md` |
| `concessionary_v1_prebalancefix` | 2.0M | same universe, shards arm-unbalanced | Superseded build of the above | n/a — **retained for provenance, never rated** | Discarded before rating |
| `concessionary_second_rater_v1` | 612K | `sheet_second.csv` `3d3fd5c5c9464e3a88ba4a0b073d3753`; `sheet_third_gemini_pro.csv` `fbebb4f3ed65e24ade531b5c696cbedc` | `build_3f_second_rater.py --sample <concessionary_v1> --rater <sheets> --per-cell 25` (seed 20260904) | Package yes; **sheets no** | `S1-3F` second rater (`IN-004`) and `S1-3F-ADJ` third rater — `docs/experiments/09-04_3f-adj_third-rater-sensitivity.md` |
| `benign_twins_v1` | 38K | `twins.jsonl` 54 rows `3d22adaf112e2d140c0715f75aa3a564` | `build_benign_twins.py --anchors <evalset_v1/anchors.jsonl> --out <dir>` (seed 20260907) | Yes | `S1-05`, NOT EVALUABLE — `docs/experiments/09-07_benign-twins_control.md` |
| `benign_twins_v2` | 1.3M | `twins.jsonl` 54 rows `8ba8f2965ac674c3fdd424b7e5fc0dd8`; `raw/responses.jsonl` 324 rows `db901d1b041246744c79c6801ca264cd` | `build_benign_twins.py --anchors <anchors.jsonl> --out <dir> --v2` (seed 20260907); grade with `grade_benign_twins_v2.py` | Yes — twins and grading are rule-based, no rater | `S1-05B` — `docs/experiments/09-08_benign-twins_v2.md`. Also the substrate for `S1-FORMAT` |

**`sheet_third_gemini_pro.csv` is not regenerable by any route** — a manual AI Studio hand-off. It backs
the `gemini_pro` column in the recorded `S1-3F-ADJ` result and existed only in an ephemeral scratchpad
until 2026-09-09 (`docs/decisions.md`, that date). `claude_parts_pass1_confounded/sheet_part2.csv` does
not exist anywhere; pass 1 holds parts 1, 3 and 4 only.

## Not-created data

Behaviours are **sourced, not authored**. The 54-behaviour misinformation set is the
`misinformation_disinformation` slice of the HarmBench test split, taken through the pinned safety-eval
checkout at commit `060cc903`, not a dataset this project built. `S1-06` would change that: its
reachable ceiling is 101 distinct behaviours against a frozen target of 150, and closing the gap by
authoring new behaviours makes the eval partly synthetic. That is the open question in `IN-006`.

## Gaps

1. **The label tree is not archived.** 515 MB on flushed, unbacked scratch, holding every rubric sheet
   an external rater filled — the files this table marks not recreatable. A flush loses the main
   decomposition's labels, all three `S1-3F` rater sheets, and the GPT out-of-sample sheet. Nothing here
   is regenerable from code.
2. **No expanded-evalset hash yet**, because `S1-06` is blocked on `IN-006`. That row is the Stage 2 gate.
