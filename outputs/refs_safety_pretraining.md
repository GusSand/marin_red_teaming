# References — pretraining-data safety / tamper-resistance (for the Marin proposal)

- **Deep Ignorance: Filtering Pretraining Data Builds Tamper-Resistant Safeguards into Open-Weight LLMs.**
  arXiv:2508.06601. Pretraining-data filtering of dual-use/biothreat content; 6.9B models from scratch;
  resistance to 10k adversarial fine-tuning steps (300M biothreat tokens); >1 order of magnitude over
  post-training baselines; residual limitation = in-context (search/RAG) harmful-info use.
  **ICLR 2026** (peer-reviewed); 50 citations as of 2026-07-27; open models/data/code on HF + GitHub.
  Standing + counterpoints (Phantom Transfer 2602.04899; biorisk-eval 2510.27629): see
  outputs/deep_ignorance_reception.md — established but explicitly defence-in-depth, not settled.
- **Modular Pretraining Enables Access Control (GRAM — Gradient-Routed Auxiliary Modules).**
  Roland, Cubuktepe, Martinez, Servaes, Pepper, Vaiana, de Lucena, Rosenblatt (AE Studio); Foote (Independent);
  Anil, Cloud (Anthropic). **ICML 2026 Spotlight.** arXiv:2607.08077 · OpenReview yIubI9l3IT ·
  code https://github.com/agencyenterprise/modular-pretraining · data https://huggingface.co/datasets/AE-data/dual-use-papers ·
  blogs https://ae.studio/research/modular-pretraining-access-control + https://www.anthropic.com/research/off-switch-dual-use .
  Pretraining-TIME access control: route gradients from dual-use data into small removable auxiliary MLP modules
  so ONE training run yields many capability profiles — delete a module at inference to drop that capability while
  keeping general performance. Matches data-filtering on capability removal, BEATS it under sparse/partial labels,
  and composes across modules better than LoRA. Scales 50M→5B (capability gap widens with scale). The
  "train it but quarantine it" complement to Deep Ignorance's "don't train on it at all."
  **Caveats for us:** (1) NO LICENSE file on the repo → defaults to all-rights-reserved; we can read/learn but
  cannot redistribute adapted code without permission — check with authors or reimplement gradient routing from
  the paper. (2) No checkpoints released (`*.pth`/`*.safetensors` git-ignored) → train from scratch. (3) Repo
  ALREADY ships an adversarial-finetuning "elicited-forget" metric + unlearning baselines (RMU/MaxEnt/ASCENT) +
  DEMix/LoRA comparisons; authors call tamper-resistance preliminary and note capabilities can be elicited back.
  Relevance: the concrete pretraining DEFENSE our report keeps pointing at (moves us from measuring the problem
  to building+breaking a fix); candidate "phase after the Safety Gap Toolkit." Follow-up: BACKLOG "evaluate GRAM".
- **The WMDP Benchmark: Measuring and Reducing Malicious Use with Unlearning.** Li et al., ICML 2024.
  arXiv:2403.03218. 3,668 MC proxy questions (bio/chem/cyber). Introduces RMU (Representation Misdirection
  for Unlearning): perturbs activations on hazardous data, preserves general capability; near-random WMDP
  after unlearning. https://proceedings.mlr.press/v235/li24bc.html
- **Tamper-Resistant Safeguards for Open-Weight LLMs (TAR).** arXiv:2408.00761. Safeguards resisting
  hundreds of FT steps across 28 adversaries; later shown susceptible to abliteration / init variance
  (the arms race). https://openreview.net/forum?id=4FIjRodbW6
- **Safety Alignment Should Be Made More Than Just a Few Tokens Deep.** Qi et al., ICLR 2025 (Outstanding
  Paper). arXiv:2406.05946. "Shallow safety alignment": alignment mostly changes the first few tokens;
  explains susceptibility to prefilling/decoding/fine-tuning attacks; proposes deeper-alignment regularizer.
- **Abliteration / refusal-direction removal** — gradient-free attack removing a refusal direction from the
  residual stream (context: tamper-resistance is beaten by activation-editing, not just fine-tuning).
- **Token Buncher: Shielding LLMs from Harmful RL Fine-Tuning.** arXiv:2508.20697 (adjacent defense).
- **Marin 8B Retro report** — pretraining phases & data mixture (Kestrel/Ocelot/Jellyfish/Phoenix/
  Starling/Deeper-Starling); Nemotron-CC introduced at Phoenix. https://marin.readthedocs.io/en/latest/reports/marin-8b-retro/
- **Nemotron-CC: Transforming Common Crawl into a Refined Long-Horizon Pretraining Dataset.** arXiv:2412.02595
  (the web-scale corpus introduced at Marin's Phoenix phase).

Our own inputs (on-disk, verified): repro-olmo3-safety/report/harmbench_gap_analysis.md (red-team gap map),
report/marin_vs_olmo.md (base vs instruct vs Olmo), docs/research_journal.md.

## Safety-gap / tamper-resistance toolkit (added 2026-07-29)
- **The Safety Gap Toolkit: Evaluating Hidden Dangers of Open-Source Models.** Dombrowski, Bowen, Gleave,
  Cundy, 2025. arXiv:2507.11544 · code https://github.com/AlignmentResearch/safety-gap . Defines the
  **"safety gap"** = difference in *dangerous capability* between a model with intact safeguards and one
  stripped of them; KEY CLAIM: the gap **widens with model scale** (tested Llama-3 + Qwen-2.5, 0.5B–405B).
  Toolkit (Hydra + PEFT/vLLM/accelerate): attacks = SFT + refusal-ablation; evals = MC-accuracy +
  refusal (`strong_reject` pkg) + quality (Anthropic API). Directly generalizes our tamper-resistance study
  (SUMMARY Part 10) from refusal-collapse to capability-uplift-vs-scale. NO explicit license on repo — check
  before redistributing adapted code. Follow-up task: BACKLOG "adapt the Safety Gap Toolkit".
- **Refusal in LLMs Is Mediated by a Single Direction** (refusal ablation / "abliteration"). arXiv:2410.03415.
  White-box, gradient-free safeguard removal (ablate the refusal direction from the residual stream) used by
  the Safety Gap toolkit — a second, cheaper removal path than fine-tuning that we don't currently implement.
- **TamperBench** — arXiv:2602.06911. Standardizes tamper-resistance comparison across ~21 open-weight models
  (held-out attack-success after safeguard removal). The community benchmark our tamper study (SUMMARY Part 10)
  and the safety-gap follow-up are instances of; cited in the companion blog's measurement section.
- **Model tampering attacks predict held-out input-space attack success** — instrument (cited in the blog)
  showing that fine-tuning/latent-space tampering forecasts a model's worst-case jailbreak susceptibility better
  than static prompt benchmarks. Motivates measuring the *stripped* model, not the aligned checkpoint.
- **Companion blog — *Red-Teaming Language Models*** (gs157, https://gussand.github.io/posts/2026/07/red-teaming-language-models/).
  Conceptual/landscape framing for this whole project: threat models & the "access ladder"; jailbreaks vs prompt
  injection; the measurement problem (judge error rates, incomparable estimands, non-harmful benchmark prompts);
  "open weights changes the order" (red-teaming aligned checkpoints is a config no adversary uses). Our report is
  the concrete empirical instance; the blog is the theory. Bidirectional companion.
