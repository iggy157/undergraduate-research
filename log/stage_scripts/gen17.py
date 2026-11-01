import json
R,M,S,Ma,A="Rin","Midori","Shunichi","May","Asuka"
def mk(rows):
    out=[]
    for r in rows:
        seq,sp,c,to,t,rb,pd,note=(list(r)+[0,0,""])[:8] if len(r)<8 else r
        d={"seq":seq,"speaker":sp,"content":c,"resp":1 if to else 0,"resp_to":to,"resp_type":t if to else None,"rebut":rb,"padded":pd}
        if rb or pd or c==0: d["note"]=note or "adds nothing new"
        out.append(d)
    return out
p=[(5,R,2,None,None,0,0,""),(6,M,1,5,"add",0,0,""),(7,S,1,None,None,0,0,""),(8,Ma,1,None,None,0,0,""),(9,A,1,None,None,0,0,""),
(10,R,1,9,"add",0,0,""),(11,M,1,8,"add",0,0,""),(12,S,1,10,"add",0,0,""),(13,Ma,1,11,"add",0,0,""),(14,A,1,7,"add",0,0,""),
(35,R,2,None,None,0,0,""),(36,M,1,None,None,0,0,""),(37,S,2,None,None,0,0,""),(38,Ma,2,None,None,0,0,""),(39,A,2,None,None,0,0,""),
(40,R,1,36,"add",0,0,""),(41,M,0,37,"add",0,0,"repeats cost point of [36]"),(42,S,1,40,"object",1,0,""),(43,Ma,1,35,"add",0,0,""),(44,A,1,40,"object",0,0,""),
(45,R,0,None,None,0,0,"repeats [5]"),(46,M,1,45,"add",0,0,""),(47,S,1,46,"add",0,0,""),(48,Ma,0,None,None,0,0,"repeats [38]/[43]/[13]"),(49,A,1,None,None,0,0,""),
(60,R,1,None,None,0,0,""),(61,M,1,60,"add",0,0,""),(62,S,1,60,"add",0,0,""),(63,Ma,1,62,"add",0,0,""),(64,A,1,62,"add",0,0,""),
(65,R,1,64,"add",0,0,""),(66,M,1,62,"add",0,0,""),(67,S,1,66,"answer",0,0,""),(68,Ma,0,65,"add",0,0,"repeats [63]"),(69,A,1,65,"answer",0,0,""),
(70,R,0,None,None,0,0,"repeats [60]"),(71,M,0,70,"agree",0,0,"repeats [61]"),(72,S,0,None,None,0,0,"repeats [62]"),(73,Ma,0,None,None,0,0,"repeats [63]"),(74,A,0,None,None,0,0,"repeats [64]")]
s=[(5,R,2,None,None,0,0,""),(6,M,2,None,None,0,0,""),(7,S,1,None,None,0,0,""),(8,Ma,2,None,None,0,0,""),(9,A,2,None,None,0,0,""),
(30,R,2,None,None,0,0,""),(31,M,2,None,None,0,0,""),(32,S,2,None,None,0,0,""),(33,Ma,2,None,None,0,0,""),(34,A,2,None,None,0,0,""),
(35,R,1,31,"add",0,0,""),(36,M,1,35,"answer",0,0,""),(37,S,1,32,"add",0,0,""),(38,Ma,1,37,"add",0,0,""),(39,A,1,38,"add",0,0,""),
(40,R,1,39,"add",0,0,""),(41,M,1,39,"add",0,0,""),(42,S,1,41,"add",0,0,""),(43,Ma,1,39,"add",0,0,""),(44,A,1,42,"answer",0,0,""),
(45,R,1,None,None,0,0,""),(46,M,0,45,"agree",0,0,"repeats [31]/[36]"),(47,S,1,46,"add",0,0,""),(48,Ma,0,47,"add",0,0,"repeats [43]"),(49,A,0,None,None,0,0,"repeats [39]/[44]"),
(55,R,1,None,None,0,0,""),(56,M,1,None,None,0,0,""),(57,S,0,None,None,0,0,"repeats [47]"),(58,Ma,0,None,None,0,0,"repeats [48]"),(59,A,0,None,None,0,0,"repeats [49]")]
b=[(5,R,2,None,None,0,0,""),(6,M,2,None,None,0,0,""),(7,S,1,None,None,0,0,""),(8,Ma,2,None,None,0,0,""),(9,A,2,None,None,0,0,""),
(30,R,2,None,None,0,0,""),(31,M,2,None,None,0,0,""),(32,S,2,None,None,0,0,""),(33,Ma,2,None,None,0,0,""),(34,A,2,None,None,0,0,""),
(35,R,1,33,"add",0,0,""),(36,M,1,34,"add",0,0,""),(37,S,1,36,"add",0,0,""),(38,Ma,0,35,"agree",0,0,"repeats [33]"),(39,A,1,37,"add",0,0,""),
(40,R,1,None,None,0,0,""),(41,M,0,40,"agree",0,0,"repeats cost point"),(42,S,1,32,"add",0,0,""),(43,Ma,0,None,None,0,0,"repeats [33]"),(44,A,1,None,None,0,0,""),
(55,R,1,None,None,0,0,""),(56,M,1,44,"add",0,0,""),(57,S,1,None,None,0,0,""),(58,Ma,1,None,None,0,0,""),(59,A,1,None,None,0,0,""),
(60,R,0,59,"agree",0,0,"cheer"),(61,M,1,59,"add",0,0,""),(62,S,1,61,"answer",0,0,""),(63,Ma,0,None,None,0,0,"repeats [58]/[43]"),(64,A,0,61,"answer",0,0,"repeats [59]"),
(65,R,0,None,None,0,0,"repeats [55]"),(66,M,0,None,None,0,0,"repeats [56]"),(67,S,0,None,None,0,0,"repeats [57]"),(68,Ma,0,None,None,0,0,"repeats [58]"),(69,A,0,None,None,0,0,"repeats [59]")]
json.dump({"shared_living_0002__single-batch-process.md":mk(p),"shared_living_0002__single-batch-stepped.md":mk(s),"shared_living_0002__single-batch.md":mk(b)},open("out/sonnet_17.json","w"),ensure_ascii=False)
print(len(p),len(s),len(b))
