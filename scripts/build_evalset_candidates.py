#!/usr/bin/env python3
"""S1-06: assemble the blinded candidate package for the >=150-behaviour misinformation eval set.

Plan: docs/experiments/08-29_misinfo-evalset_selection.md (frozen 2026-08-29; judge substitution
declared 2026-09-05 before any screening ran).

Sources:
  - HarmBench misinformation_disinformation (standard + contextual) -- the 54 anchors, kept whole,
    never screened. They are the incumbent set.
  - WildJailbreak vanilla-harmful, keyword-and-artefact prescreened (the 08-29 recall net).

Emits a blinded screening package. Candidates are re-cid'd `c####` and SHUFFLED WITH THE ANCHORS
REMOVED, so a screener cannot infer source from position. Two independent screens are run over the same
file; this script only builds the input.

Writes, outside the repo:
  <out>/candidates.jsonl   blinded screener input: cid / request only
  <out>/anchors.jsonl      the 54 HarmBench anchors, for the near-duplicate pass
  <out>/key.json           cid -> source, source_index, whether it is an anchor
  <out>/provenance.json    counts, keyword net definition, source paths, sha of each source file

Usage: build_evalset_candidates.py --se <safety-eval dir> --out <dir>
"""
import argparse, csv, hashlib, json, random, re
from pathlib import Path

KW = re.compile(r"\b(misinformation|disinformation|fake news|false claim|conspiracy|hoax|propaganda|"
                r"debunk|vaccine|climate|election|fraudulent article|fabricat|rumou?r|deny|denial|"
                r"flat earth|chemtrail|5g|microchip|stolen election|deep ?fake|pseudoscien)\w*", re.I)
ART = re.compile(r"\b(article|blog|post|essay|op-ed|news|story|tweet|thread|report|press release|"
                 r"pamphlet|speech)\b", re.I)
MISINFO = "misinformation_disinformation"

ap = argparse.ArgumentParser()
ap.add_argument("--se", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--seed", type=int, default=20260905)
a = ap.parse_args()
out = Path(a.out)
if (out / "key.json").exists():
    raise SystemExit(f"REFUSING: {out}/key.json exists")
G = Path(a.se) / "evaluation" / "tasks" / "generation"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ---- anchors: HarmBench misinfo, standard + contextual --------------------------------------------
hb_path = None
for cand in (G / "harmbench" / "harmbench_behaviors_text_all.csv",
             G / "harmbench" / "harmbench.csv"):
    if cand.exists():
        hb_path = cand; break
if hb_path is None:
    hb_path = next(p for p in (G / "harmbench").glob("*.csv"))
hb = [r for r in csv.DictReader(open(hb_path))
      if r.get("SemanticCategory") == MISINFO and r.get("FunctionalCategory") in ("standard", "contextual")]
anchors = []
for r in hb:
    req = r["Behavior"]
    ctx = (r.get("ContextString") or "").strip()
    if ctx:
        req = f"{req}\n\n[Context]\n{ctx}"
    anchors.append({"BehaviorID": r["BehaviorID"], "request": req,
                    "functional": r.get("FunctionalCategory")})

# ---- candidates: WildJailbreak vanilla-harmful through the 08-29 recall net -----------------------
wj = [json.loads(l) for l in open(G / "wildjailbreak" / "harmful.jsonl")]
van = [r["vanilla"] for r in wj]
cand_idx = [i for i, p in enumerate(van) if KW.search(p) and ART.search(p)]

rng = random.Random(a.seed)
rows = [{"src": "wildjailbreak", "i": i, "request": van[i]} for i in cand_idx]
rng.shuffle(rows)

out.mkdir(parents=True, exist_ok=True)
key = {}
with (out / "candidates.jsonl").open("w") as f:
    for n, r in enumerate(rows):
        cid = f"c{n:04d}"
        key[cid] = {"source": r["src"], "source_index": r["i"], "is_anchor": False}
        f.write(json.dumps({"cid": cid, "request": r["request"]}) + "\n")
with (out / "anchors.jsonl").open("w") as f:
    for n, r in enumerate(anchors):
        f.write(json.dumps({"anchor_id": f"a{n:03d}", "BehaviorID": r["BehaviorID"],
                            "request": r["request"]}) + "\n")

prov = {"experiment": "docs/experiments/08-29_misinfo-evalset_selection.md",
        "seed": a.seed,
        "anchors_harmbench_misinfo": len(anchors),
        "anchor_functional_mix": {k: sum(1 for r in anchors if r["functional"] == k)
                                  for k in {r["functional"] for r in anchors}},
        "wildjailbreak_pool": len(van),
        "wildjailbreak_keyword_and_artifact": len(cand_idx),
        "candidates_emitted": len(key),
        "target_after_dedupe": 150,
        "shortfall_if_all_rejected": 150 - len(anchors),
        "keyword_net": KW.pattern, "artifact_net": ART.pattern,
        "source_files": {"harmbench": str(hb_path), "harmbench_sha256": sha(hb_path),
                         "wildjailbreak": str(G / "wildjailbreak" / "harmful.jsonl"),
                         "wildjailbreak_sha256": sha(G / "wildjailbreak" / "harmful.jsonl")},
        "note": "keyword net is a RECALL net only; inclusion is decided by the frozen rule via two "
                "independent blind screens plus gs157's hand check"}
(out / "key.json").write_text(json.dumps({"items": key}, indent=1))
(out / "provenance.json").write_text(json.dumps(prov, indent=1))
print(json.dumps(prov, indent=1))
