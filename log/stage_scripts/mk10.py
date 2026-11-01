import json
S=dict(Servas=1,Asuka=1,Minako=1,Mio=1,Toshio=1)
def R(rows):
    out=[]
    for r in rows:
        seq,sp,c,to,ty=r[:5]; rb=r[5] if len(r)>5 else 0; pd=r[6] if len(r)>6 else 0; note=r[7] if len(r)>7 else ""
        d=dict(seq=seq,speaker=sp,content=c,resp=1 if to else 0,resp_to=to,resp_type=ty if to else None,rebut=rb,padded=pd)
        if rb or pd or c==0: d["note"]=note or ("repeats earlier point" if c==0 else "")
        out.append(d)
    return out
SV,AS,MN,MO,TO="Servas","Asuka","Minako","Mio","Toshio"
r1=[(5,SV,1,None,None),(6,AS,1,None,None),(7,MN,1,None,None),(8,MO,1,None,None),(9,TO,1,None,None)]
proc=r1+[
(25,SV,1,None,None),(26,AS,2,None,None),(27,MN,2,None,None),(28,MO,2,None,None),(29,TO,2,None,None),
(30,SV,1,27,"add"),(31,AS,1,29,"add"),(32,MN,1,30,"answer"),(33,MO,1,31,"add"),(34,TO,1,33,"add"),
(35,SV,1,32,"add"),(36,AS,1,35,"add"),(37,MN,1,36,"add"),(38,MO,1,37,"add"),(39,TO,1,38,"agree"),(40,SV,1,39,"add"),
(41,AS,0,40,"agree",0,0,"bare agreement"),(42,MN,0,40,"agree",0,0,"ritual assent"),(43,MO,0,40,"agree",0,0,"ritual assent"),(44,TO,0,40,"agree",0,0,"ritual assent"),
(50,SV,2,None,None),(51,AS,2,50,"add"),(52,MN,1,51,"add"),(53,MO,2,52,"add"),(54,TO,2,53,"add"),
(55,SV,1,53,"add"),(56,AS,1,54,"add"),(57,MN,2,55,"add"),(58,MO,2,57,"object",1),(59,TO,1,56,"answer"),
(60,SV,1,59,"add"),(61,AS,0,60,"agree",0,0,"repeats [56]"),(62,MN,1,60,"add"),(63,MO,1,62,"add"),(64,TO,0,60,"agree",0,0,"repeats [59]"),
(65,SV,1,64,"add"),(66,AS,0,65,"agree",0,0,"vote already stated in [61]"),(67,MN,0,65,"agree",0,0,"position already stated in [62]"),(68,MO,0,65,"agree",0,0,"repeats [63]"),(69,TO,0,65,"agree",0,0,"repeats [64]")]
st=r1[:]
st[0]=(5,SV,1,None,None,0,1,"opening phrase delivers nothing")
stp=st+[
(25,SV,2,None,None),(26,AS,2,None,None),(27,MN,2,None,None),(28,MO,2,None,None),(29,TO,1,None,None),
(30,SV,1,27,"add"),(31,AS,1,29,"add"),(32,MN,1,30,"agree"),(33,MO,1,26,"add"),(34,TO,1,31,"answer"),
(35,SV,1,28,"add"),(36,AS,1,None,None),(37,MN,1,35,"add"),(38,MO,0,37,"agree",0,0,"repeats [28]/[33]"),(39,TO,1,None,None),
(40,SV,1,39,"add"),(41,AS,0,40,"agree",0,0,"repeats earlier avoidance of overhead"),(42,MN,0,40,"agree",0,0,"repeats [37]"),(43,MO,0,40,"agree",0,0,"ritual assent"),(44,TO,0,40,"agree",0,0,"ritual assent"),
(50,SV,1,None,None),(51,AS,2,50,"add"),(52,MN,2,50,"add"),(53,MO,2,52,"add"),(54,TO,2,53,"add"),
(55,SV,1,52,"add"),(56,AS,1,54,"add"),(57,MN,1,55,"add"),(58,MO,1,57,"add"),(59,TO,1,56,"answer"),
(60,SV,1,59,"add"),(61,AS,0,60,"agree",0,0,"repeats [51]"),(62,MN,0,60,"agree",0,0,"repeats [52]/[57]"),(63,MO,1,62,"add"),(64,TO,0,60,"agree",0,0,"repeats [39]/[54]"),
(65,SV,1,64,"add"),(66,AS,0,65,"agree",0,0,"repeats [61]"),(67,MN,0,65,"agree",0,0,"bare agreement"),(68,MO,0,65,"agree",0,0,"bare agreement"),(69,TO,0,65,"agree",0,0,"bare agreement")]
sb=[(5,SV,1,None,None,0,1,"opening phrase delivers nothing")]+r1[1:]+[
(25,SV,2,None,None),(26,AS,2,None,None),(27,MN,2,None,None),(28,MO,2,None,None),(29,TO,1,None,None),
(30,SV,1,27,"add"),(31,AS,1,29,"add"),(32,MN,1,30,"agree"),(33,MO,1,26,"add"),(34,TO,1,31,"answer"),
(35,SV,1,28,"add"),(36,AS,1,34,"add"),(37,MN,1,35,"add"),(38,MO,0,37,"agree",0,0,"repeats [28]/[33]"),(39,TO,1,None,None),
(50,SV,1,None,None),(51,AS,1,50,"add"),(52,MN,1,50,"add"),(53,MO,1,52,"add"),(54,TO,2,53,"add"),
(55,SV,1,54,"add"),(56,AS,1,55,"agree"),(57,MN,1,55,"add"),(58,MO,0,57,"agree",0,0,"repeats [53]"),(59,TO,0,55,"agree",0,0,"bare agreement")]
o={"candidate_selection_0002__single-batch-process.md":R(proc),"candidate_selection_0002__single-batch-stepped.md":R(stp),"candidate_selection_0002__single-batch.md":R(sb)}
json.dump(o,open("out/sonnet_10.json","w"),ensure_ascii=False)
print({k:len(v) for k,v in o.items()})
