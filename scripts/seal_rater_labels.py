#!/usr/bin/env python3
"""Seal one S1-ENDORSE-V2 rater's labels: merge the shards, hash them, record provenance.

Sealing is what makes a rater file evidence. It happens BEFORE the disagreement audit and before any
checkpoint difference is computed, so the labels cannot be revised once the contrast is visible.

Refuses to overwrite an existing seal. Records a hash per shard and over the merged file, so a later
verifier can prove the analyzed labels are the sealed ones.
"""
import argparse, getpass, hashlib, json, platform, socket
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--rater", required=True, help="rater identity, e.g. raterA-claude-opus-5")
ap.add_argument("--shards", nargs="+", required=True)
ap.add_argument("--package", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--note", default="")
ap.add_argument("--exception", action="append", default=[],
                help="declared null-span exception carried from the gate check, CID:FIELD=REASON")
a = ap.parse_args()

out = Path(a.out)
if out.exists():
    raise SystemExit(f"REFUSING: seal already exists: {out}")
sha = lambda b: hashlib.sha256(b).hexdigest()

rows, per_shard = [], {}
for s in a.shards:
    p = Path(s)
    body = p.read_bytes()
    got = [json.loads(x) for x in body.decode().splitlines() if x.strip()]
    per_shard[p.parent.name or p.name] = {"path": str(p), "rows": len(got), "sha256": sha(body)}
    rows += got

cids = [r["cid"] for r in rows]
if len(set(cids)) != len(cids):
    raise SystemExit(f"REFUSING: {len(cids) - len(set(cids))} duplicate cids")

out.mkdir(parents=True)
merged = "\n".join(json.dumps(r, sort_keys=True) for r in sorted(rows, key=lambda r: r["cid"])) + "\n"
(out / "labels.jsonl").write_text(merged)

pkg = Path(a.package)
prov = {
    "task": "S1-ENDORSE-V2",
    "experiment": "docs/experiments/09-10_endorsement-feature_decomposition.md",
    "rater": a.rater,
    "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "sealed_by": f"{getpass.getuser()}@{socket.gethostname()} ({platform.platform()})",
    "rows": len(rows),
    "merged_sha256": sha(merged.encode()),
    "shards": per_shard,
    "package_key_sha256": sha((pkg / "key.json").read_bytes()),
    "package_prompt_sha256": sha((pkg / "PROMPT.md").read_bytes()),
    "package_provenance": json.loads((pkg / "provenance.json").read_text()),
    "declared_null_span_exceptions": a.exception,
    "note": a.note,
    "field_distributions_pooled": {
        f: dict(Counter(r.get(f) for r in rows)) for f in
        ("boundary_confidence", "net_stance", "assertion_form", "claim_uncertainty",
         "attribution", "added_support", "final_takeaway")},
    "concession_counts_pooled": {
        k: sum(1 for r in rows if (r.get("concessions") or {}).get(k) in (True, "true", "True"))
        for k in ("moral", "social", "legal", "stylistic", "opposing_view")},
}
(out / "provenance.json").write_text(json.dumps(prov, indent=1))
print(json.dumps({k: v for k, v in prov.items() if k != "package_provenance"}, indent=1))
