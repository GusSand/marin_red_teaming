#!/usr/bin/env python
"""Merge a LoRA adapter into its base model and save a full model dir, so the pinned
safety-eval harness (which loads a model by path) can evaluate the attacked checkpoint.
Temporary: scripts/tamper_run.sh deletes the merged dir right after its ASR eval."""
import argparse, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--adapter", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

tok = AutoTokenizer.from_pretrained(a.base)
base = AutoModelForCausalLM.from_pretrained(a.base, torch_dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, a.adapter).merge_and_unload()
merged.save_pretrained(a.out)
tok.save_pretrained(a.out)
print("merged ->", a.out)
