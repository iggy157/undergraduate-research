import re,json,sys,os,glob
sys.path.insert(0,os.path.dirname(__file__))
exec(open(os.path.join(os.path.dirname(__file__),'scan.py')).read().split('setups=sorted')[0].replace("base=sys.argv[1]; conds=sys.argv[2].split(',')",""))
base=sys.argv[1]
for c in sys.argv[2].split(','):
    vals=[]
    for p in sorted(glob.glob(f'{base}/games/*__{c}.md')):
        s=os.path.basename(p).split('__')[0]
        try: a=ann(s,c)
        except Exception: continue
        vals.append(sum(1 for r in ignored(parse(p),a) if not r[3]))
    print(c, len(vals), round(sum(vals)/len(vals),2))
