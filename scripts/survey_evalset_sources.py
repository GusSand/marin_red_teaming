#!/usr/bin/env python3
"""S1-06: census of reachable misinformation behaviours across candidate sources.

Counts distinct behaviours available from HarmBench (all splits), JailbreakBench Disinformation,
AdvBench (keyword+artefact net) and WildJailbreak, with exact normalized-text dedupe across sources.
The number it prints is a CEILING: semantic near-duplicates survive it and AdvBench items have not been
through the frozen inclusion rule.

Run on the Torch login node in the safety-eval venv (needs `datasets` and network):
  HF_HOME=/scratch/gs157/.huggingface .venv-safety-eval/bin/python survey_evalset_sources.py

Result 2026-09-05: 101 distinct against a frozen target of 150. See
docs/experiments/08-29_misinfo-evalset_selection.md.
"""
import csv, io, json, re, urllib.request
from collections import Counter
KW = re.compile(r"\b(misinformation|disinformation|fake news|false claim|conspiracy|hoax|propaganda|debunk|vaccine|climate|election|fraudulent article|fabricat|rumou?r|deny|denial|flat earth|chemtrail|5g|microchip|stolen election|deep ?fake|pseudoscien)\w*", re.I)
ART = re.compile(r"\b(article|blog|post|essay|op-ed|news|story|tweet|thread|report|press release|pamphlet|speech|script)\b", re.I)
norm = lambda t: re.sub(r"\W+", " ", t.lower()).strip()

def get(u): return urllib.request.urlopen(u, timeout=30).read().decode()

hb = list(csv.DictReader(io.StringIO(get(
  "https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv"))))
hb_mis = [r for r in hb if r["SemanticCategory"] == "misinformation_disinformation"
          and r["FunctionalCategory"] in ("standard", "contextual")]

from datasets import load_dataset
jb = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors", split="harmful")
jb_dis = [r for r in jb if r["Category"] == "Disinformation"]

adv = list(csv.DictReader(io.StringIO(get(
  "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv"))))
adv_kw = [r for r in adv if KW.search(r["goal"]) and ART.search(r["goal"])]

seen, tally = {}, Counter()
def add(src, text, ident):
    n = norm(text)
    if n in seen:
        tally[f"{src}_dup_of_{seen[n][0]}"] += 1
        return False
    seen[n] = (src, ident); tally[f"{src}_new"] += 1
    return True

for r in hb_mis: add("harmbench", r["Behavior"], r["BehaviorID"])
for r in jb_dis: add("jailbreakbench", r["Goal"], f"jbb{r['Index']}")
for r in adv_kw: add("advbench", r["goal"], "adv")

res = {
 "harmbench_all_misinfo": len(hb_mis),
 "harmbench_functional": dict(Counter(r["FunctionalCategory"] for r in hb_mis)),
 "jailbreakbench_disinformation": len(jb_dis),
 "advbench_keyword_and_artifact": len(adv_kw),
 "advbench_total": len(adv),
 "after_exact_dedupe": dict(tally),
 "DISTINCT_TOTAL": len(seen),
 "target": 150,
 "shortfall": 150 - len(seen),
 "note": "exact normalized-text dedupe only; semantic near-duplicates would reduce this further, so this is a CEILING",
}
print(json.dumps(res, indent=1))
import csv, io, json, re, urllib.request
from collections import Counter
KW = re.compile(r"\b(misinformation|disinformation|fake news|false claim|conspiracy|hoax|propaganda|debunk|vaccine|climate|election|fraudulent article|fabricat|rumou?r|deny|denial|flat earth|chemtrail|5g|microchip|stolen election|deep ?fake|pseudoscien)\w*", re.I)
ART = re.compile(r"\b(article|blog|post|essay|op-ed|news|story|tweet|thread|report|press release|pamphlet|speech|script)\b", re.I)
norm = lambda t: re.sub(r"\W+", " ", t.lower()).strip()

def get(u): return urllib.request.urlopen(u, timeout=30).read().decode()

hb = list(csv.DictReader(io.StringIO(get(
  "https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/data/behavior_datasets/harmbench_behaviors_text_all.csv"))))
hb_mis = [r for r in hb if r["SemanticCategory"] == "misinformation_disinformation"
          and r["FunctionalCategory"] in ("standard", "contextual")]

from datasets import load_dataset
jb = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors", split="harmful")
jb_dis = [r for r in jb if r["Category"] == "Disinformation"]

adv = list(csv.DictReader(io.StringIO(get(
  "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv"))))
adv_kw = [r for r in adv if KW.search(r["goal"]) and ART.search(r["goal"])]

seen, tally = {}, Counter()
def add(src, text, ident):
    n = norm(text)
    if n in seen:
        tally[f"{src}_dup_of_{seen[n][0]}"] += 1
        return False
    seen[n] = (src, ident); tally[f"{src}_new"] += 1
    return True

for r in hb_mis: add("harmbench", r["Behavior"], r["BehaviorID"])
for r in jb_dis: add("jailbreakbench", r["Goal"], f"jbb{r['Index']}")
for r in adv_kw: add("advbench", r["goal"], "adv")

res = {
 "harmbench_all_misinfo": len(hb_mis),
 "harmbench_functional": dict(Counter(r["FunctionalCategory"] for r in hb_mis)),
 "jailbreakbench_disinformation": len(jb_dis),
 "advbench_keyword_and_artifact": len(adv_kw),
 "advbench_total": len(adv),
 "after_exact_dedupe": dict(tally),
 "DISTINCT_TOTAL": len(seen),
 "target": 150,
 "shortfall": 150 - len(seen),
 "note": "exact normalized-text dedupe only; semantic near-duplicates would reduce this further, so this is a CEILING",
}
print(json.dumps(res, indent=1))
