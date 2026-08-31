"""Independent verification of pre-registered analysis 08-31 (S1-3D).
Written from scratch from the preregistration document only.
No repo analysis code was read.
"""
import json, random, sys, collections
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss

SCRATCH = "/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad"
KEY = SCRATCH + "/labels/key.json"
P2 = SCRATCH + "/labels/claude_fable_pass2.jsonl"

REL = ["on_topic", "partial", "off_topic"]        # ref on_topic
TASK = ["complete", "partial", "no_attempt"]      # ref complete
STANCE = ["endorses", "refuses", "corrects", "hedges"]  # ref endorses

out = {}
log = []
def P(*a):
    s = " ".join(str(x) for x in a)
    log.append(s); print(s)

key = json.load(open(KEY))["items"]
judge = {}
dupe = 0
with open(P2) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r["cid"] in judge: dupe += 1
        judge[r["cid"]] = r

P("=== GATES ===")
P("n key items:", len(key), " unique key cids:", len(set(key)))
P("n judge lines-with-cid:", len(judge), " duplicate judge cids:", dupe)
judge_not_in_key = sorted(set(judge) - set(key))
key_not_in_judge = sorted(set(key) - set(judge))
P("judge cids missing from key:", len(judge_not_in_key), judge_not_in_key[:10])
P("key cids missing from judge:", len(key_not_in_judge), key_not_in_judge[:10])

# vocabulary check
oov = collections.Counter()
for cid, r in judge.items():
    if r.get("relevance") not in REL: oov[("relevance", r.get("relevance"))] += 1
    if r.get("task") not in TASK: oov[("task", r.get("task"))] += 1
    if r.get("stance") not in STANCE: oov[("stance", r.get("stance"))] += 1
    for q in ("specificity", "coherence", "persuasiveness"):
        v = r.get(q)
        if v is not None and not (isinstance(v, int) and 1 <= v <= 5):
            oov[(q, v)] += 1
P("out-of-vocabulary label values:", dict(oov) if oov else "NONE")

# quality mean
def qmean(r):
    vs = [r.get(k) for k in ("specificity", "coherence", "persuasiveness")]
    if any(v is None for v in vs): return None
    return sum(vs) / 3.0

viol_null_not_na = 0   # quality null but task != no_attempt
viol_na_not_null = 0   # task == no_attempt but quality non-null
partial_q = 0          # some of the three null, some not
for cid, r in judge.items():
    vs = [r.get(k) for k in ("specificity", "coherence", "persuasiveness")]
    nnull = sum(v is None for v in vs)
    if 0 < nnull < 3: partial_q += 1
    q = qmean(r)
    if q is None and r.get("task") != "no_attempt": viol_null_not_na += 1
    if q is not None and r.get("task") == "no_attempt": viol_na_not_null += 1
P("quality-null-but-task!=no_attempt:", viol_null_not_na)
P("task==no_attempt-but-quality-non-null:", viol_na_not_null)
P("rows with partially-null quality triple:", partial_q)

wgvals = collections.Counter(v.get("wg_harm") for v in key.values())
P("wg_harm value counts over all 1080 key items:", dict(wgvals))

# Build rows: set S = all rows with a pass-2 label (and present in key)
rows = []
for cid in sorted(set(judge) & set(key)):
    r = judge[cid]; k = key[cid]
    rows.append(dict(cid=cid, bid=k["BehaviorID"], run=k["run"],
                     y=1 if k.get("wg_harm") == "harmful" else 0,
                     wg_harm=k.get("wg_harm"), empty=k.get("empty"),
                     relevance=r["relevance"], task=r["task"], stance=r["stance"],
                     q=qmean(r)))
S = rows
Pset = [r for r in rows if r["q"] is not None]
P("n(S):", len(S), "harmful:", sum(r["y"] for r in S), "unharmful:", len(S) - sum(r["y"] for r in S))
P("n(P):", len(Pset), "harmful:", sum(r["y"] for r in Pset), "unharmful:", len(Pset) - sum(r["y"] for r in Pset))
P("rows with wg_harm null (counted y=0 per prereg 'else 0'):",
  sum(1 for r in S if r["wg_harm"] is None), " of which in P:", sum(1 for r in Pset if r["wg_harm"] is None))
P("empty==True rows: in S:", sum(1 for r in S if r["empty"]), " in P:", sum(1 for r in Pset if r["empty"]))

bids = sorted({r["bid"] for r in S})
P("n behaviors:", len(bids))

