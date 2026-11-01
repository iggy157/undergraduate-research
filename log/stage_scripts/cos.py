import json, numpy as np, glob
D="hidden/out/"
def load(pat):
    f=glob.glob(D+pat+"*.index.json")[0]; idx=json.load(open(f)); h=np.load(f.replace(".index.json",".npz"))["h"].astype(np.float32); return idx,h
bi,bh=load("aiwolf_0001__single-batch__"); si,sh=load("aiwolf_0001__single-batch-stepped__"); oi,oh=load("aiwolf_0001__single-online__"); mi,mh=load("aiwolf_0001__multi-public__"); pi,ph=load("aiwolf_0001__multi-private__")
print("layers", bi["layers"], "h shape", bh.shape, sh.shape, oh.shape)
def cos(a,b): return float((a*b).sum()/ (np.linalg.norm(a)*np.linalg.norm(b)+1e-9))
bp=bi["positions"]; sp=si["positions"]
print("batch kinds", {p["kind"] for p in bp}, "stepped kinds", {p["kind"] for p in sp}, "online kinds", {p["kind"] for p in oi["positions"]})
print("batch labels[:8]", [p["label"] for p in bp[:8]]); print("stepped labels[:8]", [p["label"] for p in sp[:8]])
print("batch n_tokens", bp[0]["n_tokens"], "stepped n_tokens first/last", sp[0]["n_tokens"], sp[-1]["n_tokens"])
L=bi["layers"]
for i in range(min(len(bp),len(sp))):
    cs=[cos(bh[i,l],sh[i,l]) for l in range(len(L))]
    print(f"pos {i:2d} {bp[i]['label']:18} / {sp[i]['label']:18} tokpos {bp[i]['pos']:5d}/{sp[i]['pos']:5d} cos min {min(cs):.4f} last {cs[-1]:.4f} mid {cs[len(L)//2]:.4f}")
# online label-kind positions vs batch
ol=[p for p in oi["positions"] if p["kind"]=="label"]; opr=[p for p in oi["positions"] if p["kind"]=="prompt"]
oh_l=oh[[k for k,p in enumerate(oi["positions"]) if p["kind"]=="label"]]; oh_p=oh[[k for k,p in enumerate(oi["positions"]) if p["kind"]=="prompt"]]
print("online label tokens (decoded?) labels[:5]", [p["label"] for p in ol[:5]], "n", len(ol))
for i in [0,1,2,5,10,20,30,40]:
    if i<len(ol) and i<len(bp):
        cs=[cos(bh[i,l],oh_l[i,l]) for l in range(len(L))]; cp=[cos(bh[i,l],oh_p[i,l]) for l in range(len(L))]
        print(f"batch vs online pos {i:2d} {bp[i]['label']:18}/{ol[i]['label']:18} label-cos last {cs[-1]:.3f} min {min(cs):.3f} ; prompt-pos cos last {cp[-1]:.3f}")
# label vs prompt within online (how different are the two positions)
for i in [0,10,30]:
    cs=[cos(oh_l[i,l],oh_p[i,l]) for l in range(len(L))]; print(f"online label vs prompt pos {i}: cos last {cs[-1]:.3f} min {min(cs):.3f}")
# multi-public vs multi-private vs online at prompt position
mp=[k for k,p in enumerate(mi["positions"]) if p["kind"]=="prompt"]; pp=[k for k,p in enumerate(pi["positions"]) if p["kind"]=="prompt"]
for i in [0,10,30]:
    print(f"public vs private prompt pos {i}: cos last {cos(mh[mp[i],-1],ph[pp[i],-1]):.3f}; online vs public {cos(oh_p[i,-1],mh[mp[i],-1]):.3f}")
# check the index 'checks' and that stepped positions pos == n_tokens-1
print("stepped pos==n_tokens-1:", all(p["pos"]==p["n_tokens"]-1 for p in sp), "checks all ok:", all(all(p["checks"].values()) for p in sp+bp+oi["positions"]))
