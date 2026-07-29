#!/usr/bin/env python
"""Regenerate the tamper-collapse figure (SUMMARY Part 10 / README result 3) from the verified
metrics.json. ASR = 100*(1 - harmbench:default.inverted_micro_asr_lower). Outputs PNG + SVG."""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

STEPS = [0, 5, 10, 20, 40, 80]
RUN = "repro-olmo3-safety/runs/2026-07-29-tamper-{m}-step{s}-harmbench/metrics.json"
def asr(m):
    out = []
    for s in STEPS:
        d = json.load(open(RUN.format(m=m, s=s)))
        inv = d["harmbench:default"]["inverted_micro_asr_lower"]
        out.append(100.0 * (1.0 - inv))
    return out

olmo = asr("olmo7b"); marin = asr("marin8b")
print("olmo :", [round(x,1) for x in olmo])
print("marin:", [round(x,1) for x in marin])

plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(8, 5), dpi=160)
ax.plot(STEPS, marin, "-o", color="#c1440e", lw=2.5, ms=7, label="Marin-8B-Instruct")
ax.plot(STEPS, olmo, "-o", color="#2166ac", lw=2.5, ms=7, label="Olmo-3-7B-Instruct")
ax.axhspan(90, 100, color="#d62728", alpha=0.06)
ax.annotate("~99% by step 10", xy=(10, 95.6), xytext=(26, 78),
            arrowprops=dict(arrowstyle="->", color="#555"), color="#333", fontsize=11)
ax.annotate("start: 5.6% / 15.6%", xy=(0, 15.6), xytext=(6, 33),
            arrowprops=dict(arrowstyle="->", color="#555"), color="#333", fontsize=10)
ax.set_xlabel("LoRA fine-tuning steps")
ax.set_ylabel("Attack-success rate (%)   ↑ = less safe")
ax.set_title("Safety collapses under a small fine-tuning attack", fontweight="bold", pad=12)
ax.set_ylim(0, 103); ax.set_xlim(-2, 82)
ax.set_xticks(STEPS)
ax.grid(True, alpha=0.25)
ax.legend(loc="center right", frameon=False)
fig.text(0.5, -0.02,
         "HarmBench attack-success under a LoRA affirmative-prefix attack (~100 public AdvBench examples). "
         "Higher = model complied with more harmful requests.\nNeither open model resists: both go from near-"
         "safe to ~99% within 10 steps. Verified — recomputed from raw labels; labels re-checked by re-running WildGuard.",
         ha="center", va="top", fontsize=8.2, color="#555", wrap=True)
fig.tight_layout()
fig.savefig("repro-olmo3-safety/report/figures/tamper_collapse.png", bbox_inches="tight", facecolor="white")
fig.savefig("repro-olmo3-safety/report/figures/tamper_collapse.svg", bbox_inches="tight", facecolor="white")
print("wrote repro-olmo3-safety/report/figures/tamper_collapse.{png,svg}")
