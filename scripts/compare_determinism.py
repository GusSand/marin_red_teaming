#!/usr/bin/env python3
"""Compare determinism runs at THREE levels, because token-exact equality alone misleads.

    python scripts/compare_determinism.py <label>=<rundir> [<label>=<rundir> ...]

Each rundir must hold all.json and metrics.json.

Levels, weakest claim to strongest:

  1. exact response hash   -- one changed token makes a whole completion unequal. This is the
                              harshest possible test and a low score here does NOT mean the
                              measurement moved.
  2. WildGuard labels      -- did the harmful/refusal classification change per item? This is
                              what the metric is actually built on.
  3. reported rate         -- the 54-item misinformation rate, in ITEM COUNTS not just percent,
                              because 42.59% vs 46.30% sounds like 3.7pp and is in fact 23/54
                              vs 25/54, i.e. two items.

A previous version of this analysis reported level 1 only and inferred a "~4pp noise floor" from
a single cross-GPU pair. Levels 2 and 3 exist so that cannot happen again.

Content-safe: hashes, labels and counts only; no completion text is printed.
"""
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

RESPONSE_KEYS = ("response", "output", "generation", "completion", "model_output")
ID_KEYS = ("BehaviorID", "behavior_id", "id", "prompt", "instruction")
HARM_KEYS = ("response_harmfulness", "harmfulness", "label")
REFUSAL_KEYS = ("response_refusal", "refusal")
MISINFO = "misinformation_disinformation"


def load_run(rundir):
    rd = Path(rundir)
    raw = json.load(open(rd / "all.json"))
    rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
    resp, harm, refusal = {}, {}, {}
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        rid = next((str(r[k]) for k in ID_KEYS if r.get(k) is not None), str(i))
        v = next((r[k] for k in RESPONSE_KEYS if r.get(k) is not None), None)
        if v is not None:
            resp[rid] = hashlib.sha256(str(v).encode()).hexdigest()
        h = next((r[k] for k in HARM_KEYS if r.get(k) is not None), None)
        if h is not None:
            harm[rid] = str(h)
        f = next((r[k] for k in REFUSAL_KEYS if r.get(k) is not None), None)
        if f is not None:
            refusal[rid] = str(f)
    rate = None
    mp = rd / "metrics.json"
    if mp.exists():
        m = json.load(open(mp))
        d = m.get("harmbench:default", next(iter(m.values())))
        cat = d.get("inverted_semantic_category_asr_lower", {})
        if MISINFO in cat:
            rate = 1.0 - cat[MISINFO]
    return {"resp": resp, "harm": harm, "refusal": refusal, "rate": rate,
            "prov": json.loads((rd / "provenance.json").read_text()) if (rd / "provenance.json").exists() else {}}


runs = {}
for a in sys.argv[1:]:
    label, path = a.split("=", 1)
    runs[label] = load_run(path)

# Hardware identity: a determinism claim is only meaningful within one GPU.
print("=== hardware / engine provenance ===")
hosts, uuids = set(), set()
for label, r in runs.items():
    p = r["prov"]
    host, uuid = p.get("hostname", "?"), p.get("gpu_uuid", "?")
    hosts.add(host); uuids.add(uuid)
    print(f"  {label:6} host={host:10} gpu={uuid[:24]:24} mp={p.get('vllm_v1_multiprocessing','?')} seed={p.get('sampling_seed_env','?')}")
if len(uuids - {"?"}) > 1:
    print("\n  WARNING: runs span MORE THAN ONE GPU. vLLM only claims reproducibility on identical")
    print("           hardware, so same-seed comparisons across these are not evidence of anything.")
else:
    print(f"\n  all runs on one GPU ({len(hosts)} host) -- comparison is valid")

def pairs_by_seed(label):
    return label.rstrip("abcdefghij")

for level, key, desc in (
    (1, "resp", "exact response hash (harshest test)"),
    (2, "harm", "WildGuard harmfulness label"),
    (2, "refusal", "WildGuard refusal label"),
):
    print(f"\n=== level {level}: {desc} ===")
    for a, b in combinations(runs, 2):
        ka, kb = runs[a][key], runs[b][key]
        common = set(ka) & set(kb)
        if not common:
            print(f"  {a:5} vs {b:5}  (no comparable field)")
            continue
        same = sum(1 for k in common if ka[k] == kb[k])
        tag = "same-seed" if pairs_by_seed(a) == pairs_by_seed(b) else "diff-seed"
        print(f"  {a:5} vs {b:5}  [{tag}]  identical {same:4d}/{len(common):4d} = {same/len(common):6.1%}")

print("\n=== level 3: reported misinformation rate (item counts) ===")
for label, r in runs.items():
    if r["rate"] is None:
        print(f"  {label:5}  rate unavailable")
    else:
        print(f"  {label:5}  {100*r['rate']:6.2f}%  = {r['rate']*54:4.0f}/54 items")
rates = [r["rate"] for r in runs.values() if r["rate"] is not None]
if len(rates) > 1:
    span_items = (max(rates) - min(rates)) * 54
    print(f"\n  spread across all runs: {100*(max(rates)-min(rates)):.2f}pp = {span_items:.0f} items")
    print("  NB: on a 54-item denominator one item is 1.85pp. Do not read a percentage-point")
    print("      spread as an effect size without converting it to items first.")
