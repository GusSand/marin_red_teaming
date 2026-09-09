#!/usr/bin/env python3
import json, re, random
from collections import Counter, defaultdict
import numpy as np
DATA = "/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad/twins_v2"
twins = {}
for line in open(f"{DATA}/twins.jsonl"):
    if line.strip():
        r = json.loads(line); twins[r["twin_id"]] = r
resps = [json.loads(l) for l in open(f"{DATA}/responses.jsonl") if l.strip()]
def trunc(t):
    i = t.find("\nUser:"); return t[:i] if i != -1 else t

print("== 1. does 'Requirements:' appear in ANY twin prompt? ==")
n = sum(1 for t in twins.values() if "Requirements:" in t["instruction"])
print(f"  twins whose instruction contains literal 'Requirements:': {n}/{len(twins)}")
print(f"  twins whose instruction contains 'Please follow all four': "
      f"{sum(1 for t in twins.values() if 'Please follow all four' in t['instruction'])}/{len(twins)}")
print(f"  twins whose instruction contains 'requirement' (any case): "
      f"{sum(1 for t in twins.values() if 'requirement' in t['instruction'].lower())}/{len(twins)}")
# any response echoing the bullet block?
ech = sum(1 for r in resps if "Please follow all four" in trunc(r["response"]))
ech2 = Counter()
for r in resps:
    b = trunc(r["response"])
    if "Please follow all four" in b or "- Begin with a title line" in b:
        ech2[r["checkpoint"]] += 1
print(f"  responses echoing 'Please follow all four': {ech}")
print(f"  responses echoing bullet block (either marker) by checkpoint: {dict(ech2)}")

print("\n== 2. truncation ==")
for cp in ["phoenix", "starling"]:
    sub = [r for r in resps if r["checkpoint"] == cp]
    tr = [r for r in sub if "\nUser:" in r["response"]]
    lost = [len(r["response"].split()) - len(trunc(r["response"]).split()) for r in tr]
    print(f"  {cp}: truncated {len(tr)}/{len(sub)} = {100*len(tr)/len(sub):.2f}%; "
          f"median tokens removed {np.median(lost) if lost else 0:.0f}")
    # how many hit max tokens (no User: turn, very long)
    long = [r for r in sub if "\nUser:" not in r["response"]]
    print(f"     no 'User:' turn at all: {len(long)}; their median word count "
          f"{np.median([len(r['response'].split()) for r in long]) if long else 0:.0f}")

print("\n== 3. title diagnostics: preamble hypothesis ==")
TITLE_RE = re.compile(r"^(Title:|#)\s*\S")
for cp in ["phoenix", "starling"]:
    sub = [r for r in resps if r["checkpoint"] == cp]
    first_ok = anywhere = neither = 0
    kind = Counter()
    for r in sub:
        b = trunc(r["response"])
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        f = lines[0] if lines else ""
        if TITLE_RE.match(f):
            first_ok += 1
            kind["Title:" if f.startswith("Title:") else "#"] += 1
        elif any(TITLE_RE.match(l) for l in lines):
            anywhere += 1
        else:
            neither += 1
    print(f"  {cp}: title on first line={first_ok} (forms {dict(kind)}), "
          f"title present but NOT first={anywhere}, no title anywhere={neither}")

print("\n== 4. audience: near-miss analysis ==")
for cp in ["phoenix", "starling"]:
    sub = [r for r in resps if r["checkpoint"] == cp]
    exact = partial = none = 0
    for r in sub:
        b = trunc(r["response"]).lower()
        aud = twins[r["twin_id"]]["audience"].lower()
        if aud in b:
            exact += 1
        else:
            head = aud.split()[-1]  # last word e.g. 'apprentices'
            partial += 1 if head in b else 0
            none += 0 if head in b else 1
    print(f"  {cp}: exact phrase={exact}, head-noun only={partial}, neither={none}")

print("\n== 5. length tie: how coincidental? ==")
# per-seed breakdown
for cp in ["phoenix", "starling"]:
    per = Counter()
    for r in resps:
        if r["checkpoint"] != cp: continue
        b = trunc(r["response"]); t = twins[r["twin_id"]]
        if t["word_lo"] <= len(b.split()) <= t["word_hi"]:
            per[r["seed"]] += 1
    print(f"  {cp} length passes by seed: {dict(sorted(per.items()))} total {sum(per.values())}")
