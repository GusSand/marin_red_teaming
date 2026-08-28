#!/usr/bin/env python3
"""Preflight for Torch GPU jobs. Prints DRY RUN OK, or fails loudly.

    cd $SCRATCH/marin-red-teaming/safety-eval && python ../scripts/dry_run_check.py

Ported from safety-decay/scripts/dry_run_check.py on 2026-08-27, with the checks
specialised to THIS project's failure history. Every check below corresponds to a
failure that actually happened here or in the sibling repo. Add to it whenever a new
failure class costs a GPU job.

A minute of CPU beats a queue wait plus a dead job.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WORK = Path(os.environ.get("MARIN_RT_ROOT",
                           Path(os.environ.get("SCRATCH", "/scratch/gs157")) / "marin-red-teaming"))
ROOT = WORK / "repro-olmo3-safety"
SE = ROOT / "safety-eval"
PINNED_SHA = "060cc903d64703214c549b5c3a30ea8ceef2e588"

fail = []


def check(name, fn):
    try:
        msg = fn()
    except Exception as exc:  # noqa: BLE001 - preflight reports, never raises
        fail.append(f"{name}: {type(exc).__name__}: {exc}")
        print(f"  FAIL  {name}: {exc}")
        return
    print(f"  ok    {name}{f' ({msg})' if msg else ''}")


# Protocol pins. These are not cosmetic: the 07-28/07-29 runs this experiment reproduces were
# produced on exactly these versions (runs/*/provenance.json). A fresh resolve after a scratch
# flush pulls transformers 5.x, which changes tokenizer/generation behaviour and shifts numbers
# by more than the reproduction tolerance WITHOUT crashing. Caught by hand on 2026-08-27; this
# check exists so it is never caught by hand again.
PINS = {"torch": "2.8.0", "vllm": "0.11.0", "transformers": "4.57.1"}


def c_imports():
    import torch
    import vllm
    import transformers
    got = {"torch": torch.__version__.split("+")[0],
           "vllm": vllm.__version__,
           "transformers": transformers.__version__}
    bad = [f"{k}: got {v}, pinned {PINS[k]}" for k, v in got.items() if v != PINS[k]]
    if bad:
        raise RuntimeError("protocol pin violated -> " + "; ".join(bad))
    return ", ".join(f"{k} {v}" for k, v in got.items())


def c_gpu():
    """Non-fatal: preflight runs on a login node, which has no GPU by design."""
    import torch
    if not torch.cuda.is_available():
        return "no CUDA here (expected on a login node)"
    n = torch.cuda.get_device_name(0)
    gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
    return f"{n}, {gb:.0f}GB"


def c_harness_sha():
    sha = subprocess.check_output(["git", "-C", str(SE), "rev-parse", "HEAD"], text=True).strip()
    if sha != PINNED_SHA:
        raise RuntimeError(f"safety-eval at {sha[:12]}, expected pinned {PINNED_SHA[:12]}")
    return sha[:12]


def c_seed_patch():
    """The seed patch is the one whose absence is SILENT and corrupting.

    Without it PYTHONHASHSEED does not reach vLLM's sampler, so N seeds collapse to
    one set of outputs wherever generation is stable. That understates every CI and
    fabricates tight distributions. It already happened once on this project
    (starling / deeper-starling, INBOX 2026-07-29).
    """
    src = (SE / "src" / "generation_utils.py").read_text()
    if "SAFETYEVAL_SAMPLING_SEED" not in src:
        raise RuntimeError(
            "seed patch NOT applied. Run: "
            "git -C safety-eval apply $MARIN_RT_WORK/scripts/patches/seed_fix_generation_utils.patch"
        )
    return "applied"


def c_venv_portable():
    """The venv must resolve to the same interpreter on login AND compute nodes.

    Torch's login node has /usr/bin/python3 = 3.12; the l40s compute nodes have 3.9. A stock
    venv symlinks bin/python3 -> /usr/bin/python3, which silently becomes 3.9 inside a job and
    makes every installed package invisible. Job 16488571 died on exactly this.
    """
    link = SE.parent / ".venv-safety-eval" / "bin" / "python3"
    target = os.readlink(link) if link.is_symlink() else str(link)
    if not os.path.isabs(target) or "python3." not in os.path.basename(target):
        raise RuntimeError(
            f"venv bin/python3 -> {target}; must be an ABSOLUTE versioned path "
            "(e.g. /usr/bin/python3.12) or it resolves to 3.9 on compute nodes"
        )
    return target


def c_openai_key():
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY unset; safety-eval constructs a client at import time")
    return "set (dummy is fine)"


def c_base_template():
    t = ROOT / "config" / "base_template_v2.txt"
    if not t.exists():
        raise RuntimeError(f"missing base scaffold {t}")
    body = t.read_text()
    if "{instruction}" not in body:
        raise RuntimeError("base scaffold has no {instruction} placeholder")
    # base_template.txt (v1) is bare "{instruction}" and also passes the test above. v1 is the
    # template that produced the prompt-echo confound: the base model repeats the harmful
    # instruction and WildGuard scores the echo as compliance. A v1 file sitting at the v2
    # filename would produce a complete, plausible, invalid run.
    for marker in ("User:", "Assistant:"):
        if marker not in body:
            raise RuntimeError(
                f"scaffold at {t} lacks {marker!r}; that is the v1 bare template, "
                "which reinstates the prompt-echo confound"
            )
    return "base_template_v2.txt (User:/Assistant: scaffold present)"


def c_no_paperspace():
    """32 hardcoded /home/paperspace paths existed before the Torch port."""
    scripts_dir = WORK / "scripts"
    if not scripts_dir.is_dir():
        raise RuntimeError(f"{scripts_dir} does not exist; the tree was never rsynced here")
    out = subprocess.run(
        ["grep", "-rn", "--include=*.sh", "--include=*.py",
         "--exclude=dry_run_check.py",  # this file discusses the path in comments
         "/home/paperspace", str(WORK / "scripts")],
        capture_output=True, text=True,
    ).stdout.splitlines()
    # A mention inside a MARIN_RT_ROOT default is fine; a real path is not.
    real = [ln for ln in out if "MARIN_RT_ROOT" not in ln]
    if real:
        raise RuntimeError(f"{len(real)} live /home/paperspace path(s), first: {real[0][:120]}")
    return "clean"


def c_judge_cached():
    """WildGuard (the judge) is a GATED HF repo with no token on Torch, so the jobs run OFFLINE
    against a local copy. Generation ran fine without it and the job died 5 GPU-minutes in at the
    judge step (job 16489489). Verify the judge weights are actually on disk before submitting.
    """
    hub = Path(os.environ.get("HF_HOME", WORK / "hf_cache")) / "hub" / "models--allenai--wildguard"
    snaps = hub / "snapshots"
    if not snaps.is_dir():
        raise RuntimeError(f"WildGuard not cached at {hub}; jobs run HF_HUB_OFFLINE and cannot fetch it")
    shards = list(snaps.glob("*/model-*.safetensors"))
    resolved = [s for s in shards if s.exists()]  # follow symlinks into blobs/
    if len(resolved) < 2:
        raise RuntimeError(f"WildGuard cache at {hub} is incomplete: {len(resolved)} weight shard(s) resolve")
    return f"{len(resolved)} shards cached, offline OK"


def c_hf_cache():
    home = os.environ.get("HF_HOME")
    if not home:
        raise RuntimeError("HF_HOME unset; downloads would land in the home quota, not $SCRATCH")
    Path(home).mkdir(parents=True, exist_ok=True)
    return home


def c_disk():
    """Quota, not filesystem free space.

    os.statvfs reports the whole 5TB vast scratch filesystem, so it never fires no matter what
    threshold is set. What actually binds is the per-user quota. Six 8B checkpoints at ~16GB
    plus a 7B judge is ~110GB, so the old 80GB threshold was below its own error message.
    """
    need_gb = 110
    try:
        q = subprocess.run(["myquota"], capture_output=True, text=True, timeout=30).stdout
        m = re.search(r"/scratch\s+\S+\s+\S+\s+([\d.]+)TB/\S+\s+(\d+)GB", q)
        if m:
            total_gb, used_gb = float(m.group(1)) * 1024, float(m.group(2))
            free_gb = total_gb - used_gb
            if free_gb < need_gb:
                raise RuntimeError(f"scratch quota: only {free_gb:.0f}GB of headroom, need ~{need_gb}GB")
            return f"{free_gb:.0f}GB of quota headroom"
    except FileNotFoundError:
        pass
    st = os.statvfs(WORK)
    return f"{st.f_bavail * st.f_frsize / 1024**3:.0f}GB on the filesystem (quota NOT checked)"


print("preflight: marin_red_teaming on Torch")
check("python imports", c_imports)
check("gpu visible", c_gpu)
check("safety-eval pinned sha", c_harness_sha)
check("SEED PATCH applied", c_seed_patch)
check("venv node-portable", c_venv_portable)
check("OPENAI_API_KEY", c_openai_key)
check("base scaffold", c_base_template)
check("no paperspace paths", c_no_paperspace)
check("judge cached (offline)", c_judge_cached)
check("HF_HOME", c_hf_cache)
check("scratch disk", c_disk)

if fail:
    print(f"\n{len(fail)} check(s) failed. NOT submitting.", file=sys.stderr)
    sys.exit(1)
print("\nDRY RUN OK")
