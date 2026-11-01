import json, glob, os, sys, difflib
sys.path.insert(0, os.getcwd())
root="log/_pilot5"
def load(sid, cond):
    dom = sid.rsplit("_",1)[0]
    ds = sorted(glob.glob(f"{root}/{dom}/{cond.split('-process')[0]}/{sid}__{cond}__*"))
    assert len(ds)==1, (sid,cond,ds)
    gid=os.path.basename(ds[0])
    rows=[json.loads(l) for l in open(f"{ds[0]}/{gid}.jsonl")]
    return rows
def calls(rows): return [r for r in rows if r.get("kind")=="llm_call" or r.get("type")=="llm_call"]
def sysof(c): return c["messages"][0]["content"]
def diff(a,b,la,lb):
    d=list(difflib.unified_diff(a.splitlines(),b.splitlines(),la,lb,lineterm="",n=0))
    return "\n".join(d) if d else "(identical)"
for sid in ["aiwolf_0001","candidate_selection_0001"]:
    print("#"*20, sid)
    C={c:calls(load(sid,c)) for c in ["single-batch","single-batch-stepped","single-online","multi-public","multi-private","single-batch-process","multi-private-process"]}
    sb=sysof(C["single-batch"][0])
    # per seat name of multi calls
    def seatname(c):
        return c.get("seat") or c.get("agent") or c.get("name")
    print("call keys:", sorted(C["multi-public"][0].keys()))
    print("--- single-batch vs single-batch-stepped (system)")
    print(diff(sb, sysof(C["single-batch-stepped"][0]), "batch","stepped"))
    print("--- single-batch vs single-online (system)")
    print(diff(sb, sysof(C["single-online"][0]), "batch","online"))
    seen=set()
    for c in C["multi-public"]:
        s=sysof(c)
        if s in seen: continue
        seen.add(s)
        print("--- single-batch vs multi-public system of", seatname(c))
        print(diff(sb, s, "batch","multi-public"))
    seen=set()
    for c in C["multi-private"]:
        s=sysof(c)
        if s in seen: continue
        seen.add(s)
        pub=next(x for x in C["multi-public"] if seatname(x)==seatname(c))
        print("--- multi-public vs multi-private system of", seatname(c))
        print(diff(sysof(pub), s, "public","private"))
    print("--- single-batch vs single-batch-process (system)")
    print(diff(sb, sysof(C["single-batch-process"][0]), "batch","batch-process"))
    seen=set()
    for c in C["multi-private-process"]:
        s=sysof(c)
        if s in seen: continue
        seen.add(s)
        pri=next(x for x in C["multi-private"] if seatname(x)==seatname(c))
        print("--- multi-private vs multi-private-process system of", seatname(c))
        print(diff(sysof(pri), s, "private","private-process"))
    # check all systems within a condition are constant per seat
    for cond in ["single-batch-stepped","single-online"]:
        ss={sysof(c) for c in C[cond]}
        print(cond, "distinct system prompts:", len(ss))
    for cond in ["multi-public","multi-private","multi-private-process"]:
        per={}
        for c in C[cond]: per.setdefault(seatname(c),set()).add(sysof(c))
        print(cond, "distinct systems per seat:", {k:len(v) for k,v in per.items()})
