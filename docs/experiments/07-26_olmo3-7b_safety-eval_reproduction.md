# Experiment: reproduce Olmo 3 7B safety numbers (Instruct + Think)

Created 2026-07-26, before any compute. Pre-registered.

## Research question / hypothesis
Can we reproduce, within tolerance, the published safety-benchmark values for
Olmo 3 7B Instruct (arXiv:2512.13961v2 Table 53) and Think (Table 52) using
`allenai/safety-eval` @ 060cc903, and where does reproduction diverge?

## Setup
- Models: `allenai/Olmo-3-7B-Instruct`, `allenai/Olmo-3-7B-Think` (revisions pinned at Gate 1).
- Harness: `safety-eval` @ 060cc903, vLLM backend, one A100 80GB.
- Sampling: temperature 0.7, top-p 0.95 (report A.8.2). Seeds fixed & recorded per run.
- Judges/classifiers per row: see `repro-olmo3-safety/config/rows.json`.
- Targets: `repro-olmo3-safety/targets.json` (human-verified at Gate 0 STOP).

## Success criteria (pre-registered)
- **Gate 2** (HarmBench, Instruct Final, single run): |produced − 94.9| ≤ 3.0 pp. (DECISIONS.md)
- **Gate 3** (HarmBench, XSTest, DAN, WildGuard-Test): report mean ± spread over 3 runs;
  "clean" if each mean within ≤ 3.0 pp of the published Final value.
- **Gates 4–5**: no pass/fail threshold on convention/held-out rows — the deliverable is
  the per-row delta plus an explanation of every divergence. A non-reproducing row is a
  result, not a failure, if its cause is documented.
- Determinism: vLLM decoding is not bit-exact; compare within tolerance, never exact equality.

## Results
RAN 2026-07-26/28. Harness fully validated against both published Olmo-3 tables.

- Gate 0: DONE. Targets human-verified against the PDF.
- Olmo-3-7B-Instruct (Table 53): 13/13 rows PASS within the pre-registered ±3pp.
- Olmo-3-7B-Think (Table 52, thinker_eval=answers, 32k tokens): 11/13 rows PASS, max |Δ| = 0.82pp.
  StrongReject-Think and Toxigen-Think NOT RUN — reasoning over 2294 and 14000 prompts is impractical
  (~days); gs157 chose to skip. Toxigen is non-discriminating at 100.0 in any case.
- WMDP-Think independently recomputed as fraction-incorrect (41.83 / 44.28 / 42.64) = reported. MATCH.

Per-row deltas: repro-olmo3-safety/report/deltas.md. Write-up: SUMMARY.md Parts 3 and 5.

## Verified / Unverified
- VERIFIED. Each headline recomputed from raw labels by an independent subagent on a separate code path.
- Reproducing the published numbers on this harness is the precondition that makes the Marin numbers
  (SUMMARY Parts 2 and 4) checkable rather than self-reported.

## Links
- Targets: `repro-olmo3-safety/targets.json`
- Config: `repro-olmo3-safety/config/rows.json`
- Decisions: `repro-olmo3-safety/DECISIONS.md`
- Report: `outputs/olmo3.pdf`
