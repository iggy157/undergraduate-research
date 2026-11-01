import json, glob, hashlib, os, re, sys
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
def sha1(p): return hashlib.sha1(open(p,'rb').read()).hexdigest()
for d in sorted(glob.glob(ROOT+"/log/_pilot6/*/*/*process*")):
    gid=os.path.basename(d)
    f=d+"/"+gid+".jsonl"
    hdr=None; viol=None; calls=[]
    for line in open(f):
        r=json.loads(line)
        if r["kind"]=="header": hdr=r
        elif r["kind"]=="violations": viol=r
        elif r["kind"]=="llm_call": calls.append(r)
    sc=hdr["scenario"]
    cur=sha1(ROOT+"/"+sc["path"])
    print("=====",gid)
    print("  header.scenario:",sc, " sha1==current file:", sc["sha1"]==cur)
    print("  axes:",hdr["axes"], "outcome:", hdr.get("outcome"))
    devs=[v for v in viol["items"] if v["code"]=="scenario_deviation"] if viol else []
    print("  scenario_deviation items:",devs)
    # system of first call per seat
    seen=set()
    for c in calls:
        msgs=c.get("messages") or c.get("request",{}).get("messages")
        if not msgs: continue
        sysm=msgs[0]["content"]
        seat=c.get("seat") or c.get("agent")
        key=seat
        if key in seen: continue
        seen.add(key)
        i=sysm.find("## Plan")
        tail=sysm[i:] if i>=0 else "<NO PLAN BLOCK>"
        bad=[w for w in ("Votes:","Executed:","Night:","Outcome:","Adopted:") if w in tail]
        nseats=tail.count("\n- ") - tail.count("\n- Day") - tail.count("\n- Round")
        print(f"  seat={seat} plan_block_len={len(tail)} outcome_words={bad} seat_lines={nseats}")
        if len(seen)==1: print("  ---- PLAN BLOCK ----\n"+tail+"\n  --------------------")
