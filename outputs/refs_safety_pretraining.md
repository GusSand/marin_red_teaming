# References — pretraining-data safety / tamper-resistance (for the Marin proposal)

- **Deep Ignorance: Filtering Pretraining Data Builds Tamper-Resistant Safeguards into Open-Weight LLMs.**
  arXiv:2508.06601. Pretraining-data filtering of dual-use/biothreat content; 6.9B models from scratch;
  resistance to 10k adversarial fine-tuning steps (300M biothreat tokens); >1 order of magnitude over
  post-training baselines; residual limitation = in-context (search/RAG) harmful-info use.
  **ICLR 2026** (peer-reviewed); 50 citations as of 2026-07-27; open models/data/code on HF + GitHub.
  Standing + counterpoints (Phantom Transfer 2602.04899; biorisk-eval 2510.27629): see
  outputs/deep_ignorance_reception.md — established but explicitly defence-in-depth, not settled.
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
