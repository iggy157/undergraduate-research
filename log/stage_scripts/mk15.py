import json
N={'Mio':'Mio','Sh':'Shizue','Ry':'Ryuji','Ri':'Rin','Mi':'Misaki'}
# (seq,spk,content,resp_to,type,rebut,padded,note)
def b(seq,sp,c,rt=None,ty=None,rb=0,pd=0,note=None):
    d={"seq":seq,"speaker":N[sp],"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":rb,"padded":pd}
    if note: d["note"]=note
    return d
F1=[b(5,'Mio',1),b(6,'Sh',1),b(7,'Ry',1),b(8,'Ri',1),b(9,'Mi',1),b(10,'Mio',1,9,'add'),b(11,'Sh',1),b(12,'Ry',1),b(13,'Ri',1),
b(14,'Mi',1,10,'add'),b(15,'Mio',1),b(16,'Sh',1,15,'add'),b(17,'Ry',1),b(18,'Ri',1),b(19,'Mi',1,18,'add'),
b(35,'Mio',2),b(36,'Sh',2),b(37,'Ry',2),b(38,'Ri',2),b(39,'Mi',2),b(40,'Mio',1,37,'add'),b(41,'Sh',1),b(42,'Ry',1,40,'add'),
b(43,'Ri',0,note="repeats [38]"),b(44,'Mi',1,40,'add'),b(45,'Mio',1,44,'add'),b(46,'Sh',1,45,'object',1),b(47,'Ry',0,note="repeats [37]"),
b(48,'Ri',1),b(49,'Mi',1),
b(60,'Mio',1),b(61,'Sh',1),b(62,'Ry',1),b(63,'Ri',1),b(64,'Mi',1),b(65,'Mio',1,61,'add'),b(66,'Sh',1,65,'answer'),
b(67,'Ry',1,66,'object',1),b(68,'Ri',1,67,'add'),b(69,'Mi',1,68,'add'),b(70,'Mio',1,69,'add'),b(71,'Sh',1,70,'add'),
b(72,'Ry',0,note="repeats [62]"),b(73,'Ri',0,72,'agree',note="bare agreement"),b(74,'Mi',0,note="repeats [64]")]
F2=[b(5,'Mio',1),b(6,'Sh',1),b(7,'Ry',1),b(8,'Ri',1),b(9,'Mi',1),b(10,'Mio',1,9,'add'),b(11,'Sh',1),b(12,'Ry',1),b(13,'Ri',1),
b(14,'Mi',1,10,'add'),b(15,'Mio',1,14,'add'),b(16,'Sh',1,15,'add'),b(17,'Ry',1),b(18,'Ri',1),b(19,'Mi',0,note="repeats [14]"),
b(35,'Mio',2),b(36,'Sh',2),b(37,'Ry',2),b(38,'Ri',2),b(39,'Mi',1),b(40,'Mio',1,39,'add'),b(41,'Sh',1,40,'object',1),b(42,'Ry',1,40,'add'),
b(43,'Ri',0,note="repeats [38]"),b(44,'Mi',1,40,'add'),b(45,'Mio',0,note="repeats [40]/[35]"),b(46,'Sh',1),b(47,'Ry',0,note="repeats [37]"),
b(48,'Ri',1),b(49,'Mi',1,46,'add'),
b(60,'Mio',1),b(61,'Sh',1,60,'object',1),b(62,'Ry',1),b(63,'Ri',1),b(64,'Mi',1),b(65,'Mio',1,63,'object',1),b(66,'Sh',1,64,'object',1),
b(67,'Ry',1,66,'add'),b(68,'Ri',1,65,'add'),b(69,'Mi',1,68,'object',1),b(70,'Mio',1,69,'agree'),b(71,'Sh',1),b(73,'Ri',1,71,'add')]
F3=[b(5,'Mio',1),b(6,'Sh',2),b(7,'Ry',2),b(8,'Ri',2),b(9,'Mi',2),b(10,'Mio',1,7,'add'),b(11,'Sh',1,10,'add',pd=1,note="praise and 'happy with choices' add nothing"),
b(12,'Ry',1,10,'answer'),b(13,'Ri',0,note="repeats [8]",pd=1),b(14,'Mi',1,12,'agree'),
b(15,'Mio',0,note="repeats [5]"),b(16,'Sh',0,note="repeats [6]",pd=1),b(17,'Ry',0,note="repeats [7]",pd=1),b(18,'Ri',0,note="repeats [8]",pd=1),
b(19,'Mi',0,note="repeats [14]",pd=1),b(20,'Mio',0,note="ritual closing"),b(21,'Sh',0,note="ritual closing",pd=1),b(22,'Ry',0,note="repeats [17]"),
b(23,'Ri',0,note="ritual closing"),b(24,'Mi',0,note="ritual closing"),
b(35,'Mio',2),b(36,'Sh',2),b(37,'Ry',2),b(38,'Ri',2),b(39,'Mi',2),b(40,'Mio',1,39,'add'),b(41,'Sh',1,40,'add',pd=1,note="opening praise adds nothing"),
b(42,'Ry',1,40,'answer'),b(43,'Ri',1,35,'add'),b(44,'Mi',1,43,'add'),b(45,'Mio',1,43,'add'),b(46,'Sh',2,45,'answer'),b(47,'Ry',1,43,'add'),
b(48,'Ri',1,47,'add'),b(49,'Mi',1,48,'add'),b(50,'Mio',1,49,'add'),b(51,'Sh',1,50,'answer'),
b(52,'Ry',0,51,'agree',pd=1,note="endorses [51] with restated reasons"),b(53,'Ri',1,51,'add'),b(54,'Mi',1,51,'add'),
b(60,'Mio',1,51,'add'),b(61,'Sh',1),b(62,'Ry',1),b(63,'Ri',1,pd=1,note="closing sentiment about the beach"),b(64,'Mi',1)]
o={"shared_living_0001__single-batch-stepped.md":F1,"shared_living_0001__single-batch.md":F2,"shared_living_0001__single-online.md":F3}
json.dump(o,open("out/sonnet_15.json","w"),ensure_ascii=False)
print({k:len(v) for k,v in o.items()})
