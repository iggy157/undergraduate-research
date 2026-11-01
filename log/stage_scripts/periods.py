import csv, glob, os, sys, difflib
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
csv.field_size_limit(10**8)
rows_by={}
for d in sorted(glob.glob(ROOT+"/log/_pilot5/*/*/*")):
    gid=os.path.basename(d); f=d+"/"+gid+".log"
    if not os.path.isfile(f): continue
    rows=[dict(zip(["seq","round","turn","type","agent","target","text","extra"],r)) for r in csv.reader(open(f))]; rows=[r for r in rows if r.get("type") and r["type"]!="type"]
    talks=[r for r in rows if r["type"]=="talk"]
    rounds=sorted({int(r["round"]) for r in rows if r["type"] in ("talk","vote","pass")})
    res=[r["text"] for r in rows if r["type"]=="result"]
    votes=[(r["round"],r["agent"],r["target"]) for r in rows if r["type"]=="vote"]
    setup,cond=gid.split("__")[:2]
    rows_by[(setup,cond)]=talks
    print(f"{setup:28s} {cond:28s} periods={rounds} talks={len(talks)} passes={sum(1 for r in rows if r['type']=='pass')} result={res} lastvotes={[v for v in votes if v[0]==str(rounds[-1])]}")
print()
# similarity single-batch vs single-batch-process
for (setup,cond),talks in sorted(rows_by.items()):
    if cond=="single-batch-process":
        base=rows_by.get((setup,"single-batch"))
        if base:
            a="\n".join(f"{r['agent']}: {r['text']}" for r in base); b="\n".join(f"{r['agent']}: {r['text']}" for r in talks)
            print(f"{setup}: single-batch vs single-batch-process talk similarity = {difflib.SequenceMatcher(None,a,b).ratio():.3f}  (len {len(base)} vs {len(talks)})")
    if cond=="multi-private-process":
        base=rows_by.get((setup,"multi-private"))
        if base:
            a="\n".join(f"{r['agent']}: {r['text']}" for r in base); b="\n".join(f"{r['agent']}: {r['text']}" for r in talks)
            print(f"{setup}: multi-private vs multi-private-process talk similarity = {difflib.SequenceMatcher(None,a,b).ratio():.3f}  (len {len(base)} vs {len(talks)})")
