#!/usr/bin/env python
"""Gate 6: build report/deltas.md from runs/*/metrics.json vs targets.json.
Produced = mean over the (up to 3) seed runs; spread = min-max. Delta = produced - published.
A row with no run dir / no metrics.json is reported NOT RUN (never a guessed value).
Metrics in metrics.json are fractions (0-1); published targets are on a 0-100 scale, so we x100.

Usage: python scripts/make_delta_report.py            # writes report/deltas.md
"""
import json, os, glob, statistics as st

ROOT = "/home/paperspace/marin/repro-olmo3-safety"
TARGETS = json.load(open(f"{ROOT}/targets.json"))

# report-row -> (targets.json row key, metrics.json headline field). BBQ expands to 3 rows.
# instruct uses default configs; think uses *_reasoning_answer. run dirs are discovered by prefix+slug.
ROWSPEC = [
    ("DoAnythingNow",              "DoAnythingNow",              "inverted_macro_asr"),
    ("HarmBench",                  "HarmBench",                  "inverted_micro_asr_lower"),
    ("TrustLLM-JailbreakTrigger",  "TrustLLM-JailbreakTrigger",  "inverted_macro_asr"),
    ("WildJailbreak-Test_Harmful", "WildJailbreak-Test_Harmful", "inverted_macro_asr"),
    ("WildJailbreak-Test_Benign",  "WildJailbreak-Test_Benign",  "macro_asr"),
    ("WildGuard-Test",             "WildGuard-Test",             "inverted_micro_harm_lower"),
    ("XSTest",                     "XSTest",                     "overall_accuracy"),
    ("BBQ_Accuracy",               "BBQ_Accuracy",               "accuracy"),
    ("BBQ_Bias-Ambig",             "BBQ_Bias-Ambig",             "bias_ambig"),
    ("BBQ_Bias-Disambig",          "BBQ_Bias-Disambig",          "bias_disambig"),
    ("StrongReject",               "StrongReject",               "inverted_asr"),
    ("Toxigen",                    "Toxigen",                    "safe_overall"),
    ("WMDP",                       "WMDP",                       "inverted_accuracy"),
]
# maps report row -> the run-dir slug used by run_suite.sh
SLUG = {
    "DoAnythingNow": {"instruct": "dan", "think": "do-anything-now-wildguard-reasoning-answer"},
    "HarmBench": {"instruct": "harmbench", "think": "harmbench-wildguard-reasoning-answer"},
    "TrustLLM-JailbreakTrigger": {"instruct": "trustllm-jailbreaktrigger", "think": "trustllm-jailbreaktrigger-wildguard-reasoning-answer"},
    "WildJailbreak-Test_Harmful": {"instruct": "wildjailbreak-harmful", "think": "wildjailbreak-harmful-wildguard-reasoning-answer"},
    "WildJailbreak-Test_Benign": {"instruct": "wildjailbreak-benign", "think": "wildjailbreak-benign-wildguard-reasoning-answer"},
    "WildGuard-Test": {"instruct": "wildguardtest", "think": "wildguardtest-wildguard-reasoning-answer"},
    "XSTest": {"instruct": "xstest", "think": "xstest-wildguard-reasoning-answer"},
    "BBQ_Accuracy": {"instruct": "bbq", "think": "bbq-default-reasoning-answer"},
    "BBQ_Bias-Ambig": {"instruct": "bbq", "think": "bbq-default-reasoning-answer"},
    "BBQ_Bias-Disambig": {"instruct": "bbq", "think": "bbq-default-reasoning-answer"},
    "StrongReject": {"instruct": "strongreject-logprobs", "think": "strongreject-logprobs-reasoning-answer"},
    "Toxigen": {"instruct": "toxigen", "think": "toxigen-default-reasoning-answer"},
    "WMDP": {"instruct": "wmdp", "think": "wmdp-default-reasoning-answer"},
}
TOL = 3.0

def runs_for(prefix, slug):
    return sorted(glob.glob(f"{ROOT}/runs/{prefix}-{slug}-r*"))

def val_from(run, field):
    mp = f"{run}/metrics.json"
    if not os.path.exists(mp):
        return None
    m = json.load(open(mp)); k = list(m.keys())[0]
    v = m[k].get(field)
    return v * 100 if v is not None else None

def summarize(prefix, kind, targets_block):
    lines = []
    for report_row, tkey, field in ROWSPEC:
        slug = SLUG[report_row][kind]
        vals = [v for r in runs_for(prefix, slug) if (v := val_from(r, field)) is not None]
        pub = targets_block["rows"].get(tkey, {}).get("Final") if False else targets_block.get(tkey)
        pub = targets_block.get(tkey)
        n = len(vals)
        if n == 0:
            lines.append((report_row, pub, "NOT RUN", "", "", "NOT RUN"))
            continue
        mean = sum(vals) / n
        spread = f"{min(vals):.2f}-{max(vals):.2f}" if n > 1 else f"{vals[0]:.2f}"
        delta = mean - pub if pub is not None else None
        status = "PASS" if (delta is not None and abs(delta) <= TOL) else ("FAIL" if delta is not None else "?")
        lines.append((report_row, pub, f"{mean:.2f}", spread, f"{delta:+.2f}" if delta is not None else "", f"{status} (n={n})"))
    return lines

def block_targets(model_key):
    b = TARGETS[model_key]["rows"]
    return {k: v["Final"] for k, v in b.items()}

def render(title, lines):
    out = [f"### {title}", "", "| Row | Published | Produced (mean) | Spread | Δ pp | Status |", "|---|---|---|---|---|---|"]
    for row, pub, prod, spread, delta, status in lines:
        out.append(f"| {row} | {pub} | {prod} | {spread} | {delta} | {status} |")
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    md = ["# Olmo 3 7B safety reproduction — delta report", "",
          "Produced = mean over 3 seed runs (0-2). Spread = min-max. Δ = produced - published.",
          f"Tolerance {TOL}pp. safety-eval @060cc903, temp0.7/top_p0.95. Metrics x100 from fractions.",
          "Targets human-verified (Gate 0). Rows with no metrics.json = NOT RUN.", ""]
    md.append(render("Olmo 3 7B Instruct (Table 53, Final Instruct)",
                     summarize("2026-07-26-instruct", "instruct", block_targets("olmo3_7b_instruct"))))
    md.append(render("Olmo 3 7B Think (Table 52, Final Think)",
                     summarize("2026-07-26-think", "think", block_targets("olmo3_7b_think"))))
    os.makedirs(f"{ROOT}/report", exist_ok=True)
    open(f"{ROOT}/report/deltas.md", "w").write("\n".join(md))
    print("wrote", f"{ROOT}/report/deltas.md")
    print("\n".join(md))
