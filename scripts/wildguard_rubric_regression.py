#!/usr/bin/env python3
"""Stage 1, S1-3D: which rubric dimension does WildGuard's `harmful` label track?

Pre-registration: docs/experiments/08-31_wildguard_rubric-dimension-regression.md (frozen 2026-08-31,
commit f4b2eac). Observational, CPU only, no new labels.

Outcome  y = 1 iff key.items[cid].wg_harm == "harmful".
Predictors from the pass-2 blind Claude rubric labels:
  relevance (one-hot, ref on_topic) | task (one-hot, ref complete) |
  stance (one-hot, ref endorses)    | quality = mean(specificity, coherence, persuasiveness), standardized.

Primary metric: unique out-of-fold AUC contribution per dimension, 6-fold CV grouped by BehaviorID
(fold assignment = sorted BehaviorIDs shuffled once with Random(20260828), six contiguous blocks of 9).
Uncertainty: 10k behavior-level bootstrap over fixed out-of-fold predictions, percentile 95% CI.

Aggregate statistics only. Never reads items.jsonl; no response text is touched.

Usage:
  wildguard_rubric_regression.py --labels <dir with key.json and claude_fable_pass2.jsonl> --out <dir>
"""
import argparse, json, random, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

SEED = 20260828
NBOOT = 10000
NFOLD = 6
MATERIALITY = 0.02
IRON_LAW_AUC = 0.98

VOCAB = {
    "relevance": ["on_topic", "partial", "off_topic"],
    "task": ["complete", "partial", "no_attempt"],
    "stance": ["refuses", "corrects", "hedges", "endorses"],
}
REF = {"relevance": "on_topic", "task": "complete", "stance": "endorses"}
QUALITY = ("specificity", "coherence", "persuasiveness")
DIMS = ["relevance", "task", "stance", "quality"]

ap = argparse.ArgumentParser()
ap.add_argument("--labels", required=True, help="dir holding key.json and claude_fable_pass2.jsonl")
ap.add_argument("--out", required=True)
a = ap.parse_args()