# frozen folds
shuf = list(bids)
random.Random(20260828).shuffle(shuf)
assert len(shuf) == 54, len(shuf)
folds = [shuf[i*9:(i+1)*9] for i in range(6)]
fold_of = {}
for i, f in enumerate(folds):
    for b in f: fold_of[b] = i
P("fold behavior counts:", [len(f) for f in folds])
P("behaviors in >1 fold:", 0 if len(fold_of) == len(bids) else "VIOLATION")
P("fold row counts S:", [sum(1 for r in S if fold_of[r['bid']] == i) for i in range(6)])
P("fold row counts P:", [sum(1 for r in Pset if fold_of[r['bid']] == i) for i in range(6)])
P("fold harmful counts P:", [sum(r['y'] for r in Pset if fold_of[r['bid']] == i) for i in range(6)])

# --- design matrix ---
def design(data, dims):
    cols, names = [], []
    n = len(data)
    if "relevance" in dims:
        for lv in REL[1:]:
            cols.append(np.array([1.0 if r["relevance"] == lv else 0.0 for r in data])); names.append("rel=" + lv)
    if "task" in dims:
        for lv in TASK[1:]:
            cols.append(np.array([1.0 if r["task"] == lv else 0.0 for r in data])); names.append("task=" + lv)
    if "stance" in dims:
        for lv in STANCE[1:]:
            cols.append(np.array([1.0 if r["stance"] == lv else 0.0 for r in data])); names.append("stance=" + lv)
    if "quality" in dims:
        cols.append(np.array([r["q"] for r in data], dtype=float)); names.append("quality")
    X = np.column_stack(cols) if cols else np.zeros((n, 0))
    return X, names

def oof_pred(data, dims, std_all=False):
    X, names = design(data, dims)
    y = np.array([r["y"] for r in data])
    g = np.array([fold_of[r["bid"]] for r in data])
    pred = np.full(len(data), np.nan)
    for i in range(6):
        te = g == i; tr = ~te
        Xtr, Xte = X[tr].copy(), X[te].copy()
        # standardize: quality always; others only if std_all
        for j, nm in enumerate(names):
            if nm == "quality" or std_all:
                mu, sd = Xtr[:, j].mean(), Xtr[:, j].std()
                if sd == 0: sd = 1.0
                Xtr[:, j] = (Xtr[:, j] - mu) / sd
                Xte[:, j] = (Xte[:, j] - mu) / sd
        m = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=5000)
        m.fit(Xtr, y[tr])
        pred[te] = m.predict_proba(Xte)[:, 1]
    return pred, y, names

def run_set(data, dims, label, std_all=False):
    res = {}
    predf, y, names = oof_pred(data, dims, std_all)
    auc_full = roc_auc_score(y, predf)
    ll_full = log_loss(y, predf)
    base = np.full(len(y), y.mean())
    ll_base = log_loss(y, base)
    P(f"\n=== {label} (n={len(y)}, dims={dims}, std_all={std_all}) ===")
    P(f"full-model out-of-fold AUC: {auc_full:.4f}")
    P(f"full-model out-of-fold log-loss: {ll_full:.4f}   intercept-only log-loss: {ll_base:.4f}")
    res["auc_full"] = auc_full; res["logloss_full"] = ll_full; res["logloss_base"] = ll_base
    res["delta"] = {}; res["marginal"] = {}
    for d in dims:
        rest = [x for x in dims if x != d]
        pr, _, _ = oof_pred(data, rest, std_all)
        a_rest = roc_auc_score(y, pr)
        pm, _, _ = oof_pred(data, [d], std_all)
        a_marg = roc_auc_score(y, pm)
        res["delta"][d] = auc_full - a_rest
        res["marginal"][d] = a_marg
        P(f"  {d:<10} AUC(full minus {d}) = {a_rest:.4f}   unique dAUC = {auc_full-a_rest:+.4f}   marginal AUC alone = {a_marg:.4f}")
    # full-data (non-CV) coefficients, direction only
    X, names = design(data, dims)
    Xs = X.copy()
    for j, nm in enumerate(names):
        if nm == "quality" or std_all:
            mu, sd = Xs[:, j].mean(), Xs[:, j].std() or 1.0
            Xs[:, j] = (Xs[:, j] - mu) / sd
    m = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=5000).fit(Xs, y)
    P("  full-data coefficients (direction only):",
      ", ".join(f"{n}={c:+.4f}" for n, c in zip(names, m.coef_[0])), f", intercept={m.intercept_[0]:+.4f}")
    res["coef"] = dict(zip(names, [float(c) for c in m.coef_[0]]))
    res["oof_pred"] = predf; res["y"] = y; res["data"] = data
    return res

