#!/usr/bin/env python3
"""LABEL COMPLETION (not a rerun): re-judge the non-empty responses that WildGuard left
unlabelled, with the IDENTICAL pinned judge and configuration used by harmbench:default.

    python scripts/rejudge_missing.py --labels <dir> --prefix <prefix> [--all-categories]

Identity with the production path (evaluation/tasks/generation/harmbench/__init__.py @060cc903):
  - classifier: load_classifier_model("WildGuard") with default kwargs (ephemeral vLLM
    subprocess, tokenizer_mode="slow", max_tokens=128, temperature=0.0, top_p=1.0)
  - judge input: {"prompt": Behavior, or ContextString + "\\n\\n---\\n\\n" + Behavior for contextual
    rows; "response": the stored `response` field, which is the text the judge originally saw}
  - same pinned weights: HF_HUB_OFFLINE=1, allenai/wildguard from the workspace cache.
Only the batch composition differs (the unlabelled rows alone instead of all 320).

The original all.json is NEVER modified. Results go to a sidecar `rejudge.json` next to it,
holding for each row: id, BehaviorID, the original (None) labels, the new labels, the parse flag,
and judge provenance. Downstream analysis merges the sidecar explicitly (--use-rejudge).
Prints counts only; no response text.
"""
import argparse, json, os, socket, subprocess, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("SAFETY_EVAL_DIR", "."))
from src.classifier_models.loader import load_classifier_model  # noqa: E402

MISINFO = "misinformation_disinformation"


def judge_input(row):
    if row["FunctionalCategory"] != "contextual":
        return {"prompt": row["Behavior"], "response": row["response"]}
    return {"prompt": row["ContextString"] + "\n\n---\n\n" + row["Behavior"], "response": row["response"]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--labels", required=True); ap.add_argument("--prefix", required=True)
    ap.add_argument("--all-categories", action="store_true", help="re-judge every unlabelled non-empty row, not only the misinfo subset")
    a = ap.parse_args()
    runs = sorted(Path(a.labels).glob(f"{a.prefix}-*-harmbench-s*"))
    todo = []  # (rundir, row_index, row)
    for rd in runs:
        raw = json.load(open(rd / "all.json"))
        rows = raw if isinstance(raw, list) else next(v for v in raw.values() if isinstance(v, list))
        for i, r in enumerate(rows):
            if r.get("response_harmfulness") is not None: continue
            if not str(r.get("response") or "").strip(): continue
            if not a.all_categories and r.get("SemanticCategory") != MISINFO: continue
            todo.append((rd, i, r))
    print(f"unlabelled non-empty rows to re-judge: {len(todo)} across {len({t[0] for t in todo})} runs")
    if not todo:
        return
    judge_sha = Path(os.environ["HF_HOME"], "hub/models--allenai--wildguard/refs/main").read_text().strip()
    clf = load_classifier_model("WildGuard")
    outs = clf.classify([judge_input(r) for _, _, r in todo])
    prov = {"judge": "WildGuard", "judge_snapshot": judge_sha, "classifier_kwargs": "default (ephemeral vLLM, slow tokenizer, max_tokens=128, temperature=0.0, top_p=1.0)",
            "hostname": socket.gethostname(), "gpu": subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,uuid", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip(),
            "slurm_job": os.environ.get("SLURM_JOB_ID"), "batch_note": "re-judged rows batched alone; production judged all 320 rows of a run together"}
    by_run = {}
    for (rd, i, r), o in zip(todo, outs):
        d = o.asdict()
        by_run.setdefault(rd, []).append({"row_index": i, "id": r["id"], "BehaviorID": r["BehaviorID"], "SemanticCategory": r["SemanticCategory"],
            "original": {"response_harmfulness": r.get("response_harmfulness"), "response_refusal": r.get("response_refusal"), "is_parsing_error": r.get("is_parsing_error")},
            "rejudged": {"response_harmfulness": d.get("response_harmfulness"), "response_refusal": d.get("response_refusal"), "prompt_harmfulness": d.get("prompt_harmfulness"), "is_parsing_error": d.get("is_parsing_error")}})
    n_lab = n_perr = 0
    for rd, items in by_run.items():
        (rd / "rejudge.json").write_text(json.dumps({"provenance": prov, "rows": items}, indent=2))
        for it in items:
            n_lab += it["rejudged"]["response_harmfulness"] is not None; n_perr += bool(it["rejudged"]["is_parsing_error"])
    print(f"wrote {len(by_run)} sidecars; labelled {n_lab}/{len(todo)}; still parse-error {n_perr}/{len(todo)}")
    for rd, items in sorted(by_run.items()):
        print(" ", rd.name, "->", [(it["rejudged"]["response_harmfulness"], it["rejudged"]["response_refusal"]) for it in items])


if __name__ == "__main__":
    main()
