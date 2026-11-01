import json
N={'Mi':'Minako','S':'Shizue','Z':'Mizuki','B':'Benjamin','K':'Kenji'}
# seq,sp,content,resp_to,type,rebut,padded,note
def build(rows):
    out=[]
    for r in rows:
        seq,sp,c,rt,ty,rb,pd,nt=(list(r)+[None]*8)[:8]
        d={"seq":seq,"speaker":N[sp],"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":rb or 0,"padded":pd or 0}
        if (rb or c==0 or pd) : d["note"]=nt or "no new content"
        out.append(d)
    return out
P=[(5,'Mi',1),(6,'S',0,5,'agree',0,1,"pleasantry agreeing with [5]"),(7,'Z',1,5,'add'),(8,'B',1,5,'add'),
(9,'K',1,7,'add'),(10,'Mi',1,9,'answer'),(11,'S',0,None,None,0,1,"general sentiment only"),(12,'Z',1,9,'add'),
(13,'B',1,12,'add'),(14,'K',1,13,'add'),(15,'Mi',1,14,'object',1),(16,'S',0,15,'agree',0,0,"agrees with [15]"),
(17,'Z',0,15,'agree',0,0,"agrees with [15]"),(18,'B',0,15,'agree',0,0,"agrees with [15]"),(19,'K',0,15,'agree',0,0,"accepts [15]"),
(20,'Mi',1,19,'add'),(21,'S',0,None,None,0,0,"ritual"),(22,'Z',0,None,None,0,0,"ritual"),(23,'B',0,None,None,0,0,"farewell"),(24,'K',0,None,None,0,0,"farewell"),
(31,'Mi',1),(32,'S',1,31,'answer'),(33,'Z',1),(34,'B',1,33,'answer'),(35,'K',1,34,'object',1),(36,'Mi',1,34,'add'),
(37,'S',1,34,'object',1),(38,'Z',1,34,'add'),(39,'B',1,36,'answer'),(40,'K',1,39,'object',1),(41,'Mi',1,40,'add'),
(42,'S',0,None,None,0,0,"repeats denial in [37]"),(43,'Z',1,40,'object',1),(44,'B',0,40,'add',0,0,"repeats claim from [34]"),
(45,'K',0,43,'object',1,0,"repeats suspicion in [40]"),(46,'Mi',1,45,'object',1),(47,'S',0,None,None,0,0,"repeats denial"),
(48,'Z',1,47,'object',1),(49,'B',0,None,None,0,0,"repeats claim"),(50,'K',1,46,'add')]
S=[(5,'Mi',1),(6,'S',0,5,'agree',0,1,"pleasantry agreeing with [5]"),(7,'Z',1,5,'add'),(8,'B',1,5,'add'),(9,'K',0,None,None,0,0,"enthusiasm only"),
(10,'Mi',1),(11,'S',1,10,'answer'),(12,'Z',1,11,'object',1),(13,'B',1,12,'agree'),(14,'K',1,12,'add'),
(31,'Mi',1),(32,'S',1,31,'answer'),(33,'Z',2,32,'add'),(34,'B',1,33,'answer'),(35,'K',1,34,'add'),(36,'Mi',1,34,'add'),
(37,'S',0,34,'add',0,0,"vague support, no new point"),(38,'Z',1,34,'add'),(39,'B',2,36,'answer'),(40,'K',1,39,'object',1),
(41,'Mi',1,39,'add'),(42,'S',1,41,'answer'),(43,'Z',1,39,'add'),(44,'B',1,43,'answer'),(45,'K',1,44,'agree'),
(46,'Mi',1,44,'agree'),(47,'S',0,None,None,0,0,"apology only"),(48,'Z',1,44,'agree'),(49,'B',0,None,None,0,0,"repeats [39]"),(50,'K',1,48,'agree')]
T=[(5,'Mi',1),(6,'S',0,5,'agree',0,1,"pleasantry agreeing with [5]"),(7,'Z',1,5,'add'),(8,'B',1,5,'add'),(9,'K',0,None,None,0,0,"enthusiasm only"),
(10,'Mi',1),(11,'S',1,10,'answer'),(12,'Z',1,11,'object',1),(13,'B',1,12,'agree'),(14,'K',1,12,'add'),
(31,'Mi',1),(32,'S',1,31,'answer'),(33,'Z',0,32,'add',0,1,"generic call for vigilance"),(34,'B',1,31,'answer'),(35,'K',1,34,'add'),(36,'Mi',1,34,'add'),
(37,'S',1,34,'object',1),(38,'Z',1,34,'add'),(39,'B',1,36,'answer'),(40,'K',1,39,'object',1),(41,'Mi',1,40,'object',1),
(42,'S',0,None,None,0,0,"resignation, repeats [37]"),(43,'Z',0,40,'add',0,0,"repeats [38]"),(44,'B',0,40,'add',0,0,"repeats [34]"),
(45,'K',1,41,'agree'),(46,'Mi',1,44,'agree'),(47,'S',0,None,None,0,0,"closing sentiment"),(48,'Z',0,46,'agree',0,0,"repeats agreement"),
(49,'B',0,48,'agree',0,0,"procedural"),(50,'K',0,48,'agree',0,0,"repeats [45]")]
o={"games/aiwolf_0001__single-batch-process.md":build(P),"games/aiwolf_0001__single-batch-stepped.md":build(S),"games/aiwolf_0001__single-batch.md":build(T)}
json.dump(o,open('out/sonnet_01.json','w'),ensure_ascii=False)
print({k:len(v) for k,v in o.items()})