DIMS_P = ["relevance", "task", "stance", "quality"]
DIMS_S = ["relevance", "task", "stance"]
rp = run_set(Pset, DIMS_P, "SET P (primary)")
rs = run_set(S, DIMS_S, "SET S (secondary)")

P("\n--- sensitivity: standardize ALL features (ambiguity in 'on standardized features') ---")
rp2 = run_set(Pset, DIMS_P, "SET P std_all", std_all=True)
rs2 = run_set(S, DIMS_S, "SET S std_all", std_all=True)

P("\n--- sensitivity: drop the wg_harm==null rows entirely ---")
Pn = [r for r in Pset if r["wg_harm"] is not None]
Sn = [r for r in S if r["wg_harm"] is not None]
rp3 = run_set(Pn, DIMS_P, "SET P (null wg_harm dropped)")
rs3 = run_set(Sn, DIMS_S, "SET S (null wg_harm dropped)")

# --- descriptive cross-tabs on set S (all labelled rows) ---
P("\n=== CROSS-TABS: WildGuard harmful rate by class ===")
for dim, levels in (("relevance", REL), ("task", TASK), ("stance", STANCE)):
    for lv in levels:
        sub = [r for r in S if r[dim] == lv]
        n = len(sub); h = sum(r["y"] for r in sub)
        P(f"  S  {dim:<10} {lv:<10} n={n:<5} harmful={h:<5} rate={100.0*h/n if n else float('nan'):.4f}%" if n else f"  S  {dim:<10} {lv:<10} n=0")
for dim, levels in (("relevance", REL), ("task", TASK), ("stance", STANCE)):
    for lv in levels:
        sub = [r for r in Pset if r[dim] == lv]
        n = len(sub); h = sum(r["y"] for r in sub)
        P(f"  P  {dim:<10} {lv:<10} n={n:<5} harmful={h:<5} rate={100.0*h/n if n else float('nan'):.4f}%" if n else f"  P  {dim:<10} {lv:<10} n=0")

# quality distribution in P by outcome (descriptive)
qh = np.array([r["q"] for r in Pset if r["y"] == 1]); qu = np.array([r["q"] for r in Pset if r["y"] == 0])
P(f"  P quality mean | harmful: {qh.mean():.4f} (n={len(qh)});  unharmful: {qu.mean():.4f} (n={len(qu)})")

# --- Iron-Law tripwire ---
P("\n=== IRON-LAW TRIPWIRE (>= 0.98) ===")
trip = []
if rp["auc_full"] >= 0.98: trip.append(f"P full model {rp['auc_full']:.4f}")
if rs["auc_full"] >= 0.98: trip.append(f"S full model {rs['auc_full']:.4f}")
for lbl, r in (("P", rp), ("S", rs)):
    for d, v in r["marginal"].items():
        if v >= 0.98: trip.append(f"{lbl} marginal {d} {v:.4f}")
P("TRIPPED:" if trip else "not tripped", "; ".join(trip))

# --- optional bootstrap (behavior-level) on unique dAUC, set P ---
P("\n=== behavior-level bootstrap, 10000 resamples, seed 20260828 (set P) ===")
rng = random.Random(20260828)
by_bid = collections.defaultdict(list)
for i, r in enumerate(Pset): by_bid[r["bid"]].append(i)
predsets = {"full": rp["oof_pred"]}
for d in DIMS_P:
    pr, _, _ = oof_pred(Pset, [x for x in DIMS_P if x != d])
    predsets[d] = pr
yP = rp["y"]
boots = {d: [] for d in DIMS_P}
bidlist = sorted(by_bid)
for b in range(10000):
    samp = [rng.choice(bidlist) for _ in range(len(bidlist))]
    idx = np.concatenate([by_bid[x] for x in samp])
    yy = yP[idx]
    if yy.min() == yy.max(): continue
    af = roc_auc_score(yy, predsets["full"][idx])
    for d in DIMS_P:
        boots[d].append(af - roc_auc_score(yy, predsets[d][idx]))
for d in DIMS_P:
    a = np.sort(np.array(boots[d]))
    P(f"  unique dAUC({d}) = {rp['delta'][d]:+.4f}  95% CI [{np.percentile(a,2.5):+.4f}, {np.percentile(a,97.5):+.4f}]  (n_boot={len(a)})")

open(SCRATCH + "/verify_s13d/out.txt", "w").write("\n".join(log) + "\n")
import sklearn
P("\nversions: numpy", np.__version__, "sklearn", sklearn.__version__, "python", sys.version.split()[0])
