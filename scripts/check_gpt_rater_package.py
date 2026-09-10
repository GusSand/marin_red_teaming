#!/usr/bin/env python3
"""Verify a built S1-ENDORSE-V2 external-rater package before it is handed to anyone.

Checks the three things that have actually gone wrong on this project:
  - a rater package that leaked what it should not (checkpoint identity, key material);
  - item formats that disagree, so the rater labels something other than what we think it saw;
  - a return sheet whose header the converter cannot parse.

`upload/` is the handover surface and must be clean of checkpoint tokens and key material. Files
outside it are ours.
"""
import argparse, csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sheet_to_labels import COLS  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--package", required=True, help="the frozen source package")
ap.add_argument("--rater-package", required=True, help="the built external-rater package")
ap.add_argument("--parts", type=int, default=10)
a = ap.parse_args()
pkg, out = Path(a.package), Path(a.rater_package)
up = out / "upload"

fails, ok = [], []
gate = lambda c, m: (ok if c else fails).append(("PASS " if c else "FAIL ") + m)

leak = [str(p.relative_to(out)) for p in out.rglob("*") if "key" in p.name.lower()]
gate(not leak, f"no key material in the package: {leak}")

cids_all = set()
for p in range(1, a.parts + 1):
    src = pkg / "shards" / f"items_part{p}.jsonl"
    gate((up / f"items_part{p}.jsonl").read_bytes() == src.read_bytes(),
         f"part{p}: items jsonl byte-identical to the frozen shard")
    rows = [json.loads(x) for x in (up / f"items_part{p}.jsonl").read_text().splitlines() if x.strip()]
    cids = [r["cid"] for r in rows]
    csv_rows = list(csv.DictReader((up / f"items_part{p}.csv").open(newline="")))
    md = (up / f"items_part{p}.md").read_text()
    gate([r["cid"] for r in csv_rows] == cids, f"part{p}: csv cids match jsonl, in order")
    gate(all(r["response"] == c["response"] for r, c in zip(rows, csv_rows)),
         f"part{p}: csv response text exact")
    gate(all(f"## {c}" in md for c in cids), f"part{p}: md carries every cid")
    sheet = list(csv.DictReader((up / f"sheet_part{p}.csv").open(newline="")))
    gate([r["cid"] for r in sheet] == cids, f"part{p}: sheet cids match, in order")
    gate(list(sheet[0]) == COLS, f"part{p}: sheet header parses under the converter schema")
    gate(all(v == "" for r in sheet for k, v in r.items() if k != "cid"), f"part{p}: sheet is empty")
    cids_all |= set(cids)

gate(len(cids_all) == 108 * a.parts, f"{108 * a.parts} distinct cids: {len(cids_all)}")

prompt = (up / "PROMPT.md").read_text()
for need, label in (("net_stance", "output schema"), ("Non-epistemic concessions", "codebook"),
                    ("character-for-character", "verbatim-span rule"),
                    ("honest list beats an invented span", "permission to decline a span")):
    gate(need in prompt, f"PROMPT.md carries the {label}")

blob = "".join(p.read_text(errors="ignore") for p in up.rglob("*") if p.is_file())
hits = sorted(set(re.findall(r"phoenix|starling", blob, re.I)))
gate(not hits, f"handover surface upload/ names no checkpoint: {hits}")
for p in out.rglob("*"):
    if p.is_file() and p.parent != up:
        h = sorted(set(re.findall(r"phoenix|starling", p.read_text(errors='ignore'), re.I)))
        gate(not h, f"{p.relative_to(out)} names no checkpoint: {h}")

print("\n".join(ok))
if fails:
    print("\n".join(fails))
print(f"\n{'RATER PACKAGE OK' if not fails else 'RATER PACKAGE FAILED'} — "
      f"{len(ok)} checks, {len(fails)} failures")
sys.exit(1 if fails else 0)
