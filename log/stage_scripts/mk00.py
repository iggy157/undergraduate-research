import re,json
B="/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot8v2/"
# seq: (content,resp_to,type,rebut,padded,note)
A,G,O,D='add','agree','object','answer'
def n(c,to=None,t=None,r=0,p=0,note=""): return (c,to,t,r,p,note)
F={}
F["aiwolf_0001__multi-private-process.md"]={
5:n(2),6:n(1,5,D),7:n(1,5,A),8:n(1,6,O,1),9:n(1,5,D),10:n(2,9,O,1),11:n(1,10,D),12:n(1,10,D),13:n(1,12,A),14:n(1,12,A),
15:n(1,14,A),16:n(0,15,G,0,1,"agrees with [15]"),17:n(1,15,A),18:n(0,17,G,0,1,"echoes [17]"),19:n(1,17,O),20:n(1,19,O,0,1),
22:n(0,20,G,0,1,"farewell"),24:n(0,note="farewell, repeats own plan [7]",p=1),26:n(0,note="farewell"),28:n(0,note="farewell",p=1),
36:n(1),37:n(0,36,D,0,1,"no information given"),38:n(1,36,A),39:n(1,38,O,1),40:n(1,38,O,1),41:n(1,39,A),42:n(0,40,A,0,1,"generic plea for patience"),
43:n(1,40,O,1),44:n(1,43,A),45:n(1,43,O,1),46:n(1,45,A),47:n(1,46,D,0,1),48:n(2,47,O,1),49:n(1,48,O,1),50:n(1,48,O,1),51:n(1,50,A),
52:n(1,51,D,0,1),53:n(1,51,D),54:n(1,53,O,1),55:n(0,53,O,1,0,"repeats [45]/[50]"),
69:n(1),70:n(0,69,A,0,1,"expresses grief only"),71:n(1,69,A),72:n(1,71,A),73:n(0,72,D,0,1,"no substantive answer"),74:n(1,73,A),75:n(1,74,A),
76:n(1,75,D),77:n(1,76,O,1),78:n(1,77,A),79:n(0,78,O,0,1,"emotional plea, no new point"),80:n(1,79,A)}
F["aiwolf_0001__multi-private.md"]={
5:n(2),6:n(0,5,G,0,1,"agrees with [5]"),7:n(1,5,A),8:n(0,7,G,0,1,"agrees with [7]"),9:n(0,5,G,0,1,"agrees with everyone"),10:n(1,9,A),11:n(1,10,D),
12:n(1,11,O,1),13:n(1,12,A),14:n(1,10,D),15:n(1,14,O,1),16:n(0,15,G,0,1,"agrees with [15]"),17:n(1,15,A),18:n(0,17,G,0,1,"echoes [17]"),
19:n(0,17,A,0,0,"no new point"),20:n(0,note="closing"),22:n(0,note="farewell"),24:n(0,note="farewell"),26:n(0,note="farewell"),28:n(0,note="farewell"),
36:n(1),37:n(0,36,D,0,1,"no information given"),38:n(1,36,A),39:n(1,38,D),40:n(1,39,A),41:n(1,39,A),42:n(1,39,A),43:n(2,39,A),44:n(1,43,D),
45:n(1,44,A,0,1),46:n(1,44,O,1),47:n(1,46,O),48:n(1,47,O,1),49:n(1,48,D),50:n(2,48,O,1),51:n(1,50,A),52:n(1,51,D,0,1),53:n(1,51,D),54:n(1,51,D),55:n(1,51,D,0,1),
68:n(1),69:n(1,68,A,0,1),70:n(1,68,A),71:n(1,70,A),72:n(1,70,A),73:n(1,72,A),74:n(1,72,A),75:n(1,74,O,1),76:n(1,75,D),77:n(1,76,D,0,1),
78:n(2,76,D),79:n(0,78,O,1,0,"repeats [75]"),80:n(1,79,A),81:n(0,79,A,0,1,"generic plea for calm"),82:n(1,81,O,1),83:n(0,82,O,1,0,"repeats [79]")}
F["aiwolf_0001__multi-public.md"]={
5:n(2),6:n(1,5,D),7:n(1,5,A),8:n(0,7,G,0,1,"agrees with [7]"),9:n(1,5,D),10:n(1,9,O,1),11:n(1,10,D),12:n(1,11,O,1),13:n(0,12,G,0,0,"repeats [12]"),
14:n(1,13,A),15:n(1,14,A),16:n(1,15,D),17:n(1,16,O,1),18:n(0,17,G,0,1,"echoes [17]"),19:n(0,18,G,0,0,"acknowledges [18]"),
20:n(0,note="closing"),22:n(0,note="farewell"),24:n(0,note="farewell"),26:n(0,note="farewell"),28:n(0,note="farewell"),
36:n(1),37:n(0,36,D,0,1,"no information given"),38:n(1,36,A),39:n(2,38,D),40:n(1,39,A),41:n(1,39,A),42:n(1,41,D,1),43:n(2,42,O,1),44:n(1,43,D),
45:n(1,44,G),46:n(1,42,O,1),47:n(0,46,D,0,1,"restates denial"),48:n(1,47,O,1),49:n(1,48,A),50:n(1,49,G),51:n(1,49,A),
53:n(0,51,G,0,1,"farewell and repeated plea"),55:n(1,51,A),57:n(1,55,G),59:n(0,57,G,0,1,"vote already stated in [50]")}
out={}
for f,d in F.items():
    L=[]
    for line in open(B+"games/"+f):
        m=re.match(r"- \[(\d+)\] \*\*(\w+)\*\*",line)
        if not m: continue
        s=int(m[1]); c,to,t,r,p,note=d[s]
        o={"seq":s,"speaker":m[2],"content":c,"resp":1 if to else 0,"resp_to":to,"resp_type":t if to else None,"rebut":r,"padded":p}
        if note or c==0 or r or p: o["note"]=note or "see text"
        L.append(o)
    assert len(L)==len(d),(f,len(L),len(d))
    out[f]=L
json.dump(out,open(B+"out/sonnet_00.json","w"),ensure_ascii=False)
