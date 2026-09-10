#!/usr/bin/env python3
"""Emit upload-ready formats of the frozen S1-ENDORSE-V2 shards for an external rater.

Reads the built package; never modifies it. The frozen `shards/*.jsonl` stay authoritative — these
are the same rows in formats a web rater UI will actually accept. `.jsonl` alone silently failed on
2026-09-07 (AI Studio rejected it and the rater labelled 150 items it had never seen), so every shard
also ships as CSV and Markdown.
"""
import argparse, csv, hashlib, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--package", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--parts", type=int, default=10)
a = ap.parse_args()
pkg, out = Path(a.package), Path(a.out)
if out.exists():
    raise SystemExit(f"REFUSING: output exists: {out}")
out.mkdir(parents=True)

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = {"source_package": str(pkg), "parts": a.parts, "files": {}}
total = 0
for p in range(1, a.parts + 1):
    src = pkg / "shards" / f"items_part{p}.jsonl"
    rows = [json.loads(x) for x in src.read_text().splitlines() if x.strip()]
    total += len(rows)
    (out / f"items_part{p}.jsonl").write_text(src.read_text())
    with (out / f"items_part{p}.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cid", "request", "response"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ("cid", "request", "response")})
    md = [f"# Items — part {p} of {a.parts} ({len(rows)} items)", ""]
    for r in rows:
        md += [f"## {r['cid']}", "", "**Request**", "", "```", r["request"].strip(), "```", "",
               "**Response**", "", "```", r["response"].strip(), "```", ""]
    (out / f"items_part{p}.md").write_text("\n".join(md))
    manifest["files"][f"part{p}"] = {
        "rows": len(rows), "source_sha256": sha(src),
        **{ext: sha(out / f"items_part{p}.{ext}") for ext in ("jsonl", "csv", "md")}}

(out / "PROMPT.md").write_text((pkg / "PROMPT.md").read_text())
manifest["rows_total"] = total
manifest["prompt_sha256"] = sha(out / "PROMPT.md")
(out / "manifest.json").write_text(json.dumps(manifest, indent=1))
readme = f"""# S1-ENDORSE-V2 — external rater package (full set, {total} rows)

Each of the {a.parts} parts holds the same rows in three formats. Give the rater **one** format; the
other two exist because upload paths differ. Never send `key.json` — it is not in this directory.

1. Give the rater `PROMPT.md` in full. It is the frozen codebook plus the output schema.
2. Give it one part's items.
3. Ask for one JSON object per input line, `cid` preserved exactly, spans verbatim from the response.
4. Return the labels as `labels_part<N>.jsonl`.

The rater must not be told the checkpoint contrast, the hypothesis, this project, or the other rater's
output. Give each rater a private working directory.

Validate any returned file before it is trusted:

    python3 scripts/check_endorsement_labels.py --package <package> --labels labels_part*.jsonl
"""
(out / "README.md").write_text(readme)
print(json.dumps({"rows": total, "parts": a.parts, "out": str(out)}, indent=1))
