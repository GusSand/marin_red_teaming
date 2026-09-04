#!/usr/bin/env python3
"""Independent verifier: second-rater agreement on the 3f concessionary slice.
Written from scratch; no project analysis code consulted."""
import csv, json, os
from collections import Counter, defaultdict

BASE = "/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad/slice"
KEY = os.path.join(BASE, "key.json")
CSV = os.path.join(BASE, "sheet_second.csv")

LAB = ["unqualified", "concessionary", "misclassified"]

key = json.load(open(KEY))["items"]

rows = []
with open(CSV, newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)

print("=" * 70)
print("1. GATES")
print("=" * 70)
print("csv data rows:", len(rows))
cids = [r["cid"].strip() for r in rows]
dupes = [c for c, n in Counter(cids).items() if n > 1]
print("duplicate cids in csv:", len(dupes), dupes)
print("key.json items:", len(key))
missing_from_csv = sorted(set(key) - set(cids))
extra_in_csv = sorted(set(cids) - set(key))
print("in key, missing from csv:", len(missing_from_csv), missing_from_csv)
print("in csv, not in key:", len(extra_in_csv), extra_in_csv)
bad = [(r["cid"], repr(r["subtype"])) for r in rows if r["subtype"].strip() not in LAB]
print("subtypes outside vocabulary:", len(bad), bad)
blank = [r["cid"] for r in rows if not r["subtype"].strip()]
print("blank subtypes:", len(blank), blank)
blanknotes = [r["cid"] for r in rows if not (r.get("notes") or "").strip()]
print("blank notes:", len(blanknotes))
# whitespace / case oddities
odd = [(r["cid"], repr(r["subtype"])) for r in rows if r["subtype"] != r["subtype"].strip()]
print("subtype cells with stray whitespace:", len(odd))

# primary key stratification
strat = Counter((key[c]["arm"], key[c]["primary_subtype"]) for c in key)
print("slice stratification (arm, primary):", dict(strat))

# ---------------------------------------------------------------- pairs
pairs = []  # (cid, arm, primary, second)
for r in rows:
    c = r["cid"].strip()
    if c not in key:
        continue
    pairs.append((c, key[c]["arm"], key[c]["primary_subtype"], r["subtype"].strip()))
N = len(pairs)


def conf(ps):
    m = {a: {b: 0 for b in LAB} for a in LAB}
    for _, _, p, s in ps:
        m[p][s] += 1
    return m


def wconf(ps, w):
    m = {a: {b: 0.0 for b in LAB} for a in LAB}
    for cid, _, p, s in ps:
        m[p][s] += w[cid]
    return m


def kappa_from(m):
    tot = sum(m[a][b] for a in LAB for b in LAB)
    po = sum(m[a][a] for a in LAB) / tot
    pe = 0.0
    for a in LAB:
        rmarg = sum(m[a][b] for b in LAB) / tot
        cmarg = sum(m[x][a] for x in LAB) / tot
        pe += rmarg * cmarg
    k = (po - pe) / (1 - pe) if pe != 1 else float("nan")
    return po, pe, k, tot


print()
print("=" * 70)
print("2. AGREEMENT (primary rows x second columns)")
print("=" * 70)
M = conf(pairs)
po, pe, k, tot = kappa_from(M)
print(f"n = {int(tot)}")
print(f"raw 3-subtype agreement = {po:.3f}   ({sum(M[a][a] for a in LAB)}/{int(tot)})")
print(f"expected agreement pe   = {pe:.3f}")
print(f"Cohen's kappa           = {k:.3f}")
print()
hdr = f"{'primary \\ second':>20}" + "".join(f"{b:>16}" for b in LAB) + f"{'row tot':>10}"
print(hdr)
for a in LAB:
    rt = sum(M[a][b] for b in LAB)
    print(f"{a:>20}" + "".join(f"{M[a][b]:>16d}" for b in LAB) + f"{rt:>10d}")
print(f"{'col tot':>20}" + "".join(f"{sum(M[a][b] for a in LAB):>16d}" for b in LAB) + f"{int(tot):>10d}")

print()
print("per-class:")
print(f"{'class':>16}{'primary n':>12}{'second n':>11}{'both':>7}{'recall':>9}{'precision':>11}")
for a in LAB:
    pn = sum(M[a][b] for b in LAB)
    sn = sum(M[x][a] for x in LAB)
    both = M[a][a]
    rec = both / pn if pn else float("nan")
    prec = both / sn if sn else float("nan")
    print(f"{a:>16}{pn:>12d}{sn:>11d}{both:>7d}{rec:>9.3f}{prec:>11.3f}")

print()
print("by arm:")
for arm in ["phoenix", "starling"]:
    sub = [p for p in pairs if p[1] == arm]
    Ma = conf(sub)
    poa, pea, ka, tota = kappa_from(Ma)
    print(f"  {arm}: n={int(tota)}  agreement={poa:.3f}  kappa={ka:.3f}")
    for a in LAB:
        print(f"      {a:>14}" + "".join(f"{Ma[a][b]:>7d}" for b in LAB))

print()
print("=" * 70)
print("3. THE BOUNDARY: concessionary <-> misclassified")
print("=" * 70)
cm = M["concessionary"]["misclassified"]
mc = M["misclassified"]["concessionary"]
print(f"primary concessionary -> second misclassified : {cm}")
print(f"primary misclassified -> second concessionary : {mc}")
print(f"total crossings on that boundary              : {cm + mc}")
print("other off-diagonal cells:")
for a in LAB:
    for b in LAB:
        if a != b and not {a, b} == {"concessionary", "misclassified"}:
            print(f"  {a} -> {b}: {M[a][b]}")

