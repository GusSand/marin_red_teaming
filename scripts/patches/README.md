# scripts/patches/

Patches to the vendored (gitignored) `repro-olmo3-safety/safety-eval` checkout.
safety-eval is pinned at SHA `060cc903d64703214c549b5c3a30ea8ceef2e588` and not tracked
by the main repo, so any modification to it is captured here as a re-appliable diff.

## seed_fix_generation_utils.patch (2026-07-29, gs157-approved INBOX seed-method → b)
Injects a real per-run vLLM sampling seed from env `SAFETYEVAL_SAMPLING_SEED` into
`SamplingParams` (additive; no metric-definition change). Without it, `run_row.sh`'s
`PYTHONHASHSEED` did NOT control vLLM sampling, so the 3 seeds collapsed to identical
outputs where generation is stable (understated CIs). `run_row.sh` now exports the env var.
Apply from the safety-eval root:  `git apply /home/paperspace/marin/scripts/patches/seed_fix_generation_utils.patch`
Validated cross-process on Llama-3.2-1B: same seed reproduces, different seeds diverge.
