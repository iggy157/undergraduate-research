import json
S,M,K,B,T="Servas","Midori","Kenji","Benjamin","Toshio"
def mk(rows):
    out=[]
    for r in rows:
        seq,sp,c,rt,ty=r[:5]; reb=r[5] if len(r)>5 else 0; pad=r[6] if len(r)>6 else 0; note=r[7] if len(r)>7 else ""
        d={"seq":seq,"speaker":sp,"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":reb,"padded":pad}
        if (reb or pad or c==0) and not note: note="see text"
        if note: d["note"]=note
        out.append(d)
    return out
R1=[(5,S,1,None,None),(6,M,1,None,None),(7,K,1,None,None),(8,B,1,None,None),(9,T,1,None,None)]
st=R1+[(25,S,2,None,None),(26,M,2,None,None),(27,K,2,None,None),(28,B,2,None,None),(29,T,2,None,None),
(30,S,1,28,"add"),(31,M,1,25,"add"),(32,K,1,28,"add"),(33,B,1,32,"add"),(34,T,1,None,None),(35,S,1,34,"add"),(36,M,1,35,"add"),
(37,K,1,36,"object"),(38,B,1,37,"add"),(39,T,0,None,None,0,0,"repeats [29] repository point"),(40,S,0,39,"agree",0,0,"summary of consensus"),
(41,M,0,40,"agree",0,0,"agreement and ritual"),(42,K,0,None,None,0,0,"ritual"),(43,B,0,None,None,0,0,"ritual"),
(50,S,1,None,None),(51,M,1,50,"add"),(52,K,1,50,"add"),(53,B,1,50,"add"),(54,T,1,50,"add"),(55,S,1,54,"add"),(56,M,1,54,"add"),
(57,K,1,55,"add"),(58,B,1,57,"agree"),(59,T,0,56,"answer",0,0,"repeats [54]"),(60,S,1,None,None),(61,M,1,60,"add"),(62,K,1,61,"add"),
(63,B,1,62,"add"),(64,T,0,63,"agree",0,0,"agreement only")]
ba=R1+[(25,S,2,None,None),(26,M,2,None,None),(27,K,2,None,None),(28,B,2,None,None),(29,T,2,None,None),
(30,S,1,26,"add"),(31,M,1,30,"add"),(32,K,1,28,"add"),(33,B,1,32,"answer"),(34,T,1,33,"add"),
(35,S,0,None,None,0,0,"repeats [25] concern"),(36,M,1,34,"add"),(37,K,1,None,None),(38,B,1,37,"add"),(39,T,1,36,"answer"),(40,S,1,None,None),
(41,M,0,40,"agree",0,0,"bare agreement"),(42,K,0,None,None,0,0,"ritual"),(43,B,0,None,None,0,0,"ritual"),
(50,S,2,None,None),(51,M,1,50,"add"),(52,K,1,50,"add"),(53,B,2,50,"add"),(54,T,1,50,"add"),(55,S,1,51,"add"),(56,M,1,55,"answer"),
(57,K,1,56,"add"),(58,B,1,54,"add"),(59,T,1,58,"answer"),(60,S,1,59,"add"),(61,M,1,60,"agree"),(62,K,1,61,"add"),(63,B,1,62,"add"),
(64,T,0,63,"agree",0,0,"repeats [54]"),(65,S,0,64,"agree",0,0,"closing pleasantry"),(66,M,0,65,"agree",0,0,"bare agreement"),
(67,K,0,66,"agree",0,0,"bare agreement"),(68,B,0,67,"agree",0,0,"bare agreement")]
on=[(5,S,1,None,None),(6,M,1,None,None),(7,K,1,None,None),(8,B,1,None,None),(9,T,1,None,None),
(11,M,1,8,"add"),(12,K,1,11,"add",0,1,"opening sentiment adds nothing"),(13,B,1,12,"object",1),
(14,T,0,None,None,0,0,"vague filler"),(15,S,0,14,"agree",0,1,"generic sentiment"),(16,M,0,15,"agree",0,0,"agreement and sentiment"),
(17,K,0,None,None,0,0,"excitement only"),(18,B,1,17,"add"),(19,T,1,18,"add"),(23,B,0,None,None,0,0,"yields floor"),
(35,S,2,None,None),(36,M,2,None,None),(37,K,2,None,None),(38,B,2,None,None),(39,T,2,None,None),
(40,S,1,39,"add",0,1,"praise opening adds nothing"),(41,M,1,38,"add"),(42,K,1,40,"add"),(43,B,1,42,"answer"),(44,T,1,41,"add"),
(45,S,1,43,"add"),(46,M,1,45,"add"),(47,K,0,46,"agree",0,0,"restates [46]"),(48,B,1,39,"add"),(49,T,0,48,"agree",0,0,"repeats [39]"),
(50,S,0,49,"agree",0,0,"summary of [46]/[48]"),(51,M,0,50,"agree",0,0,"repeats [46]"),(52,K,0,None,None,0,0,"hope only"),
(53,B,1,52,"add"),(54,T,0,None,None,0,0,"sentiment only"),
(60,S,1,None,None,0,1,"closing sentence adds nothing"),(61,M,1,60,"add"),(62,K,1,60,"add"),(63,B,1,62,"agree"),(64,T,1,63,"add"),
(65,S,1,61,"object",1),(66,M,1,65,"agree"),(67,K,0,66,"agree",0,1,"repeats [62]"),(68,B,0,64,"agree",0,0,"repeats [63]"),
(69,T,0,68,"agree",0,1,"repeats [64]"),(70,S,0,69,"agree",0,1,"restates agreement"),(71,M,0,70,"agree",0,0,"repeats [66]"),
(72,K,0,71,"agree",0,1,"sentiment"),(73,B,0,72,"agree",0,1,"sentiment"),(74,T,0,73,"agree",0,1,"repeats [64]"),
(75,S,0,None,None,0,0,"repeats support for Atlas"),(76,M,0,None,None,0,0,"repeats support for Atlas"),(77,K,0,None,None,0,0,"repeats support for Atlas"),
(78,B,0,None,None,0,0,"repeats support for Atlas"),(79,T,0,None,None,0,0,"repeats support for Atlas")]
json.dump({"candidate_selection_0001__single-batch-stepped.md":mk(st),"candidate_selection_0001__single-batch.md":mk(ba),"candidate_selection_0001__single-online.md":mk(on)},open("out/sonnet_08.json","w"),ensure_ascii=False,indent=1)
print(len(st),len(ba),len(on))
