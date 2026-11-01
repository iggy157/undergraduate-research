import re,json
def run(f,resp,rebut,empty):
    out=[]
    for l in open('games/'+f):
        m=re.match(r'- \[(\d+)\] \*\*(\w+)\*\*',l)
        if m:
            i=int(m[1]);r=1 if i in resp or i in rebut else 0
            out.append(dict(seq=i,speaker=m[2],resp=r,rebut=int(i in rebut),empty=int(i in empty),ignore=0,misattr=0,reversal=0,note=""))
    return out
d={}
d['game_052.md']=run('game_052.md',{6,7,8,10,35,41,42,43,56,57,58,59,60,65,66,67,68,69,70},{61},{43,68,69})
d['game_053.md']=run('game_053.md',{30,31,51,52,54,55,56,61},{53},{33,56})
d['game_054.md']=run('game_054.md',{35,36,37,38,39,40,41,42,43,44,56,57,58,61,62,64},{59},{40})
json.dump(d,open('out/sonnet_17.json','w'))
print({k:len(v) for k,v in d.items()})
