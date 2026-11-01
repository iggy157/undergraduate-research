import json
T,V,G,M,B="Toshio","Victoria","George","Mizuki","Benjamin"
# (seq,spk,content,resp_to,type,rebut,padded,note)
def mk(rows):
    out=[]
    for s,sp,c,rt,ty,rb,pd,*n in rows:
        d={"seq":s,"speaker":sp,"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":rb,"padded":pd}
        if rb or c==0 or pd: d["note"]=n[0] if n else "see text"
        out.append(d)
    return out
a=mk([
(5,T,2,None,None,0,0),(6,V,1,5,"add",0,0),(7,G,2,None,None,0,0),(8,M,2,None,None,0,0),(9,B,2,8,"add",0,0),
(10,T,1,6,"add",0,0),(11,V,1,10,"answer",0,0),(12,G,1,11,"add",0,0),(13,M,1,12,"add",0,0),(14,B,1,13,"add",0,1,"flourish about brochures and voids"),
(15,T,0,None,None,0,1,"repeats own choices from [5]"),(16,V,0,None,None,0,1,"restates own choices from [6]"),(17,G,0,None,None,0,1,"restates [7]"),(18,M,0,None,None,0,1,"restates [8]"),(19,B,0,None,None,0,1,"restates choices; closing sentiment"),
(20,T,1,19,"agree",0,1,"closing sentiment after the proposal to end"),(21,V,0,20,"agree",0,1,"agreement plus summary"),(22,G,0,20,"agree",0,1,"agreement only"),(23,M,0,20,"agree",0,1,"agreement only"),(24,B,0,20,"agree",0,1,"closing pleasantry"),
(35,T,2,None,None,0,0),(36,V,1,35,"add",0,0),(37,G,1,None,None,0,0),(38,M,2,None,None,0,0),(39,B,2,None,None,0,0),
(40,T,1,37,"add",0,0),(41,V,1,40,"object",0,0),(42,G,1,41,"object",1,0),(43,M,1,42,"object",1,0),(44,B,0,43,"add",0,1,"restates [39] and [37] as a dilemma"),
(45,T,1,44,"add",0,0),(46,V,0,45,"agree",0,0,"repeats own concerns from [36],[43]"),(47,G,1,45,"object",1,0),(48,M,2,47,"object",1,0),(49,B,0,48,"add",0,1,"repeats AV reserve from [39]"),
(50,T,1,47,"add",0,0),(51,V,0,50,"add",0,1,"repeats off-site cost from [36]"),(52,G,1,50,"answer",0,0),(53,M,1,52,"object",1,0),(54,B,0,53,"add",0,1,"summary and sentiment"),
(60,T,1,None,None,0,0),(61,V,1,60,"answer",0,0),(62,G,1,61,"add",0,0),(63,M,1,62,"object",1,0),(64,B,1,63,"add",0,0),
(65,T,1,64,"add",0,0),(66,V,1,65,"agree",0,0),(67,G,0,66,"agree",0,1,"repeats [62]"),(68,M,1,67,"add",0,0),(69,B,1,68,"agree",0,1,"flourish plus vote"),
(70,T,1,69,"agree",0,0),(71,V,1,70,"agree",0,0),(72,G,1,71,"agree",0,1,"repeats prior reasoning"),(73,M,1,72,"agree",0,0),
(75,T,0,73,"agree",0,1,"restates consensus"),(77,V,0,75,"agree",0,1,"restates consensus"),(79,G,0,77,"agree",0,1,"closing sentiment"),(81,M,0,79,"agree",0,1,"closing restatement"),(83,B,0,81,"agree",0,1,"closing flourish"),
])
b=mk([
(5,T,1,None,None,0,0),(6,V,1,5,"add",0,0),(7,G,1,6,"add",0,0),(8,M,1,7,"add",0,0),(9,B,1,8,"add",0,0),
(10,T,1,6,"add",0,0),(11,V,1,10,"answer",0,0),(12,G,1,None,None,0,0),(13,M,1,None,None,0,0),(14,B,1,None,None,0,0),
(15,T,1,11,"add",0,0),(16,V,1,None,None,0,0),(17,G,1,None,None,0,0),(18,M,1,None,None,0,0),(19,B,1,18,"agree",0,0),
(35,T,1,None,None,0,0),(36,V,1,35,"add",0,0),(37,G,1,None,None,0,0),(38,M,2,None,None,0,0),(39,B,2,None,None,0,0),
(40,T,1,37,"add",0,0),(41,V,1,40,"add",0,0),(42,G,0,40,"answer",0,0,"restates burden from [37]"),(43,M,1,42,"add",0,0),(44,B,0,43,"agree",0,0,"repeats [39]"),
(45,T,1,44,"add",0,0),(46,V,1,45,"add",0,0),(47,G,0,45,"object",0,0,"repeats [37]"),(48,M,0,45,"add",0,0,"repeats [38]"),(49,B,1,47,"object",0,0),
(60,T,1,None,None,0,0),(61,V,1,60,"add",0,0),(62,G,1,60,"object",1,0),(63,M,1,62,"object",1,0),(64,B,1,63,"add",0,0),
(65,T,1,64,"object",0,0),(66,V,1,65,"add",0,0),(67,G,1,64,"add",0,0),(68,M,1,67,"answer",0,0),(69,B,0,68,"agree",0,0,"repeats [64]"),
(70,T,1,69,"agree",0,0),(71,V,1,70,"agree",0,0),(72,G,1,70,"add",0,0),(73,M,1,72,"agree",0,0),(74,B,1,73,"agree",0,0),
(75,T,0,None,None,0,0,"ritual call to vote"),(76,V,0,75,"agree",0,0,"agreement only"),(77,G,0,75,"agree",0,0,"agreement only"),(78,M,0,75,"agree",0,0,"ritual"),(79,B,0,75,"agree",0,0,"ritual"),
])
c=mk([
(5,T,2,None,None,0,0),(6,V,1,5,"add",0,0),(7,G,2,None,None,0,0),(8,M,2,None,None,0,0),(9,B,2,None,None,0,0),
(30,T,2,None,None,0,0),(31,V,2,None,None,0,0),(32,G,2,None,None,0,0),(33,M,2,None,None,0,0),(34,B,2,None,None,0,0),
(35,T,1,32,"add",0,0),(36,V,1,33,"add",0,0),(37,G,0,35,"agree",0,0,"repeats [32]"),(38,M,1,36,"agree",0,0),(39,B,1,33,"add",0,0),
(55,T,1,None,None,0,0),(56,V,1,55,"add",0,0),(57,G,1,55,"add",0,0),(58,M,2,None,None,0,0),(59,B,1,57,"add",0,0),
(60,T,1,57,"add",0,0),(61,V,1,60,"object",1,0),(62,G,1,61,"object",1,0),(63,M,1,60,"agree",0,0),(64,B,1,60,"add",0,0),
(65,T,0,None,None,0,0,"restates [60]"),(66,V,0,None,None,0,0,"repeats [61]"),(67,G,1,None,None,0,0),(68,M,1,None,None,0,0),(69,B,1,None,None,0,0),
])
json.dump({"candidate_selection_0003__multi-public.md":a,"candidate_selection_0003__single-batch-process.md":b,"candidate_selection_0003__single-batch-stepped.md":c},open("out/sonnet_12.json","w"),ensure_ascii=False)
print(len(a),len(b),len(c))
