#!/usr/bin/env python3
"""Gate check 3: prove the sampler seed is actually in force on Torch.

    python scripts/check_seed_divergence.py <label> <all.json> <all.json> [...]

Give it two or more runs, each labelled with the seed it used, e.g.

    python scripts/check_seed_divergence.py \\
        s0a=/path/a/all.json s0b=/path/b/all.json s1=/path/c/all.json

It prints the fraction of per-instance responses that are IDENTICAL for every pair, and then
asserts the two properties the experiment depends on:

  same seed  -> responses reproduce   (identical fraction == 1.00)
  diff seed  -> responses diverge     (identical fraction well below 1.00)

Why this matters more than it looks. `run_row.sh` used to set only PYTHONHASHSEED, which does
NOT reach vLLM's sampler, so N "seeds" collapsed to one set of outputs wherever generation is
stable. That understated every confidence interval on this project once already (starling and
deeper-starling, INBOX 2026-07-29) and is invisible in the metrics: the numbers look clean, the
error bars are just fiction. The patch injects SAFETYEVAL_SAMPLING_SEED. This script is the
evidence the patch works *here*, on this cluster, in a real job -- not merely that the patched
line exists in a file.

Content-safe: compares hashes and counts, never prints a completion.
"""
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

RESPONSE_KEYS = ("response", "output", "generation", "completion", "model_output")
ID_KEYS = ("BehaviorID", "behavior_id", "id", "prompt", "instruction")


def load(path):
    """-> {instance_id: sha256(response)}  (hashes only; no completion text is retained)"""
    raw = json.load(open(path))
    rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
    out = {}
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        rid = next((str(r[k]) for k in ID_KEYS if k in r and r[k] is not None), str(i))
        resp = next((r[k] for k in RESPONSE_KEYS if k in r and r[k] is not None), None)
        if resp is None:
            continue
        out[rid] = hashlib.sha256(str(resp).encode()).hexdigest()
    return out


args = sys.argv[1:]
if len(args) < 2:
    sys.exit(__doc__)

runs = {}
for a in args:
    if "=" not in a:
        sys.exit(f"expected label=path, got {a!r}")
    label, path = a.split("=", 1)
    p = Path(path)
    if not p.exists():
        sys.exit(f"missing: {p}")
    runs[label] = load(p)
    print(f"{label:8} {len(runs[label]):4d} instances  {p}")

print()
results = {}
for a, b in combinations(runs, 2):
    ka, kb = runs[a], runs[b]
    common = set(ka) & set(kb)
    if not common:
        sys.exit(f"{a} and {b} share no instance ids; cannot compare")
    same = sum(1 for k in common if ka[k] == kb[k])
    frac = same / len(common)
    results[(a, b)] = frac
    print(f"{a:8} vs {b:8}  identical {same:4d}/{len(common):4d}  = {frac:6.1%}")

# Labels starting with the same seed token (s0a, s0b) are same-seed pairs.
def seed_of(label):
    return label.rstrip("abcdefghij")

print()
ok = True
for (a, b), frac in results.items():
    same_seed = seed_of(a) == seed_of(b)
    if same_seed:
        verdict = "PASS" if frac == 1.0 else "FAIL"
        print(f"  [{verdict}] same seed ({a},{b}): expected 100% identical, got {frac:.1%}")
        ok &= frac == 1.0
    else:
        verdict = "PASS" if frac < 0.95 else "FAIL"
        print(f"  [{verdict}] diff seed ({a},{b}): expected divergence, {frac:.1%} identical")
        ok &= frac < 0.95

print()
if ok:
    print("GATE CHECK 3 PASS: sampler seed is in force on Torch "
          "(same seed reproduces, different seeds diverge)")
    sys.exit(0)
print("GATE CHECK 3 FAIL: seeds are not behaving as required. Do NOT run the trajectory; "
      "any multi-seed spread would be fiction.", file=sys.stderr)
sys.exit(1)
