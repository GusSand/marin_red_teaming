#!/usr/bin/env python3
"""S1-PREFIX hand inspection, triggered by the pre-registered Iron Law tripwire.

The analysis reported an EXACT 0.0% empty and 0.0% non-response rate at all three arms.
The experiment file requires hand inspection before interpretation. This prints aggregate
counts only -- never response text -- and compares the arms against the traj4 reference
runs, where the same detector has always run.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from analyze_trajectory import load_run, is_echo, MISINFO  # noqa: E402

L = Path("/scratch/gs157/marin-misinfo-labels")
PFX = ("Here it is", "I have reviewed", "I've reviewed")


def scan(prefix, tags, nseeds):
    for t in tags:
        tot = emp = echo = miss = startpfx = short = 0
        lens = []
        for s in range(nseeds):
            raw = json.load(open(L / f"{prefix}-{t}-harmbench-s{s}" / "all.json"))
            rows = next(v for v in raw.values() if isinstance(v, list))
            for r in rows:
                if r.get("SemanticCategory") != MISINFO:
                    continue
                resp = str(r.get("response") or "")
                tot += 1
                if not resp.strip():
                    emp += 1
                if is_echo(r.get("Behavior"), resp):
                    echo += 1
                if r.get("response_harmfulness") is None:
                    miss += 1
                lens.append(len(resp))
                if resp.lstrip().startswith(PFX):
                    startpfx += 1
                if len(resp.strip()) < 40:
                    short += 1
        lens.sort()
        print(f"{t:16s} n={tot:4d} empty={emp:3d} echo={echo:3d} missing_label={miss:2d} "
              f"len_med={lens[len(lens)//2]:5d} len_p10={lens[len(lens)//10]:5d} "
              f"len_min={lens[0]:4d} starts_with_a_prefix_string={startpfx:3d} "
              f"very_short_lt40ch={short:3d}")


print("=== S1-PREFIX arms (5 seeds each) ===")
scan("2026-09-08-prefix-h200", ["none", "delivery", "deflect"], 5)
print("=== traj4 reference (10 seeds each) ===")
scan("2026-08-28-traj4-h200", ["phoenix", "starling"], 10)
