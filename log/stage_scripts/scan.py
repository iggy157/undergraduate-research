import re,json,sys,os,glob
base=sys.argv[1]; conds=sys.argv[2].split(',')
def parse(p):
    sec=None; out=[]
    for l in open(p):
        if l.startswith('## '): sec=l[3:].strip()
        m=re.match(r'- \[(\d+)\] \*\*(.+?)\*\*: (.*)',l)
        if m: out.append(dict(id=int(m[1]),sp=m[2],t=m[3],sec=sec,w=len(m[3].split())))
    return out
def ann(setup,cond):
    p=f'{base}/out/llama__{setup}__{cond}.json'
    d=json.load(open(p)); v=list(d.values())[0]; return {x['seq']:x for x in v}
def ignored(us,a):
    res=[]
    for i,u in enumerate(us):
        names=re.findall(r'@(\w+)',u['t'])
        if '?' not in u['t']: continue
        for n in names:
            nxt=[v for v in us[i+1:] if v['sp']==n and v['sec']==u['sec']]
            if not nxt: continue
            v=nxt[0]; rt=a.get(v['id'],{}).get('resp_to')
            res.append((u['id'],n,v['id'],rt==u['id'],rt, us.index(v)-i))
    return res
setups=sorted(set(os.path.basename(p).split('__')[0] for p in glob.glob(base+'/games/*.md')))
for s in setups:
    row=[s]
    for c in conds:
        us=parse(f'{base}/games/{s}__{c}.md'); a=ann(s,c)
        ig=ignored(us,a)
        aw=sum(u['w'] for u in us)/len(us)
        nig=sum(1 for x in ig if not x[3]); nans=sum(1 for x in ig if x[3])
        pad=sum(a[k]['padded'] for k in a)/len(a)
        row.append(f'{c}: w={aw:.1f} pad={pad:.2f} q={len(ig)} ans={nans} ign={nig}')
    print(' | '.join(row))
