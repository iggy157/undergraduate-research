import json, glob, os, sys, collections
root="log/_pilot5"
def rows(sid, cond):
    dom = sid.rsplit("_",1)[0]
    ds = sorted(glob.glob(f"{root}/{dom}/{cond.split('-process')[0]}/{sid}__{cond}__*"))
    gid=os.path.basename(ds[0])
    return [json.loads(l) for l in open(f"{ds[0]}/{gid}.jsonl")]
sid=sys.argv[1]
for cond in ["single-batch","single-batch-stepped","single-online","multi-public","multi-private"]:
    calls=[r for r in rows(sid,cond) if r.get("kind")=="llm_call"]
    print("="*10, cond, "calls", len(calls))
    # stop / finish / max tokens stats
    st=collections.Counter(); fr=collections.Counter(); comp=collections.defaultdict(int)
    for c in calls:
        st[(c.get("request"), json.dumps(c.get("stop")))]+=1
        fr[c.get("finish_reason")]+=1
        u=c.get("usage") or {}
        k=c.get("request") or "FULL"
        comp[k]=max(comp[k], u.get("completion_tokens",0) or 0)
    print(" stop by request:", dict(st)); print(" finish:", dict(fr), " max completion tokens by request:", dict(comp))
    # show first TALK, first VOTE, first ACTION message (user and assistant) of seat 1 (or the single call)
    shown=set()
    for c in calls:
        key=c.get("request") or "FULL"
        if key in shown: continue
        if c.get("seat") not in (None,1) and cond!="single-online": continue
        shown.add(key)
        m=c["messages"]
        print(f"--- {key} seat={c.get('seat')} round={c.get('round')} turn={c.get('turn')} seq={c.get('seq')}")
        for mm in m[1:]:
            txt=mm["content"]
            print(f"[{mm['role']}] ({len(txt)} chars)")
            lines=txt.splitlines()
            if len(lines)>30: print("\n".join(lines[:12])); print("   ..."); print("\n".join(lines[-14:]))
            else: print(txt)
        print("[response]", repr((c.get("response") or "")[:200]))
