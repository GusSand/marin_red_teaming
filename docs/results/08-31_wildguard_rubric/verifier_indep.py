# Second independent path: hand-rolled L2 logistic regression (Newton/IRLS) + rank-based AUC.
import json, random, numpy as np, collections
S="/private/tmp/claude-502/-Users-gus-github-marin-red-teaming/8390c64d-9dab-48a3-934e-802b67381284/scratchpad"
key=json.load(open(S+"/labels/key.json"))["items"]
J={}
for l in open(S+"/labels/claude_fable_pass2.jsonl"):
    l=l.strip()
    if l: r=json.loads(l); J[r["cid"]]=r
REL=["on_topic","partial","off_topic"];TASK=["complete","partial","no_attempt"];ST=["endorses","refuses","corrects","hedges"]
rows=[]
for cid in sorted(J):
    r=J[cid];k=key[cid]
    vs=[r["specificity"],r["coherence"],r["persuasiveness"]]
    q=None if any(v is None for v in vs) else sum(vs)/3
    rows.append((k["BehaviorID"],1 if k["wg_harm"]=="harmful" else 0,r["relevance"],r["task"],r["stance"],q))
Pset=[r for r in rows if r[5] is not None]
bids=sorted({r[0] for r in rows}); sh=list(bids); random.Random(20260828).shuffle(sh)
fo={b:i//9 for i,b in enumerate(sh)}
def auc(y,s):  # Mann-Whitney with tie handling, no sklearn
    y=np.asarray(y);s=np.asarray(s);o=np.argsort(s,kind="mergesort");sv=s[o]
    rk=np.empty(len(s));i=0
    while i<len(s):
        j=i
        while j+1<len(s) and sv[j+1]==sv[i]: j+=1
        rk[o[i:j+1]]=(i+j)/2.0+1; i=j+1
    n1=y.sum();n0=len(y)-n1
    return (rk[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
def X_of(data,dims):
    c=[]
    if "relevance" in dims: c+=[[1.0 if r[2]==lv else 0.0 for r in data] for lv in REL[1:]]
    if "task" in dims: c+=[[1.0 if r[3]==lv else 0.0 for r in data] for lv in TASK[1:]]
    if "stance" in dims: c+=[[1.0 if r[4]==lv else 0.0 for r in data] for lv in ST[1:]]
    if "quality" in dims: c+=[[r[5] for r in data]]
    return np.array(c,dtype=float).T if c else np.zeros((len(data),0))
def fit(X,y,C=1.0,it=200):
    n,p=X.shape; Xb=np.hstack([np.ones((n,1)),X]); w=np.zeros(p+1); lam=1.0/C
    for _ in range(it):
        z=Xb@w; mu=1/(1+np.exp(-z)); W=np.clip(mu*(1-mu),1e-10,None)
        g=Xb.T@(mu-y); g[1:]+=lam*w[1:]
        H=Xb.T@(Xb*W[:,None]); H[1:,1:]+=lam*np.eye(p); H+=1e-9*np.eye(p+1)
        step=np.linalg.solve(H,g); w-=step
        if np.max(np.abs(step))<1e-10: break
    return w
def oof(data,dims):
    X=X_of(data,dims); y=np.array([r[1] for r in data]); g=np.array([fo[r[0]] for r in data]); pr=np.zeros(len(data))
    for i in range(6):
        te=g==i;tr=~te; Xtr=X[tr].copy();Xte=X[te].copy()
        if "quality" in dims:
            j=Xtr.shape[1]-1; m,s=Xtr[:,j].mean(),Xtr[:,j].std() or 1.0
            Xtr[:,j]=(Xtr[:,j]-m)/s; Xte[:,j]=(Xte[:,j]-m)/s
        w=fit(Xtr,y[tr]); pr[te]=1/(1+np.exp(-(np.hstack([np.ones((Xte.shape[0],1)),Xte])@w)))
    return pr,y
for name,data,dims in [("P",Pset,["relevance","task","stance","quality"]),("S",rows,["relevance","task","stance"])]:
    pr,y=oof(data,dims); af=auc(y,pr)
    print(f"[indep] set {name} n={len(y)} full AUC={af:.4f}")
    for d in dims:
        p2,_=oof(data,[x for x in dims if x!=d]); p3,_=oof(data,[d])
        print(f"   {d:<10} dAUC={af-auc(y,p2):+.4f}  marginal={auc(y,p3):.4f}")
