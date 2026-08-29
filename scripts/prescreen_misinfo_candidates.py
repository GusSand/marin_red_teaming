#!/usr/bin/env python3
"""Step 6 pre-screen: count misinformation-like prompts in candidate sources by keyword (CPU, seconds).
A keyword screen is a RECALL net only; the frozen set is confirmed by the selected judge + hand check.
Writes counts and candidate ids (no prompt text) to --out.

Usage: prescreen_misinfo_candidates.py --se <safety-eval dir> --out <json>
"""
import argparse, csv, json, re
from pathlib import Path
KW = re.compile(r"\b(misinformation|disinformation|fake news|false claim|conspiracy|hoax|propaganda|debunk|vaccine|climate|election|fraudulent article|fabricat|rumou?r|deny|denial|flat earth|chemtrail|5g|microchip|stolen election|deep ?fake|pseudoscien)\w*", re.I)
ART = re.compile(r"\b(article|blog|post|essay|op-ed|news|story|tweet|thread|report|press release|pamphlet|speech)\b", re.I)
ap = argparse.ArgumentParser(); ap.add_argument("--se", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
G = Path(a.se) / "evaluation" / "tasks" / "generation"; res = {}
sr = list(csv.DictReader(open(G / "strongreject" / "strong_reject.csv")))
srd = {r["forbidden_prompt"] for r in sr if r["category"] == "Disinformation and deception"}
res["strongreject_disinfo"] = {"unique": len(srd), "kw_hits": sum(1 for p in srd if KW.search(p)), "kw_and_artifact": sum(1 for p in srd if KW.search(p) and ART.search(p))}
wj = [json.loads(l) for l in open(G / "wildjailbreak" / "harmful.jsonl")]
van = [r["vanilla"] for r in wj]
hits = [i for i, p in enumerate(van) if KW.search(p)]
res["wildjailbreak_vanilla_harmful"] = {"total": len(van), "kw_hits": len(hits), "kw_and_artifact": sum(1 for i in hits if ART.search(van[i])), "hit_ids": hits}
tl = [json.loads(l) for l in open(G / "trustllm_jailbreaktrigger" / "trustllm_jailbreaktrigger_400.jsonl")]
res["trustllm_jbt"] = {"total": len(tl), "kw_hits": sum(1 for r in tl if KW.search(r["prompt"]))}
json.dump(res, open(a.out, "w"), indent=1)
print({k: {kk: vv for kk, vv in v.items() if kk != "hit_ids"} for k, v in res.items()})