L = Path(a.labels)
key = json.loads((L / "key.json").read_text())["items"]
judge = {}
for line in (L / "claude_fable_pass2.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    if r["cid"] in judge:
        sys.exit(f"duplicate cid in judge file: {r['cid']}")
    judge[r["cid"]] = r

gates = {}
gates["n_key"] = len(key)
gates["n_judge"] = len(judge)
gates["judge_cids_missing_from_key"] = sorted(set(judge) - set(key))
gates["key_cids_without_judge_label"] = len(set(key) - set(judge))


def qmean(r):
    v = [r.get(k) for k in QUALITY]
    return None if any(x is None or x == "" for x in v) else float(np.mean([float(x) for x in v]))


# ---- gates: label vocabulary and the quality-null rule -----------------------------------------
bad_vocab, bad_quality_rule = Counter(), Counter()
for cid, r in judge.items():
    for dim in VOCAB:
        if r.get(dim) not in VOCAB[dim]:
            bad_vocab[f"{dim}={r.get(dim)!r}"] += 1
    has_q = qmean(r) is not None
    if r.get("task") == "no_attempt" and has_q:
        bad_quality_rule["no_attempt_with_quality"] += 1
    if r.get("task") != "no_attempt" and not has_q:
        bad_quality_rule["attempted_without_quality"] += 1
gates["out_of_vocabulary_values"] = dict(bad_vocab)
gates["quality_null_rule_violations"] = dict(bad_quality_rule)

# Added 2026-08-31 after the independent verifier found it: some key items carry wg_harm == null.
# The frozen rule is "y = 1 iff harmful, else 0", so nulls score 0. Counting them here does not
# change the analysis; it stops the class being invisible, and drives the reported sensitivity.
gates["wg_harm_values"] = dict(Counter(k.get("wg_harm") for k in key.values()))
gates["n_wg_harm_null"] = sum(1 for k in key.values() if k.get("wg_harm") is None)

# ---- assemble rows ----------------------------------------------------------------------------
rows = []
for cid, k in sorted(key.items()):
    r = judge.get(cid)
    if r is None:
        continue
    rows.append({
        "cid": cid, "behavior": k["BehaviorID"], "run": k["run"],
        "y": 1 if k["wg_harm"] == "harmful" else 0,
        "relevance": r["relevance"], "task": r["task"], "stance": r["stance"],
        "q": qmean(r),
    })

S = rows                                    # secondary set: everything labelled
P = [r for r in rows if r["q"] is not None]  # primary set: quality defined

behaviors = sorted({r["behavior"] for r in rows})
gates["n_behaviors"] = len(behaviors)
gates["n_set_S"] = len(S)
gates["n_set_P"] = len(P)
gates["class_balance_S"] = {"harmful": sum(r["y"] for r in S), "unharmful": sum(1 - r["y"] for r in S)}
gates["class_balance_P"] = {"harmful": sum(r["y"] for r in P), "unharmful": sum(1 - r["y"] for r in P)}

# ---- frozen fold assignment -------------------------------------------------------------------
shuffled = list(behaviors)
random.Random(SEED).shuffle(shuffled)
blocks = [shuffled[i::NFOLD] for i in range(NFOLD)] if len(shuffled) % NFOLD else \
         [shuffled[i * (len(shuffled) // NFOLD):(i + 1) * (len(shuffled) // NFOLD)] for i in range(NFOLD)]
fold_of = {b: i for i, blk in enumerate(blocks) for b in blk}
gates["fold_sizes_behaviors"] = [len(b) for b in blocks]
gates["behavior_in_one_fold_only"] = len(fold_of) == len(behaviors)
assert gates["behavior_in_one_fold_only"]


def design(data, dims):
    """One-hot the categorical dims (reference level dropped) + standardized quality."""
    names, cols = [], []
    for dim in dims:
        if dim == "quality":
            q = np.array([r["q"] for r in data], float)
            mu, sd = q.mean(), q.std()
            cols.append(((q - mu) / sd if sd else q * 0.0).reshape(-1, 1))
            names.append("quality_z")
        else:
            for lvl in VOCAB[dim]:
                if lvl == REF[dim]:
                    continue
                cols.append(np.array([[1.0 if r[dim] == lvl else 0.0] for r in data]))
                names.append(f"{dim}={lvl}")
    X = np.hstack(cols) if cols else np.zeros((len(data), 0))
    return X, names


def oof_predictions(data, dims):
    """Out-of-fold P(harmful) under the frozen behavior-grouped folds."""
    X, _ = design(data, dims)
    y = np.array([r["y"] for r in data])
    folds = np.array([fold_of[r["behavior"]] for r in data])
    pred = np.zeros(len(data))
    for f in range(NFOLD):
        te = folds == f
        tr = ~te
        if len(set(y[tr])) < 2:                       # degenerate training fold
            pred[te] = y[tr].mean()
            continue
        m = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=5000)
        m.fit(X[tr], y[tr])
        pred[te] = m.predict_proba(X[te])[:, 1]
    return y, pred


def boot_ci(stat_fn, data, nboot=NBOOT):
    """Percentile 95% CI resampling the 54 BehaviorIDs with replacement, predictions held fixed."""
    by_beh = defaultdict(list)
    for i, r in enumerate(data):
        by_beh[r["behavior"]].append(i)
    behs = sorted(by_beh)
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(nboot):
        pick = rng.integers(0, len(behs), len(behs))
        idx = np.concatenate([by_beh[behs[j]] for j in pick])
        v = stat_fn(idx)
        if v is not None and np.isfinite(v):
            vals.append(v)
    if not vals:
        return [float("nan"), float("nan")]
    return [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)]


def safe_auc(y, p, idx=None):
    if idx is not None:
        y, p = y[idx], p[idx]
    return None if len(set(y)) < 2 else roc_auc_score(y, p)


def analyze(data, dims, name):
    y, pred_full = oof_predictions(data, dims)
    auc_full = safe_auc(y, pred_full)
    out = {
        "set": name, "n": len(data), "dims": dims,
        "harmful": int(y.sum()), "unharmful": int((1 - y).sum()),
        "auc_full": round(auc_full, 4),
        "auc_full_ci": boot_ci(lambda i: safe_auc(y, pred_full, i), data),
        "logloss_full": round(log_loss(y, pred_full), 4),
        "logloss_intercept_only": round(log_loss(y, np.full(len(y), y.mean())), 4),
        "unique": {}, "marginal": {},
    }
    for d in dims:
        rest = [x for x in dims if x != d]
        _, pred_rest = oof_predictions(data, rest) if rest else (y, np.full(len(y), y.mean()))
        auc_rest = safe_auc(y, pred_rest)
        out["unique"][d] = {
            "delta_auc": round(auc_full - auc_rest, 4),
            "auc_without": round(auc_rest, 4),
            "ci": boot_ci(lambda i: (lambda a, b: None if a is None or b is None else a - b)(
                safe_auc(y, pred_full, i), safe_auc(y, pred_rest, i)), data),
        }
        _, pred_only = oof_predictions(data, [d])
        auc_only = safe_auc(y, pred_only)
        out["marginal"][d] = {
            "auc_alone": round(auc_only, 4),
            "ci": boot_ci(lambda i: safe_auc(y, pred_only, i), data),
        }
    # descriptive, full-data (non-CV) coefficients: direction only
    X, names = design(data, dims)
    m = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=5000).fit(X, y)
    out["coefficients_full_data"] = {n: round(float(c), 3) for n, c in zip(names, m.coef_[0])}
    out["intercept_full_data"] = round(float(m.intercept_[0]), 3)
    return out


results = {
    "experiment": "docs/experiments/08-31_wildguard_rubric-dimension-regression.md",
    "seed": SEED, "nboot": NBOOT, "nfold": NFOLD,
    "materiality_delta_auc": MATERIALITY, "iron_law_auc": IRON_LAW_AUC,
    "versions": {"numpy": np.__version__, "sklearn": sklearn.__version__,
                 "python": sys.version.split()[0]},
    "gates": gates,
}

# ---- power gate decides whether the primary set is readable -------------------------------------
hp, up = gates["class_balance_P"]["harmful"], gates["class_balance_P"]["unharmful"]
results["power_gate_P"] = ("ok" if min(hp, up) >= 50 else
                           "underpowered" if min(hp, up) >= 30 else "not_reportable")

if results["power_gate_P"] != "not_reportable":
    results["primary"] = analyze(P, DIMS, "P (quality defined)")
results["secondary"] = analyze(S, ["relevance", "task", "stance"], "S (all labelled rows)")

# ---- descriptive cross-tabs ---------------------------------------------------------------------
ct = {}
for dim in VOCAB:
    ct[dim] = {}
    for lvl in VOCAB[dim]:
        sub = [r for r in S if r[dim] == lvl]
        ct[dim][lvl] = {"n": len(sub),
                        "harmful_rate_pct": round(100 * sum(r["y"] for r in sub) / len(sub), 2) if sub else None}
qb = {}
for lo, hi, lab in [(1.0, 2.0, "1.0-2.0"), (2.0, 3.0, "2.0-3.0"), (3.0, 4.0, "3.0-4.0"), (4.0, 5.01, "4.0-5.0")]:
    sub = [r for r in P if lo <= r["q"] < hi]
    qb[lab] = {"n": len(sub),
               "harmful_rate_pct": round(100 * sum(r["y"] for r in sub) / len(sub), 2) if sub else None}
ct["quality_bin"] = qb
results["crosstabs"] = ct

# Same cross-tabs restricted to the primary set, which is where the registered ranking is read.
# Reported because P is degenerate on two levels: relevance=off_topic and task=no_attempt are
# empty by construction, so P cannot speak to either.
ctP = {}
for dim in VOCAB:
    ctP[dim] = {}
    for lvl in VOCAB[dim]:
        sub = [r for r in P if r[dim] == lvl]
        ctP[dim][lvl] = {"n": len(sub),
                         "harmful_rate_pct": round(100 * sum(r["y"] for r in sub) / len(sub), 2) if sub else None}
results["crosstabs_primary_set"] = ctP
results["degenerate_levels_in_P"] = [f"{d}={l}" for d in VOCAB for l in VOCAB[d]
                                     if ctP[d][l]["n"] == 0]

# Pre-registered rule followed literally above. This is the declared sensitivity: drop null-outcome rows.
if gates["n_wg_harm_null"]:
    keep = {cid for cid, k in key.items() if k.get("wg_harm") is not None}
    Pn = [r for r in P if r["cid"] in keep]
    Sn = [r for r in S if r["cid"] in keep]
    results["sensitivity_drop_null_outcome"] = {
        "note": "rows with wg_harm == null excluded; registered analysis scores them 0",
        "primary": analyze(Pn, DIMS, "P minus null-outcome rows"),
        "secondary": analyze(Sn, ["relevance", "task", "stance"], "S minus null-outcome rows"),
    }

# ---- verdict against the pre-registered criteria --------------------------------------------------
def material(u):
    return u["delta_auc"] >= MATERIALITY and u["ci"][0] > 0

if "primary" in results:
    pr = results["primary"]
    mats = {d: material(pr["unique"][d]) for d in DIMS}
    dq, ds = pr["unique"]["quality"]["delta_auc"], pr["unique"]["stance"]["delta_auc"]
    if not any(mats.values()):
        verdict = "NULL — no dimension material"
    elif mats["quality"] and dq > ds:
        verdict = "QUALITY-LED — style-sensitivity live; recommend promoting S1-3C"
    elif mats["quality"]:
        verdict = "MIXED — quality material but not larger than stance"
    else:
        verdict = "SUBSTANCE-LED — quality not material; H1-as-judge-artifact not supported observationally"
    results["material"] = mats
    results["verdict"] = verdict
    results["iron_law_tripped"] = bool(pr["auc_full"] >= IRON_LAW_AUC or
                                       any(pr["marginal"][d]["auc_alone"] >= IRON_LAW_AUC for d in DIMS))

out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
(out / "wildguard_rubric_regression.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
