import json
N=None
def mk(rows):
    out=[]
    for r in rows:
        seq,sp,c,rt,ty=r[:5]; rb=r[5] if len(r)>5 else 0; pd=r[6] if len(r)>6 else 0; note=r[7] if len(r)>7 else ""
        d={"seq":seq,"speaker":sp,"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":rb,"padded":pd}
        if rb or pd or c==0: d["note"]=note or "no new contribution"
        out.append(d)
    return out
R,T,M,S,Y="Rin","Toshio","Mizuki","Shion","Yumi"
batch=[(5,R,1,N,N),(6,T,1,N,N),(7,M,1,N,N),(8,S,1,N,N),(9,Y,1,N,N),
(25,R,2,N,N),(26,T,2,N,N),(27,M,2,N,N),(28,S,2,N,N),(29,Y,2,N,N),
(30,R,1,26,"add"),(31,T,1,30,"answer"),(32,M,1,29,"add"),(33,S,1,30,"object",1),(34,Y,1,33,"add"),
(35,R,1,N,N),(36,T,1,30,"add"),(37,M,1,N,N),(38,S,1,37,"add"),
(39,Y,0,36,"add",0,0,"restates own balance point in 34"),
(40,R,0,N,N,0,0,"repeats setup-time complaint of 25/35"),
(41,T,1,40,"add"),(42,M,0,N,N,0,0,"repeats fairness point of 37"),(43,S,1,41,"add"),
(44,Y,0,N,N,0,0,"repeats overhearing point of 29"),
(50,R,1,N,N),(51,T,1,N,N),(52,M,2,N,N),(53,S,1,N,N),(54,Y,1,N,N),
(55,R,1,52,"add"),(56,T,1,55,"answer"),(57,M,1,55,"answer"),
(58,S,0,57,"object",1,0,"repeats preference for stability"),
(59,Y,0,N,N,0,0,"repeats 54"),(60,R,1,N,N),(61,T,0,N,N,0,0,"repeats 51"),
(62,M,1,N,N),(63,S,0,N,N,0,0,"repeats 53"),(64,Y,1,N,N),
(65,R,0,N,N,0,0,"repeats 60"),(66,T,0,65,"agree",0,0,"bare agreement"),
(67,M,0,N,N,0,0,"repeats 62"),(68,S,0,N,N,0,0,"repeats 53"),(69,Y,0,68,"agree",0,0,"repeats vote")]
online=[(5,R,1,N,N),(6,T,1,N,N),(7,M,1,N,N),(8,S,1,N,N),(9,Y,1,N,N),
(10,R,1,8,"add"),(11,T,1,10,"object",1),(12,M,0,11,"agree",0,0,"agrees with 11"),
(13,S,1,11,"add"),
(14,Y,0,N,N,0,1,"excitement; restates plan of 9"),
(15,R,1,N,N),(16,T,1,15,"add"),(17,M,1,16,"add"),
(18,S,0,17,"agree",0,1,"agreement plus general sentiment"),
(19,Y,0,17,"agree",0,1,"sentiment only"),
(20,R,0,N,N,0,1,"restates own selection of 5; enthusiasm"),
(21,T,0,N,N,0,0,"restates selection of 6"),
(22,M,0,N,N,0,1,"restates selection of 7; sentiment"),
(23,S,0,N,N,0,1,"restates selection of 8; filler"),
(24,Y,0,N,N,0,1,"restates selection of 9; filler"),
(35,R,2,N,N),(36,T,2,N,N),(37,M,2,N,N),(38,S,2,N,N),(39,Y,2,N,N),
(40,R,1,36,"add"),(41,T,0,40,"answer",0,0,"restates cost point of 36"),
(42,M,1,41,"add"),(43,S,1,41,"add"),(44,Y,1,43,"add"),
(45,R,1,42,"add"),(46,T,1,45,"add"),
(47,M,0,46,"add",0,0,"summary of points already made"),
(48,S,0,47,"agree",0,1,"restates 43 after Exactly"),
(49,Y,0,47,"add",0,1,"repeats middle-ground wish of 44"),
(50,R,1,N,N),(51,T,0,50,"agree",0,1,"agreement restating cost point"),
(52,M,1,51,"add"),(53,S,0,52,"add",0,0,"repeats stability argument of 43"),
(54,Y,1,53,"add"),
(60,R,1,N,N),(61,T,1,60,"add"),(62,M,1,N,N),(63,S,1,N,N),(64,Y,1,N,N),
(65,R,1,64,"add"),(66,T,0,65,"answer",0,0,"repeats consensus and rationale"),
(67,M,1,66,"add"),(68,S,1,67,"add"),
(69,Y,0,68,"agree",0,1,"sentiment only"),
(70,R,0,N,N,0,1,"repeats vote"),
(71,T,0,70,"answer",0,0,"repeats vote of 61"),(72,M,0,70,"answer",0,0,"repeats vote of 62"),
(73,S,0,70,"answer",0,0,"repeats vote of 63"),(74,Y,0,70,"answer",0,0,"repeats vote of 64"),
(75,R,0,N,N,0,1,"repeats vote; sentiment"),
(76,T,0,N,N,0,0,"repeats vote"),(77,M,0,N,N,0,0,"repeats vote"),(78,S,0,N,N,0,0,"repeats vote"),(79,Y,0,N,N,0,0,"repeats vote")]
json.dump({"games/shared_living_0003__single-batch.md":mk(batch),"games/shared_living_0003__single-online.md":mk(online)},open("out/sonnet_20.json","w"),ensure_ascii=False)
print(len(batch),len(online))
