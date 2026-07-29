#!/usr/bin/env python
"""Regenerate the tamper-collapse figure (SUMMARY Part 10 / README) from the verified
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
print("olmo :", [round(x, 1) for x in olmo])
print("marin:", [round(x, 1) for x in marin])

plt.rcParams.update({"font.size": 15, "font.family": "DejaVu Sans"})
fig, ax = plt.subplots(figsize=(9.5, 6.4), dpi=170)
ax.plot(STEPS, marin, "-o", color="#c1440e", lw=3, ms=9, label="Marin-8B-Instruct")
ax.plot(STEPS, olmo, "-o", color="#2166ac", lw=3, ms=9, label="Olmo-3-7B-Instruct")
ax.axhspan(90, 100, color="#d62728", alpha=0.06)
ax.annotate("~99% by step 10", xy=(10, 95.6), xytext=(24, 74),
            arrowprops=dict(arrowstyle="->", color="#555"), color="#333", fontsize=16)
ax.annotate("start: 5.6% / 15.6%", xy=(0, 15.6), xytext=(6, 34),
            arrowprops=dict(arrowstyle="->", color="#555"), color="#333", fontsize=15)
ax.set_xlabel("LoRA fine-tuning steps", fontsize=17)
ax.set_ylabel("Attack-success rate (%)   ↑ = less safe", fontsize=17)
ax.set_title("Safety collapses under a small fine-tuning attack", fontweight="bold", fontsize=20, pad=14)
ax.set_ylim(0, 103); ax.set_xlim(-2, 82)
ax.set_xticks(STEPS)
ax.tick_params(labelsize=15)
ax.grid(True, alpha=0.25)
ax.legend(loc="center right", frameon=False, fontsize=17)
fig.text(0.5, -0.01,
         "HarmBench attack-success vs LoRA fine-tuning steps. Higher = more harmful compliance.\n"
         "Neither model resists. Verified from raw labels; WildGuard labels re-checked by re-running it.",
         ha="center", va="top", fontsize=14, color="#444")
fig.tight_layout()
fig.savefig("repro-olmo3-safety/report/figures/tamper_collapse.png", bbox_inches="tight", facecolor="white")
fig.savefig("repro-olmo3-safety/report/figures/tamper_collapse.svg", bbox_inches="tight", facecolor="white")
print("wrote repro-olmo3-safety/report/figures/tamper_collapse.{png,svg}")
