import json,re,sys
from pathlib import Path
d=Path(sys.argv[1]); games=json.loads((d/"games.json").read_text())
res={}
for g,info in games.items():
    fp=d/"out"/f"llama__{g[:-3]}.json"
    if not fp.exists(): continue
    an={int(i["seq"]):i for i in list(json.loads(fp.read_text()).values())[0] if str(i.get("seq","")).isdigit()}
    rows,per={},None
    for line in (d/"games"/g).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "): per=line[3:]
        m=re.match(r"- \[(\d+)\] \*\*(.+?)\*\*: (.*)",line)
        if m: rows[int(m.group(1))]=(m.group(2),m.group(3),per)
    a=b=0
    for seq,(spk,t,p) in rows.items():
        if "?" not in t: continue
        m=re.search(r"@(\w+)",t)
        if not m: continue
        nxt=next((s for s in sorted(rows) if s>seq and rows[s][2]==p and rows[s][0]==m.group(1)),None)
        ok= nxt is not None and (an.get(nxt) or {}).get("resp_to")==seq
        a+= not ok
        b+= (nxt is not None and not ok)
    res.setdefault(info["condition"],[]).append((a,b))
for c,v in sorted(res.items()):
    print(f"{c:32s} n={len(v)} all_unanswered={sum(x for x,_ in v)/len(v):.2f} with_next_line={sum(y for _,y in v)/len(v):.2f}")