# per-twin cross-tab of counts 0-3
ct = Counter()
for t in twins:
    a = sum(1 for r in resps if r["twin_id"] == t and r["checkpoint"] == "phoenix"
            and twins[t]["word_lo"] <= len(trunc(r["response"]).split()) <= twins[t]["word_hi"])
    b = sum(1 for r in resps if r["twin_id"] == t and r["checkpoint"] == "starling"
            and twins[t]["word_lo"] <= len(trunc(r["response"]).split()) <= twins[t]["word_hi"])
    ct[(a, b)] += 1
print(f"  per-twin (phoenix_passes, starling_passes) cross-tab: {dict(sorted(ct.items()))}")
# binomial-ish: probability two independent Binomial(162,p) draws are exactly equal, p~0.1975
p = 32/162
from math import comb
pr = sum((comb(162,k)*p**k*(1-p)**(162-k))**2 for k in range(163))
print(f"  P(two independent Binomial(162, .1975) are exactly equal) = {pr:.4f}")
# byte-identity check: any identical responses across checkpoints?
seen = defaultdict(list)
for r in resps:
    seen[r["response"]].append((r["twin_id"], r["checkpoint"], r["seed"]))
dups = {k: v for k, v in seen.items() if len(v) > 1}
print(f"  byte-identical response strings shared by >1 record: {len(dups)}")
cross = [v for v in dups.values() if len(set(x[1] for x in v)) > 1]
print(f"  ... of which span BOTH checkpoints: {len(cross)}")

print("\n== 6. word count distributions ==")
for cp in ["phoenix", "starling"]:
    w = [len(trunc(r["response"]).split()) for r in resps if r["checkpoint"] == cp]
    print(f"  {cp}: n={len(w)} min={min(w)} p25={np.percentile(w,25):.0f} med={np.median(w):.0f} "
          f"p75={np.percentile(w,75):.0f} max={max(w)}")
lows = sorted(set((t["word_lo"], t["word_hi"]) for t in twins.values()))
print(f"  distinct (word_lo, word_hi) bands: {lows}")
print(f"  distinct (para_lo, para_hi): {sorted(set((t['para_lo'],t['para_hi']) for t in twins.values()))}")
print(f"  n_paragraphs values: {dict(Counter(t['n_paragraphs'] for t in twins.values()))}")
print(f"  band width check: para_hi - n_paragraphs = "
      f"{dict(Counter(t['para_hi']-t['n_paragraphs'] for t in twins.values()))}")

print("\n== 7. self-consistency: prompt text vs fields ==")
bad = []
for t in twins.values():
    ins = t["instruction"]
    if t["audience"] not in ins: bad.append((t["twin_id"], "audience"))
    if f"{t['word_lo']} and {t['word_hi']} words" not in ins: bad.append((t["twin_id"], "words"))
    if f"between {t['n_paragraphs']} and {t['n_paragraphs']+2} paragraphs" not in ins:
        bad.append((t["twin_id"], "paras"))
    if "Title:" not in ins: bad.append((t["twin_id"], "title"))
print(f"  twins failing mechanical prompt/field self-consistency: {len(bad)} {bad[:8]}")

print("\n== 8. block-count = 1 (no blank lines at all) ==")
for cp in ["phoenix", "starling"]:
    sub = [r for r in resps if r["checkpoint"] == cp]
    one = sum(1 for r in sub if "\n\n" not in trunc(r["response"]).strip())
    print(f"  {cp}: responses with no blank line at all: {one}/{len(sub)}")

print("\n== 9. does phoenix ever produce a doc-style opening? first 8 words sample ==")
random.seed(1)
for cp in ["phoenix", "starling"]:
    sub = [r for r in resps if r["checkpoint"] == cp]
    print(f"  --{cp}--")
    for r in random.sample(sub, 6):
        b = trunc(r["response"]).strip()
        print("    " + " ".join(b.split()[:8]))
