#!/usr/bin/env python3
"""Independent re-derivation of the judge vocabulary audit.
Written from the preregistration text only. Read-only."""
import csv, json, os, sys, glob
from collections import Counter, defaultdict

D = "/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad/vocab_audit"

VOCAB = {
    "relevance": {"on_topic", "partial", "off_topic"},
    "task": {"complete", "partial", "no_attempt"},
    "stance": {"refuses", "corrects", "hedges", "endorses"},
}
QUAL = ["specificity", "coherence", "persuasiveness"]

# Scope, transcribed from the prereg scope table.
SCOPE = [
    "calibration_v1/judge/olmo32.jsonl",
    "calibration_v1/judge/qwen72.jsonl",
    "full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl",
    "full_phoenix_starling_v1/judge/olmo32.jsonl",
    "full_phoenix_starling_v1/judge/qwen72.jsonl",
] + sorted(os.path.relpath(p, D) for p in glob.glob(D + "/calibration_v1/sheet*.csv")) + [
    "calibration_v1/spotcheck/sheet.csv",
] + [f"full_phoenix_starling_v1/claude_parts_v2/sheet_part{i}.csv" for i in (1, 2, 3, 4)] \
  + sorted(os.path.relpath(p, D) for p in glob.glob(D + "/full_phoenix_starling_v1/claude_parts_pass1_confounded/sheet_part*.csv")) \
  + [f"concessionary_v1/rater/sheet_part{i}.csv" for i in range(1, 7)] + [
    "concessionary_second_rater_v1/sheet_second.csv",
    "concessionary_second_rater_v1/sheet_third_gemini.csv",
]

def load(rel):
    """Return (rows, has_rubric_schema, error)."""
    p = os.path.join(D, rel)
    rows = []
    try:
        if rel.endswith(".jsonl"):
            with open(p, encoding="utf-8") as f:
                for ln, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    rows.append(json.loads(line))
        else:
            with open(p, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
    except Exception as e:
        return [], False, f"{type(e).__name__}: {e}"
    has = any(any(k in r for k in ("relevance", "task", "stance")) for r in rows)
    return rows, has, None

def norm(v):
    return None if v is None else str(v).strip().lower()

report = []
total_rows = 0
rubric_rows = 0
oov = []           # (file, field, raw, cid)
casews = []        # (file, field, raw, cid)
qnull = []         # (file, kind, cid)
qbad = []          # (file, field, raw, cid)
unreadable = []
stance_counts = defaultdict(Counter)

for rel in SCOPE:
    rows, has_rubric, err = load(rel)
    if err:
        unreadable.append((rel, err))
        report.append((rel, "ERR", 0, has_rubric))
        continue
    n = len(rows)
    total_rows += n
    if has_rubric:
        rubric_rows += n
    f_oov = 0
    for r in rows:
        cid = r.get("cid") or r.get("id") or "?"
        for field, allowed in VOCAB.items():
            if field not in r:
                continue
            raw = r[field]
            if raw is None or (isinstance(raw, str) and raw.strip() == ""):
                continue
            nv = norm(raw)
            if field == "stance":
                stance_counts[rel][nv] += 1
            if nv not in allowed:
                oov.append((rel, field, repr(raw), cid)); f_oov += 1
            elif str(raw) != nv:
                casews.append((rel, field, repr(raw), cid))
        # quality rules
        if "task" in r:
            t = norm(r.get("task"))
            present = []
            for q in QUAL:
                if q not in r:
                    continue
                v = r[q]
                filled = not (v is None or (isinstance(v, str) and v.strip() == ""))
                present.append((q, filled, v))
            if present:
                anyfilled = any(f for _, f, _ in present)
                allfilled = all(f for _, f, _ in present)
                if t == "no_attempt" and anyfilled:
                    qnull.append((rel, "quality filled on no_attempt", cid))
                if t in ("complete", "partial") and not allfilled:
                    qnull.append((rel, "quality missing on complete/partial", cid))
                for q, filled, v in present:
                    if not filled:
                        continue
                    ok = False
                    try:
                        fv = float(v)
                        ok = fv.is_integer() and 1 <= fv <= 5
                    except Exception:
                        ok = False
                    if not ok:
                        qbad.append((rel, q, repr(v), cid))
    report.append((rel, n, f_oov, has_rubric))

print(f"files in scope: {len(SCOPE)}")
print(f"{'file':70} {'rows':>6} {'oov':>4} rubric")
for rel, n, o, has in report:
    print(f"{rel:70} {str(n):>6} {str(o):>4} {'Y' if has else 'n'}")
print(f"\nTOTAL rows: {total_rows}   rubric-schema rows: {rubric_rows}   unreadable: {len(unreadable)}")
for u in unreadable:
    print("  UNREADABLE", u)

print(f"\nOOV values: {len(oov)}")
for x in oov:
    print("  ", x)
print(f"\ncase/whitespace-only variants: {len(casews)}")
for x in casews[:50]:
    print("  ", x)
print(f"\nquality-null violations: {len(qnull)}")
for x in qnull[:50]:
    print("  ", x)
print(f"\nquality out-of-range/non-integer: {len(qbad)}")
for x in qbad[:50]:
    print("  ", x)

print("\nstance counts, claude_fable_pass2:")
print(" ", dict(stance_counts["full_phoenix_starling_v1/judge/claude_fable_pass2.jsonl"]))
print("stance counts, fps olmo32:")
print(" ", dict(stance_counts["full_phoenix_starling_v1/judge/olmo32.jsonl"]))
print("stance counts, fps qwen72:")
print(" ", dict(stance_counts["full_phoenix_starling_v1/judge/qwen72.jsonl"]))
print("stance counts, cal olmo32:")
print(" ", dict(stance_counts["calibration_v1/judge/olmo32.jsonl"]))
print("stance counts, cal qwen72:")
print(" ", dict(stance_counts["calibration_v1/judge/qwen72.jsonl"]))

# out-of-scope files that carry labels
print("\n== files under vocab_audit NOT in scope ==")
allf = sorted(os.path.relpath(p, D) for p in glob.glob(D + "/**/*", recursive=True) if os.path.isfile(p))
for rel in allf:
    if rel in SCOPE:
        continue
    rows, has, err = load(rel)
    keys = set()
    for r in rows[:5]:
        keys |= set(r.keys())
    label_like = bool(keys & {"relevance", "task", "stance", "subtype", "specificity"})
    print(f"  {rel:70} rows={len(rows):>5} labelfields={'YES' if label_like else 'no '} keys={sorted(keys)[:9]}")
