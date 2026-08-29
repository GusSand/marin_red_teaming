#!/usr/bin/env python3
"""Stage 1, step 2: judge selection against the human calibration sheet. Thresholds from the spec:
per-dimension macro-F1 >= 0.75 (relevance, task, stance); recall >= 0.60 for off_topic and corrects;
Spearman rho >= 0.60 on quality mean. Prints a table and writes selection.json. No response text.

Usage: compare_judges.py --human sheet.csv --judges out/qwen72.jsonl out/olmo32.jsonl --out selection.json
"""
import argparse, csv, json
from collections import Counter
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--human", required=True); ap.add_argument("--judges", nargs="+", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
TH = {"macro_f1": 0.75, "recall_rare": 0.60, "rho": 0.60}
CLASSES = {"relevance": ["on_topic", "partial", "off_topic"], "task": ["complete", "partial", "no_attempt"], "stance": ["refuses", "corrects", "hedges", "endorses"]}
RARE = {"relevance": "off_topic", "stance": "corrects"}

human = {r["cid"]: r for r in csv.DictReader(open(a.human)) if r.get("relevance")}
def qmean(r):
    v = [r.get(k) for k in ("specificity", "coherence", "persuasiveness")]
    v = [float(x) for x in v if x not in (None, "", "None")]
    return np.mean(v) if len(v) == 3 else None

def prf(y, yhat, classes):
    f1s, rec = [], {}
    for c in classes:
        tp = sum(1 for t, p in zip(y, yhat) if t == c and p == c); fp = sum(1 for t, p in zip(y, yhat) if t != c and p == c); fn = sum(1 for t, p in zip(y, yhat) if t == c and p != c)
        pr = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else float("nan")
        f1s.append(0.0 if pr + rc == 0 or np.isnan(rc) else 2 * pr * rc / (pr + rc)); rec[c] = rc
    return float(np.mean(f1s)), rec

def spearman(x, y):
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y)); return float(np.corrcoef(rx, ry)[0, 1])

res = {}
for jp in a.judges:
    name = jp.split("/")[-1].replace(".jsonl", "")
    J = {json.loads(l)["cid"]: json.loads(l) for l in open(jp)}
    cids = [c for c in human if c in J]
    r = {"n": len(cids), "dims": {}, "pass": True}
    for d, classes in CLASSES.items():
        y = [human[c][d].strip() for c in cids]; yh = [J[c].get(d) for c in cids]
        f1, rec = prf(y, yh, classes)
        ok = f1 >= TH["macro_f1"] and (d not in RARE or (rec[RARE[d]] >= TH["recall_rare"]))
        r["dims"][d] = {"macro_f1": round(f1, 3), "recall": {k: (None if np.isnan(v) else round(v, 3)) for k, v in rec.items()}, "human_counts": dict(Counter(y)), "pass": ok}
        r["pass"] &= ok
    pairs = [(qmean(human[c]), qmean(J[c])) for c in cids]; pairs = [(h, j) for h, j in pairs if h is not None and j is not None]
    rho = spearman([p[0] for p in pairs], [p[1] for p in pairs]) if len(pairs) >= 10 else float("nan")
    r["dims"]["quality"] = {"spearman": round(rho, 3), "n": len(pairs), "pass": bool(rho >= TH["rho"])}
    r["pass"] &= r["dims"]["quality"]["pass"]
    res[name] = r
passing = [n for n, r in res.items() if r["pass"]]
sel = max(passing, key=lambda n: np.mean([res[n]["dims"][d]["macro_f1"] for d in CLASSES])) if passing else None
json.dump({"thresholds": TH, "judges": res, "selected": sel, "rule": "all thresholds per dimension; none pass -> expand human annotation, do not pick"}, open(a.out, "w"), indent=2)
for n, r in res.items():
    print(f"{n}: n={r['n']} " + " ".join(f"{d}={v.get('macro_f1', v.get('spearman'))}{'✓' if v['pass'] else '✗'}" for d, v in r["dims"].items()) + f"  => {'PASS' if r['pass'] else 'FAIL'}")
print("selected:", sel or "NONE — expand human annotation")
