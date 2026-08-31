#!/usr/bin/env python3
"""Build the out-of-sample GPT rater slice (experiment 08-31).

Second frontier rater on items the calibration set never touched, under the SAME conventions the
pass-2 full-set annotators used. Answers "are the step-3 labels rater-specific?" with an
out-of-sample inter-rater estimate, replacing the in-sample Claude-vs-GPT figure on the 150.

Sampling: simple random, stratified only by arm (75 phoenix / 75 starling), seeded. No stratification
on label -- that would bias the agreement estimate toward rare classes.

Blinding: items are re-cid'd to shuffled `g####`. The full-set `i####` ids are run-ordered, so reusing
them would leak the arm to the rater -- the same defect that confounded pass 1.

Writes:
  <out>/upload/items.jsonl   blinded, THIS is what goes to the rater
  <out>/upload/PROMPT.md     rubric + conventions + output contract, paste-ready
  <out>/upload/sheet.csv     empty sheet in the locked schema
  <out>/items.jsonl          same items (for compare_anchors.py, which expects them beside the sheets)
  <out>/sheet_claude.csv     Claude pass-2 labels on these items -- NEVER upload this
  <out>/key.json             g-cid -> i-cid, run, BehaviorID, wildguard labels
  <out>/provenance.json      seed, counts, source paths, rubric sha

Usage:
  build_gpt_slice.py --full <full_phoenix_starling_v1> --calibration <calibration_v1> \
      --rubric config/judge_rubric_v1 --conventions config/annotator_conventions_v1.md --out <dir>
"""
import argparse, csv, hashlib, json, random
from pathlib import Path

COLS = ["cid", "relevance", "task", "stance", "specificity", "coherence", "persuasiveness", "notes"]
ap = argparse.ArgumentParser()
ap.add_argument("--full", required=True); ap.add_argument("--calibration", required=True)
ap.add_argument("--rubric", required=True); ap.add_argument("--conventions", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=150); ap.add_argument("--seed", type=int, default=20260831)
a = ap.parse_args()

full, cal, out = Path(a.full), Path(a.calibration), Path(a.out)
if (out / "key.json").exists():
    raise SystemExit(f"REFUSING: {out}/key.json exists")

jl = lambda p: [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
items = {r["cid"]: r for r in jl(full / "items.jsonl")}
key = json.load(open(full / "key.json"))["items"]
seen = {(r["request"], r["response"]) for r in jl(cal / "items.jsonl")}
claude = {r["cid"]: r for r in jl(full / "judge" / "claude_fable_pass2.jsonl")}

arm = lambda i: "phoenix" if "phoenix" in key[i]["run"] else "starling"
pool = {"phoenix": [], "starling": []}
for cid, it in items.items():
    if (it["request"], it["response"]) in seen: continue      # out-of-sample only
    if cid not in claude: continue                            # need a pass-2 label to compare against
    pool[arm(cid)].append(cid)

rng = random.Random(a.seed)
per = a.n // 2
chosen = []
for tag in ("phoenix", "starling"):
    if len(pool[tag]) < per: raise SystemExit(f"only {len(pool[tag])} {tag} items available, need {per}")
    chosen += rng.sample(sorted(pool[tag]), per)
rng.shuffle(chosen)

up = out / "upload"; up.mkdir(parents=True, exist_ok=True)
gmap = {}
with (up / "items.jsonl").open("w") as fu, (out / "items.jsonl").open("w") as fo, \
     (up / "sheet.csv").open("w", newline="") as fs, (out / "sheet_claude.csv").open("w", newline="") as fc:
    ws, wc = csv.writer(fs), csv.writer(fc); ws.writerow(COLS); wc.writerow(COLS)
    for n, icid in enumerate(chosen):
        g = f"g{n:04d}"; gmap[g] = icid
        rec = json.dumps({"cid": g, "request": items[icid]["request"], "response": items[icid]["response"]})
        fu.write(rec + "\n"); fo.write(rec + "\n")
        ws.writerow([g] + [""] * 7)
        r = claude[icid]
        q = [r.get(k) for k in ("specificity", "coherence", "persuasiveness")]
        wc.writerow([g, r.get("relevance", ""), r.get("task", ""), r.get("stance", "")] +
                    ["" if x is None else x for x in q] + [""])

sha = hashlib.sha256()
for f in sorted(Path(a.rubric).glob("*.txt")): sha.update(f.read_bytes())
prompt = [
    "# Annotation task\n",
    "You are labelling model responses for a research study. Work through **every** item in",
    "`items.jsonl` and return one CSV row per item.\n",
    "## Role\n", Path(a.rubric, "system.txt").read_text().strip(), "\n",
    "## The four dimensions\n",
]
for dim in ("relevance", "task", "stance", "quality"):
    body = Path(a.rubric, f"prompt_{dim}.txt").read_text().strip()
    body = body.split("RESPONSE:\n{response}\n", 1)[-1].strip()
    prompt += [f"### {dim}\n", body, ""]
prompt += ["\n## Operating conventions\n", Path(a.conventions).read_text().strip(), ""]
(up / "PROMPT.md").write_text("\n".join(prompt) + "\n")

json.dump({"g_to_i": gmap,
           "items": {g: {"run": key[i]["run"], "BehaviorID": key[i]["BehaviorID"],
                         "wg_harm": key[i]["wg_harm"], "wg_ref": key[i]["wg_ref"]} for g, i in gmap.items()}},
          open(out / "key.json", "w"), indent=1)
json.dump({"seed": a.seed, "n": a.n, "per_arm": per,
           "pool_sizes": {k: len(v) for k, v in pool.items()},
           "excluded_calibration_items": len(seen),
           "rubric_sha256": sha.hexdigest()[:8],
           "conventions": str(a.conventions),
           "source_full": str(full), "source_calibration": str(cal),
           "compare_against": "judge/claude_fable_pass2.jsonl"},
          open(out / "provenance.json", "w"), indent=1)
print(f"pool after excluding calibration: phoenix {len(pool['phoenix'])}, starling {len(pool['starling'])}")
print(f"wrote {len(chosen)} items ({per}/{per}) -> {up}")
print(f"UPLOAD ONLY {up}/items.jsonl and {up}/PROMPT.md ; sheet_claude.csv and key.json stay behind")
