#!/usr/bin/env python3
"""Independent re-derivation of the 3-rater sensitivity analysis. Written from scratch."""
import csv, json, itertools, sys
import numpy as np

BASE = "/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad/slice"
LAB = ["unqualified", "concessionary", "misclassified"]
LIDX = {l: i for i, l in enumerate(LAB)}

# ---------- load ----------
key = json.load(open(f"{BASE}/key.json"))
items = key["items"]

def load_sheet(fn):
    rows = []
    with open(f"{BASE}/{fn}", newline="") as f:
        for r in csv.DictReader(f):
            rows.append((r["cid"].strip(), (r.get("subtype") or "").strip()))
    return rows

raw = {"gpt": load_sheet("sheet_second.csv"),
       "gemini_pro": load_sheet("sheet_third_gemini_pro.csv")}

print("="*72)
print("1. GATES")
print("="*72)
for name, rows in raw.items():
    cids = [c for c, _ in rows]
    dup = sorted({c for c in cids if cids.count(c) > 1})
    foreign = sorted(set(cids) - set(items))
    missing = sorted(set(items) - set(cids))
    bad = sorted({(c, s) for c, s in rows if s not in LIDX})
    print(f"[{name}] rows={len(rows)}  unique_cids={len(set(cids))}  duplicates={len(dup)} {dup}")
    print(f"[{name}] foreign_cids={len(foreign)} {foreign}  missing_vs_key={len(missing)} {missing}")
    print(f"[{name}] invalid_or_blank_labels={len(bad)} {bad}")
print(f"key.json items = {len(items)}")

order = sorted(items)          # deterministic item order
n = len(order)
claude = np.array([LIDX[items[c]["primary_subtype"]] for c in order])
arm = np.array([items[c]["arm"] for c in order])
lab = {"claude": claude}
for name, rows in raw.items():
    d = dict(rows)
    lab[name] = np.array([LIDX[d[c]] for c in order])

print("\nLabel distribution (counts / share):")
for name in ["claude", "gpt", "gemini_pro"]:
    v = lab[name]
    cs = [int((v == i).sum()) for i in range(3)]
    print(f"  {name:11s} " + "  ".join(f"{LAB[i]}={cs[i]:3d} ({cs[i]/n:.4f})" for i in range(3)))
print("Arm counts in slice:", {a: int((arm == a).sum()) for a in ["phoenix", "starling"]})
print("Arm x claude-class strata sizes:")
for a in ["phoenix", "starling"]:
    print(f"  {a:9s} " + "  ".join(f"{LAB[i]}={int(((arm==a)&(claude==i)).sum()):2d}" for i in range(3)))

# ---------- 2. permutation validity gate ----------
print("\n" + "="*72)
print("2. VALIDITY GATE (permutation, 20000 draws, seed 20260907)")
print("="*72)
rng = np.random.default_rng(20260907)
NPERM = 20000
for name in ["gpt", "gemini_pro"]:
    v = lab[name]
    obs = float((v == claude).mean())
    null = np.empty(NPERM)
    for k in range(NPERM):
        null[k] = (rng.permutation(v) == claude).mean()
    frac = float((null >= obs).mean())
    print(f"[{name}] observed_agreement={obs:.4f}  null_mean={null.mean():.4f}  "
          f"null_p95={np.percentile(null,95):.4f}  P(null>=obs)={frac:.5f}  "
          f"-> {'PASS' if frac < 0.05 else 'FAIL'}")

# ---------- 3. pairwise agreement + kappa (unweighted + population-weighted) ----------
POP = {"unqualified": 277, "concessionary": 128, "misclassified": 64}
NPOP = sum(POP.values())
slice_share = np.array([(claude == i).mean() for i in range(3)])
pop_share = np.array([POP[LAB[i]] / NPOP for i in range(3)])
wt_class = pop_share / slice_share
w_item = wt_class[claude]

