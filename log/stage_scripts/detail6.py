import csv, glob, os, json, re, sys
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
sys.path.insert(0, ROOT)
csv.field_size_limit(10**8)
def rows_of(d):
    gid=os.path.basename(d); f=d+"/"+gid+".log"
    rs=[dict(zip(["seq","round","turn","type","agent","target","text","extra"],r)) for r in csv.reader(open(f))]
    return [r for r in rs if r.get("type") and r["type"]!="type"]
def viols(d):
    gid=os.path.basename(d)
    for line in open(d+"/"+gid+".jsonl"):
        r=json.loads(line)
        if r["kind"]=="violations": return r["items"]
    return []
print("=== early_reveal(_partial) details, process conditions + no-plan counterparts")
for d in sorted(glob.glob(ROOT+"/log/_pilot6/*/*/*")):
    gid=os.path.basename(d); setup,cond=gid.split("__")[:2]
    if cond not in ("single-batch-process","multi-private-process","single-batch","multi-private"): continue
    its=[v for v in viols(d) if v["code"].startswith("early_reveal")]
    if not its: continue
    print(f"-- {setup} {cond} {gid[-15:]}")
    for v in its:
        det=v.get("detail") or {}
        print(f"   seq={v.get('seq')} {json.dumps(det, ensure_ascii=False)[:300]}")
print()
print("=== talk dumps")
def dump(setup, cond, rounds=None, maxlen=140):
    ds=[d for d in sorted(glob.glob(ROOT+f"/log/_pilot6/*/*/{setup}__{cond}__*"))]
    d=ds[0]; rows=rows_of(d)
    print(f"----- {os.path.basename(d)}")
    for r in rows:
        if r["type"] in ("talk","pass","vote","action","result") and (rounds is None or int(r["round"]) in rounds):
            t=r["text"].replace("\n"," ")
            print(f"  R{r['round']}T{r['turn']} {r['type']:6s} {r['agent']:9s} {r['target']:9s} {t[:maxlen]}")
dump("aiwolf_0002","multi-private-process",[1])
dump("aiwolf_0002","multi-private",[1])
dump("candidate_selection_0001","multi-private-process",[1,2],120)
dump("candidate_selection_0001","multi-private",[1,2],120)
dump("shared_living_0002","multi-private-process",[3],120)
