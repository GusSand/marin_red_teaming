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
- Gate 0: DONE (extraction). Pending human verification of targets.
- Gates 1–6: NOT RUN.

## Verified / Unverified
- All numeric results UNVERIFIED until produced from a real run + reproduced from raw data.

## Links
- Targets: `repro-olmo3-safety/targets.json`
- Config: `repro-olmo3-safety/config/rows.json`
- Decisions: `repro-olmo3-safety/DECISIONS.md`
- Report: `outputs/olmo3.pdf`
