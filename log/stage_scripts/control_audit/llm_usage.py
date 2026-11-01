import json, sys, glob, collections, statistics
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research/log"
files=sorted(f for f in glob.glob(ROOT+"/*/*/*/*.jsonl") if "_pilot1" not in f)
for f in files:
    recs=[json.loads(l) for l in open(f)]
    hdr=recs[0]; calls=[r for r in recs if r.get("kind")=="llm_call"]
    print("="*100); print(f.split("/log/")[1]); print("header model:",hdr.get("model"),"method:",hdr.get("method"))
    # llm_call-level models & finish reasons
    print("llm_call.model values:",collections.Counter(c.get("model") for c in calls))
    print("finish_reason:",collections.Counter(c.get("finish_reason") for c in calls))
    print("error:",collections.Counter(bool(c.get("error")) for c in calls), [c.get("error") for c in calls if c.get("error")][:3])
    print("truncated:",collections.Counter(c.get("truncated") for c in calls))
    print("usage keys:", sorted((calls[0].get("usage") or {}).keys()))
    print("llm_call keys:", sorted(calls[0].keys()))
    if hdr.get("method")=="single":
        c=calls[0]; u=c["usage"] or {}
        print(f"single: roles={[m['role'] for m in c['messages']]} prompt_tokens={u.get('prompt_tokens')} completion_tokens={u.get('completion_tokens')} total={u.get('total_tokens')} latency_ms={c['latency_ms']} resp_chars={len(c['response'] or '')} sys_chars={len(c['messages'][0]['content'])} user_chars={len(c['messages'][1]['content'])}")
        print("extra usage:", {k:v for k,v in u.items() if k not in ('prompt_tokens','completion_tokens','total_tokens')})
        continue
    # multi
    by_req=collections.defaultdict(list)
    for c in calls: by_req[c["request"]].append(c)
    for req,cs in by_req.items():
        pt=[c["usage"]["prompt_tokens"] for c in cs if c.get("usage")]
        ct=[c["usage"]["completion_tokens"] for c in cs if c.get("usage")]
        lat=[c["latency_ms"] for c in cs]
        print(f"  {req:12s} n={len(cs):3d} prompt_tokens min/med/max={min(pt)}/{int(statistics.median(pt))}/{max(pt)} completion min/med/max={min(ct)}/{int(statistics.median(ct))}/{max(ct)} latency med={int(statistics.median(lat))}ms max={max(lat)}")
    tot_prompt=sum(c["usage"]["prompt_tokens"] for c in calls if c.get("usage")); tot_comp=sum(c["usage"]["completion_tokens"] for c in calls if c.get("usage"))
    print(f"  TOTAL prompt_tokens={tot_prompt} completion_tokens={tot_comp}")
    # per-seat TALK trajectory
    for seat in range(1,6):
        cs=[c for c in calls if c["seat"]==seat and c["request"]=="TALK"]
        traj=[(c["round"],c["turn"],c["usage"]["prompt_tokens"],c["usage"]["completion_tokens"],len(c["messages"]),sum(1 for m in c["messages"] if m["role"]=="assistant" and m["content"]=="Acknowledged."),c["finish_reason"]) for c in cs]
        print(f"  seat{seat} TALK (round,turn,prompt_tok,comp_tok,n_msgs,n_ack,finish):",traj)
    # role structure of the last call
    last=max(calls,key=lambda c:(c["seat"],c["seq"]))
    print("  last call roles:", collections.Counter(m["role"] for m in last["messages"]), "seq",last["seq"],"seat",last["seat"],last["request"])
    # response of talk: strip difference, empties, Skip/Over counts
    talks=[c for c in calls if c["request"]=="TALK"]
    print("  TALK responses: empty=",sum(1 for c in talks if not (c['response'] or '').strip()),"raw!=strip=",sum(1 for c in talks if c['response'] is not None and c['response']!=c['response'].strip()), "Skip/Over=",collections.Counter((c['response'] or '').strip() for c in talks if (c['response'] or '').strip() in ('Skip','Over')))
    # multi-line talk responses
    print("  TALK responses with newline:",sum(1 for c in talks if '\n' in (c['response'] or '')), "max chars:",max(len(c['response'] or '') for c in talks))
    # check raw agent files equal to merged
    import os
    d=os.path.dirname(f)
    for seat in range(1,6):
        p=f"{d}/raw/agent.{seat}.jsonl"
        raw=[json.loads(l) for l in open(p)]
        merged=[c for c in calls if c["seat"]==seat]
        same = [ {k:v for k,v in r.items()} for r in raw] == [ {k:v for k,v in m.items()} for m in merged]
        if not same:
            diffs=set()
            for r,m in zip(raw,merged):
                for k in set(r)|set(m):
                    if r.get(k)!=m.get(k): diffs.add(k)
            print(f"  seat{seat}: raw n={len(raw)} merged n={len(merged)} identical={same} diff keys={diffs}")
        else:
            print(f"  seat{seat}: raw n={len(raw)} merged n={len(merged)} identical")