def agree_kappa(a, b, w=None):
    w = np.ones(len(a)) if w is None else w
    W = w.sum()
    po = float((w * (a == b)).sum() / W)
    pa = np.array([w[a == i].sum() / W for i in range(3)])
    pb = np.array([w[b == i].sum() / W for i in range(3)])
    pe = float((pa * pb).sum())
    return po, (po - pe) / (1 - pe)

print(f"\nPopulation N={NPOP} (unq 277 / conc 128 / mis 64); slice share={slice_share.round(4)}; "
      f"item weights by claude class={wt_class.round(4)}")
print(f"{'pair':26s} {'agree':>7s} {'kappa':>8s} | {'agree_w':>8s} {'kappa_w':>8s}")
for x, y in [("claude", "gpt"), ("claude", "gemini_pro"), ("gpt", "gemini_pro")]:
    po, k = agree_kappa(lab[x], lab[y])
    pow_, kw = agree_kappa(lab[x], lab[y], w_item)
    print(f"{x+'-'+y:26s} {po:7.4f} {k:8.4f} | {pow_:8.4f} {kw:8.4f}")

print("\nConfusion matrices (rows=claude, cols=rater), counts:")
for name in ["gpt", "gemini_pro"]:
    print(f"  {name}: cols={LAB}")
    for i in range(3):
        row = [int(((claude == i) & (lab[name] == j)).sum()) for j in range(3)]
        print(f"    claude={LAB[i]:14s} {row}  n={sum(row)}")

# ---------- 4. projection ----------
PRIMARY = {"phoenix": np.array([87.0, 40.0, 33.0]),
           "starling": np.array([190.0, 88.0, 31.0])}
GEN = 540.0

def transmat(cl, rt):
    P = np.zeros((3, 3))
    for i in range(3):
        m = cl == i
        if m.sum() == 0:
            P[i] = np.nan
        else:
            for j in range(3):
                P[i, j] = ((rt[m] == j).sum()) / m.sum()
    return P

def share_from_P(P):
    proj = {a: PRIMARY[a] @ P for a in PRIMARY}
    mass = {a: proj[a] / GEN * 100.0 for a in proj}
    d = mass["starling"] - mass["phoenix"]
    tot = d[0] + d[1]
    return d[0] / tot, proj, mass, d, tot

print("\n" + "="*72)
print("4. PROJECTION")
print("="*72)
res = {}
for name in ["gpt", "gemini_pro"]:
    P = transmat(claude, lab[name])
    sh, proj, mass, d, tot = share_from_P(P)
    res[name] = (P, sh)
    print(f"\n[{name}] transition P(rater=y | claude=x), rows sum to 1:")
    for i in range(3):
        print(f"    claude={LAB[i]:14s} -> " +
              "  ".join(f"{LAB[j][:5]}={P[i,j]:.4f}" for j in range(3)) +
              f"   rowsum={P[i].sum():.6f}" + ("   <-- STRUCTURAL ZERO(S)" if (P[i] == 0).any() else ""))
    for a in ["phoenix", "starling"]:
        print(f"    {a:9s} primary={PRIMARY[a].astype(int).tolist()} total={int(PRIMARY[a].sum())} "
              f"-> projected={np.round(proj[a],4).tolist()} total={proj[a].sum():.6f} "
              f"| preserved={'YES' if abs(proj[a].sum()-PRIMARY[a].sum())<1e-9 else 'NO'}")
        print(f"    {a:9s} mass% = " + "  ".join(f"{LAB[j]}={mass[a][j]:.4f}" for j in range(3)))
    print(f"    delta(starling-phoenix) mass pp: " + "  ".join(f"{LAB[j]}={d[j]:+.4f}" for j in range(3)))
    print(f"    tot = d_unq + d_conc = {tot:.4f}   SHARE = {sh:.4f}")