print()
print("=" * 70)
print("4. POPULATION-WEIGHTED")
print("=" * 70)
POP = {"unqualified": 277, "concessionary": 128, "misclassified": 64}
POPN = sum(POP.values())
slice_counts = Counter(p[2] for p in pairs)
w = {}
wt_by_class = {}
for a in LAB:
    pop_share = POP[a] / POPN
    sl_share = slice_counts[a] / N
    wt_by_class[a] = pop_share / sl_share
for cid, arm, p, s in pairs:
    w[cid] = wt_by_class[p]
print(f"population (469): {POP}, shares " + ", ".join(f"{a}={POP[a]/POPN:.3f}" for a in LAB))
print(f"slice counts by primary: {dict(slice_counts)}, shares " + ", ".join(f"{a}={slice_counts[a]/N:.3f}" for a in LAB))
print("weights per item: " + ", ".join(f"{a}={wt_by_class[a]:.4f}" for a in LAB))
WM = wconf(pairs, w)
wpo, wpe, wk, wtot = kappa_from(WM)
print(f"weighted n (sum of weights) = {wtot:.3f}")
print(f"weighted agreement = {wpo:.3f}")
print(f"weighted pe        = {wpe:.3f}")
print(f"weighted kappa     = {wk:.3f}")
print(f"delta vs unweighted: agreement {wpo-po:+.3f}, kappa {wk-k:+.3f}")
print("weighted confusion (rows primary):")
for a in LAB:
    print(f"  {a:>16}" + "".join(f"{WM[a][b]:>12.3f}" for b in LAB))

print()
print("=" * 70)
print("5. VERDICT vs FROZEN THRESHOLDS")
print("=" * 70)
def verdict(kv, agv):
    if kv < 0.50:
        return "POOR"
    if kv < 0.60 or agv < 0.75:
        return "MODERATE"
    return "ADEQUATE"
print(f"unweighted: kappa={k:.3f}, agreement={po:.3f} -> {verdict(k, po)}")
print(f"weighted:   kappa={wk:.3f}, agreement={wpo:.3f} -> {verdict(wk, wpo)}")

print()
print("=" * 70)
print("6. POST-HOC ROBUSTNESS: does MAINLY UNQUALIFIED survive?")
print("=" * 70)
T = {}
for a in LAB:
    pn = sum(M[a][b] for b in LAB)
    T[a] = {b: M[a][b] / pn for b in LAB}
print("transition P(second=y | primary=x):")
print(f"{'x \\ y':>16}" + "".join(f"{b:>16}" for b in LAB))
for a in LAB:
    print(f"{a:>16}" + "".join(f"{T[a][b]:>16.4f}" for b in LAB))

PRIM = {
    "phoenix": {"unqualified": 87, "concessionary": 40, "misclassified": 33},
    "starling": {"unqualified": 190, "concessionary": 88, "misclassified": 31},
}
DEN = 540.0
proj = {}
print()
for arm in ["phoenix", "starling"]:
    proj[arm] = {b: sum(PRIM[arm][a] * T[a][b] for a in LAB) for b in LAB}
    print(f"{arm}: primary counts {PRIM[arm]} (n={sum(PRIM[arm].values())})")
    for b in LAB:
        terms = " + ".join(f"{PRIM[arm][a]}*{T[a][b]:.4f}" for a in LAB)
        print(f"    projected {b:>14} = {terms} = {proj[arm][b]:.3f}  -> mass {100*proj[arm][b]/DEN:.3f}%")
    print(f"    projected total = {sum(proj[arm].values()):.3f} (must equal {sum(PRIM[arm].values())})")

print()
delta = {}
for b in LAB:
    ms = 100 * proj["starling"][b] / DEN
    mp = 100 * proj["phoenix"][b] / DEN
    delta[b] = ms - mp
    print(f"delta {b:>14} = {ms:.3f}% - {mp:.3f}% = {delta[b]:+.3f}pp")
tot60 = delta["unqualified"] + delta["concessionary"]
share = delta["unqualified"] / tot60
print()
print(f"tot = d_u + d_c = {delta['unqualified']:.3f} + {delta['concessionary']:.3f} = {tot60:.3f}pp")
print(f"share d_u/tot = {delta['unqualified']:.3f}/{tot60:.3f} = {share:.4f} = {100*share:.2f}%")
print(f">= 60%? {'YES -> MAINLY UNQUALIFIED holds' if share >= 0.60 else 'NO -> becomes MIXED'}")
d3 = sum(delta[b] for b in LAB)
print(f"[aux] three-way sum tot = {d3:.3f}pp, share = {100*delta['unqualified']/d3:.2f}%")

print()
print("registered (primary labels) for comparison: d_u=+19.07, d_c=+8.89, share 68.21%")

print()
print("=" * 70)
print("SYMMETRY OF DISAGREEMENT")
print("=" * 70)
for a in LAB:
    for b in LAB:
        if a < b or (a != b):
            pass
seen = set()
for a in LAB:
    for b in LAB:
        if a == b or (b, a) in seen:
            continue
        seen.add((a, b))
        print(f"  primary {a} -> second {b}: {M[a][b]}   |   primary {b} -> second {a}: {M[b][a]}")
print()
print("marginal shift (second n - primary n):")
for a in LAB:
    pn = sum(M[a][b] for b in LAB)
    sn = sum(M[x][a] for x in LAB)
    print(f"  {a:>16}: primary {pn}, second {sn}, net {sn-pn:+d}")
