import re,json
base="/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot6/"
spec={
"game_034.md":dict(resp=[51,52,53,54,55,56,57,58,59],empty=[57,58,59],rebut=[]),
"game_035.md":dict(resp=[6,7,9,36,40,41,61,63,64,65,66,67,68,69,70,71,72,73,74],rebut=[63,64,67],empty=[70,72,74]),
"game_036.md":dict(resp=[6,30,31,34,51,52,53,54,55,56,57,58,59,60,61,62,64],rebut=[],empty=[33,34,61,62,63,64]),
}
out={}
for f,s in spec.items():
    L=[]
    for m in re.finditer(r"^- \[(\d+)\] \*\*(\w+)\*\*",open(base+"games/"+f).read(),re.M):
        q=int(m[1]);r=1 if q in s["resp"] or q in s["rebut"] else 0
        L.append(dict(seq=q,speaker=m[2],resp=r,rebut=int(q in s["rebut"]),empty=int(q in s["empty"]),ignore=0,misattr=0,reversal=0,note=""))
    out[f]=L
json.dump(out,open(base+"out/sonnet_11.json","w"),ensure_ascii=False)
print({k:len(v) for k,v in out.items()})