# ---------- 5. stratified bootstrap ----------
print("\n" + "="*72)
print("5. STRATIFIED BOOTSTRAP (10000 draws, within 6 arm x claude-class strata, seed 777)")
print("="*72)
strata = [np.where((arm == a) & (claude == i))[0] for a in ["phoenix", "starling"] for i in range(3)]
NB = 10000
boot = {}
for name in ["gpt", "gemini_pro"]:
    rb = np.random.default_rng(777)
    v = lab[name]
    out = np.empty(NB)
    nan_draws = 0
    for b in range(NB):
        idx = np.concatenate([s[rb.integers(0, len(s), len(s))] for s in strata])
        P = transmat(claude[idx], v[idx])
        if np.isnan(P).any():
            nan_draws += 1
            out[b] = np.nan
            continue
        out[b] = share_from_P(P)[0]
    ok = out[~np.isnan(out)]
    lo, hi = np.percentile(ok, [2.5, 97.5])
    boot[name] = (lo, hi, ok)
    print(f"[{name}] point={res[name][1]:.4f}  boot_median={np.median(ok):.4f}  "
          f"95% CI=[{lo:.4f}, {hi:.4f}]  P(share>=0.60)={float((ok>=0.60).mean()):.4f}  "
          f"valid_draws={len(ok)}/{NB}")

# ---------- 6/7 ----------
print("\n" + "="*72)
print("6/7. BAR CHECKS (claude registered share = 0.6821, given)")
print("="*72)
CLAUDE_SHARE = 0.6821
pts = {"claude": CLAUDE_SHARE, "gpt": res["gpt"][1], "gemini_pro": res["gemini_pro"][1]}
for k, v in pts.items():
    print(f"  {k:11s} point share = {v:.4f}   >=0.60? {'YES' if v >= 0.60 else 'NO'}")
print(f"  raters with point share >= 0.60: {sum(v >= 0.60 for v in pts.values())} of 3")
for name in ["gpt", "gemini_pro"]:
    lo, hi = boot[name][0], boot[name][1]
    print(f"  [{name}] CI [{lo:.4f},{hi:.4f}] contains 0.60? "
          f"{'YES' if lo <= 0.60 <= hi else 'NO'}")
g, m = boot["gpt"], boot["gemini_pro"]
print(f"  CIs overlap each other? {'YES' if (g[0] <= m[1] and m[0] <= g[1]) else 'NO'}  "
      f"overlap=[{max(g[0],m[0]):.4f},{min(g[1],m[1]):.4f}]")
print(f"  point-share spread across 3 raters: {min(pts.values()):.4f} .. {max(pts.values()):.4f}")

# ---------- fragility ----------
print("\n" + "="*72)
print("FRAGILITY")
print("="*72)
for name in ["gpt", "gemini_pro"]:
    P = res[name][0]
    print(f"[{name}] structural zeros in P: " +
          str([(LAB[i], LAB[j]) for i in range(3) for j in range(3) if P[i, j] == 0]))
    # one-cell flip sensitivity: move a single item from each off-cell
    base = res[name][1]
    worst = []
    for i in range(3):
        for j in range(3):
            for j2 in range(3):
                if j == j2:
                    continue
                cnt = np.zeros((3, 3))
                for a in range(3):
                    for b in range(3):
                        cnt[a, b] = ((claude == a) & (lab[name] == b)).sum()
                if cnt[i, j] < 1:
                    continue
                cnt[i, j] -= 1
                cnt[i, j2] += 1
                P2 = cnt / cnt.sum(axis=1, keepdims=True)
                worst.append((abs(share_from_P(P2)[0] - base), LAB[i], LAB[j], LAB[j2],
                              share_from_P(P2)[0]))
    worst.sort(reverse=True)
    print(f"[{name}] largest share move from reclassifying ONE of the 150 items: "
          f"{worst[0][0]:.4f} (claude={worst[0][1]}: {worst[0][2]}->{worst[0][3]}, "
          f"share {base:.4f}->{worst[0][4]:.4f})")
