#!/usr/bin/env python3
"""Report benign-set COMPLIANCE for the H1b control.

    python scripts/report_benign.py <metrics.json> <tag>

H1b asks whether the misinformation trajectory is really improved instruction following. The
quantity that answers it is how often the model ANSWERS a benign instruction, not any kind of
attack-success rate: nothing is being attacked on this set. If compliance on benign prompts
rises across the six revisions by about as much as harmful compliance does, the trajectory is
task-following and S9 is not a safety finding.

safety-eval reports different field names per task, so resolve compliance if present and fall
back to 1 - refusal. If neither exists, say so loudly rather than printing a number that does
not mean what the hypothesis needs.
"""
import json
import sys

COMPLY_KEYS = ("compliance", "micro_compliance", "compliance_rate", "macro_compliance")
REFUSAL_KEYS = ("refusal", "micro_refusal_lower", "macro_refusal", "refusal_rate")

metrics_path, tag = sys.argv[1], sys.argv[2]
m = json.load(open(metrics_path))
task = next(iter(m))
d = m[task]
scalars = {k: v for k, v in d.items() if isinstance(v, (int, float))}

comply, how = None, ""
for k in COMPLY_KEYS:
    if k in scalars:
        comply, how = scalars[k], k
        break
if comply is None:
    for k in REFUSAL_KEYS:
        if k in scalars:
            comply, how = 1.0 - scalars[k], f"1-{k}"
            break

if comply is None:
    print(f"{tag}: WARNING no compliance/refusal field in {task}; H1b needs one")
    print(f"{tag}: available scalars = " + " ".join(f"{k}={v:.4f}" for k, v in scalars.items()))
    sys.exit(0)

print(f"{tag}: benign COMPLIANCE = {100 * comply:.1f}%  (from {how}, task={task})")
print(f"{tag}: raw scalars = " + " ".join(f"{k}={v:.4f}" for k, v in scalars.items()))
