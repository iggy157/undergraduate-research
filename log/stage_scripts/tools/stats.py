import re,sys
for f in sys.argv[1:]:
    txt=open(f).read()
    parts=re.split(r'^# Transcript (\w)\n',txt,flags=re.M)
    print(f.split('/')[-1])
    for i in range(1,len(parts),2):
        t,body=parts[i],parts[i+1]
        utt=re.findall(r'^- \*\*(\w+)\*\*: (.*)$',body,flags=re.M)
        sp=[u for n,u in utt if u.strip().rstrip('.') not in('Skip','Over')]
        sk=sum(1 for n,u in utt if u.strip().rstrip('.')=='Skip')
        ov=sum(1 for n,u in utt if u.strip()=='Over')
        # speech+Over same turn
        turns=re.split(r'^#### ',body,flags=re.M)
        dbl=0; lock=0
        for tb in turns:
            us=re.findall(r'^- \*\*(\w+)\*\*: (.*)$',tb,flags=re.M)
            names=[n for n,_ in us]
            dbl+=len(names)-len(set(names))
            vals=[u.strip().rstrip('.') for _,u in us]
            if us and len(set(vals))==1 and vals[0] in('Skip','Over'): lock+=1
        words=sum(len(u.split()) for u in sp)
        print(f"  {t}: speech={len(sp)} avgwords={words/max(1,len(sp)):.1f} total={words} skip={sk} over={ov} spoke+over={dbl} lockstepTurns={lock}")
