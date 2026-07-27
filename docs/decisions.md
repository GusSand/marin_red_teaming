# Decisions (append-only, one line per settled choice)

2026-07-26 · pinned safety-eval @ 060cc903d64703214c549b5c3a30ea8ceef2e588 for Olmo3 repro → experiments/07-26_olmo3-7b_safety-eval_reproduction.md
2026-07-26 · target source = arXiv:2512.13961v2 Tables 52/53 (7B Think/Instruct) → repro-olmo3-safety/targets.json
2026-07-26 · use repo default.yaml classifiers as-is (all WildGuard in this commit); no OpenAI key needed; HarmBench & TrustLLM already match report → repro-olmo3-safety/DECISIONS.md
2026-07-26 · Instruct uses plain default configs; Think uses *_wildguard_reasoning_answer.yaml (thinker_eval=answers) → repro-olmo3-safety/config/rows.json
2026-07-26 · StrongReject classifier = StrongRejectLogProbs (logprobs.yaml), not StrongRejectClassifier → repro-olmo3-safety/DECISIONS.md
2026-07-26 · Gate 2 tolerance pre-registered: |produced − 94.9| ≤ 3.0 pp (single run) → repro-olmo3-safety/DECISIONS.md
