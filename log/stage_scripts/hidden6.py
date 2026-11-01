import csv, glob, os, json, collections
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
csv.field_size_limit(10**8)
def rows_of(d):
    gid=os.path.basename(d); f=d+"/"+gid+".log"
    rs=[dict(zip(["seq","round","turn","type","agent","target","text","extra"],r)) for r in csv.reader(open(f))]
    return [r for r in rs if r.get("type") and r["type"]!="type"]
for d in sorted(glob.glob(ROOT+"/log/_pilot6/*/*/*")):
    gid=os.path.basename(d); setup,cond=gid.split("__")[:2]
    dom=setup.rsplit("_",1)[0]
    sc=json.load(open(f"{ROOT}/scenarios/{dom}/{setup}.json"))
    rows=rows_of(d)
    plan={int(p["period"]):p for p in sc["periods"]}
    tot=match=0; exe_ok=[]
    for n,p in plan.items():
        pv=p.get("votes") or {}
        av={r["agent"]:r["target"] for r in rows if r["type"]=="vote" and int(r["round"])==n}
        for v,t in pv.items():
            if v in av: tot+=1; match+= (av[v]==t)
        if dom=="aiwolf" and "executed" in p:
            ex=[r["target"] for r in rows if r["type"]=="action" and int(r["round"])==n and "execute" in r["extra"]]
            exe_ok.append((n, ex[0] if ex else None, p["executed"]))
    res=[r["text"] for r in rows if r["type"]=="result"]
    fin=sc["final"].get("winner") or sc["final"].get("adopted")
    periods=sorted({int(r["round"]) for r in rows if r["type"] in ("talk","vote")})
    lastv=collections.Counter(r["target"] for r in rows if r["type"]=="vote" and int(r["round"])==periods[-1])
    viol=None
    for line in open(d+"/"+gid+".jsonl"):
        r=json.loads(line)
        if r["kind"]=="violations": viol=r
    vc=collections.Counter(v["code"] for v in (viol["items"] if viol else []))
    dv=[v["detail"] for v in (viol["items"] if viol else []) if v["code"]=="scenario_deviation"]
    print(f"{setup:26s} {cond:24s} {gid[-15:]} votes==plan {match}/{tot} final==plan {str(res==[fin]):5s} ({res[0] if res else None} vs {fin}) periods {periods} lastvote {dict(lastv)} exec {exe_ok} viol {dict(vc)} dev {dv}")
