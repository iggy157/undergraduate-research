import re,json
cfg={
"game_037.md":dict(r0={5,6,7,8,9,25,26,27,28,29,31,34,50,55},reb={57},emp={64,66,67,68,69}),
"game_038.md":dict(r0={5,6,7,8,9,25,26,27,28,29,31,32,33,34,50},reb=set(),emp={57,58,59}),
"game_039.md":dict(r0={5,6,7,8,9,25,26,27,28,29,32,33,34,50},reb={51},emp={60,61,63,64}),
}
out={}
for f,c in cfg.items():
    L=[]
    for m in re.finditer(r'^- \[(\d+)\] \*\*(\w+)\*\*',open('games/'+f).read(),re.M):
        s=int(m[1])
        if s==5 and False: pass
        L.append(dict(seq=s,speaker=m[2],resp=0 if s in c['r0'] else 1,rebut=int(s in c['reb']),empty=int(s in c['emp']),ignore=0,misattr=0,reversal=0,note=""))
    out[f]=L
json.dump(out,open('out/sonnet_12.json','w'))
print({k:len(v) for k,v in out.items()})
