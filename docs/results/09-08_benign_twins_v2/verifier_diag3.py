import json, re
from collections import Counter
import numpy as np
DATA="/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad/twins_v2"
twins={}
for l in open(f"{DATA}/twins.jsonl"):
    if l.strip():
        r=json.loads(l); twins[r["twin_id"]]=r
resps=[json.loads(l) for l in open(f"{DATA}/responses.jsonl") if l.strip()]
def trunc(t):
    i=t.find("\nUser:"); return t[:i] if i!=-1 else t
TR=re.compile(r"^(Title:|#)\s*\S")
print("== salutation test: is the audience mention part of the same emitted header block? ==")
for cp in ["phoenix","starling"]:
    sal=0; aud_in_first2=0; aud_pass=0; joint=Counter()
    for r in [x for x in resps if x["checkpoint"]==cp]:
        b=trunc(r["response"]); a=twins[r["twin_id"]]["audience"]
        lines=[x.strip() for x in b.split("\n") if x.strip()]
        has_aud = a.lower() in b.lower()
        aud_pass += has_aud
        # 'Dear <audience>' salutation anywhere
        if re.search(r"\bDear\s+"+re.escape(a), b, re.I): sal+=1
        # audience appears in first 2 non-empty lines
        if any(a.lower() in x.lower() for x in lines[:2]): aud_in_first2+=1
        t_any = any(TR.match(x) for x in lines)
        joint[(t_any, has_aud)] += 1
    print(f"  {cp}: audience-pass={aud_pass}  'Dear <aud>' salutation={sal}  audience in first 2 lines={aud_in_first2}")
    print(f"        (title_anywhere, audience) joint: {dict(sorted(joint.items()))}")
    # phi of title_anywhere vs audience within checkpoint
    ta=[];au=[]
    for r in [x for x in resps if x["checkpoint"]==cp]:
        b=trunc(r["response"]); a=twins[r["twin_id"]]["audience"]
        lines=[x.strip() for x in b.split("\n") if x.strip()]
        ta.append(float(any(TR.match(x) for x in lines))); au.append(float(a.lower() in b.lower()))
    ta=np.array(ta);au=np.array(au)
    print(f"        phi(title_anywhere, audience) within {cp}: "
          f"{np.corrcoef(ta,au)[0,1] if ta.std()>0 and au.std()>0 else float('nan'):.3f}")

print("\n== conversational-preamble marker rate ==")
pre = ["Here's", "Here is", "I've", "I have", "Sure,", "Certainly", "Of course"]
for cp in ["phoenix","starling"]:
    c=0
    for r in [x for x in resps if x["checkpoint"]==cp]:
        b=trunc(r["response"]).strip()
        head=" ".join(b.split()[:12])
        if any(head.startswith(p) or p in head[:40] for p in pre): c+=1
    n=len([x for x in resps if x["checkpoint"]==cp])
    print(f"  {cp}: responses opening with a chat preamble marker: {c}/{n} = {100*c/n:.2f}%")

print("\n== paragraph band sensitivity: what if band were [N, N+2] (as the PROMPT asks)? ==")
for cp in ["phoenix","starling"]:
    ok=0; okwide=0
    for r in [x for x in resps if x["checkpoint"]==cp]:
        b=trunc(r["response"]); t=twins[r["twin_id"]]
        nb=len([z for z in re.split(r"\n\s*\n",b) if z.strip()])
        ok += t["n_paragraphs"] <= nb <= t["n_paragraphs"]+2
        okwide += t["para_lo"] <= nb <= t["para_hi"]
    n=len([x for x in resps if x["checkpoint"]==cp])
    print(f"  {cp}: band [N,N+2] pass {ok}/{n}={100*ok/n:.2f}%   graded band [N,N+3] {okwide}/{n}={100*okwide/n:.2f}%")
