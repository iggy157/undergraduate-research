import re,json
# seq: (content, resp_to, type, rebut, padded, note)
A,O,G,N='add','object','agree','answer'
def t(c,r=None,ty=None,rb=0,p=0,n=""): return (c,r,ty,rb,p,n)
priv={5:t(1,p=1,n="greeting opening"),6:t(1,5,A,p=1),7:t(1,5,A),8:t(1,7,A),9:t(0,7,G,n="agrees with [7]"),10:t(1,7,A),11:t(1,7,A),12:t(1),13:t(1),14:t(1),15:t(1,14,A),16:t(1,15,N),17:t(1,15,N),18:t(1,17,A),19:t(0,15,G,n="repeats own wait-for-data"),
20:t(0,19,G,p=1,n="closing pleasantry"),21:t(0,20,G,p=1,n="closing pleasantry"),22:t(0,20,G,p=1,n="restates [12],[17]"),23:t(0,20,G,p=1,n="closing"),24:t(0,20,G,p=1,n="closing"),
35:t(2),36:t(1),37:t(2),38:t(1),39:t(1,35,A),40:t(1,39,A),41:t(1,40,A),42:t(0,41,A,n="repeats [37]"),43:t(1,42,A),44:t(1,42,A),45:t(1,44,A),46:t(1,45,A),47:t(0,46,O,1,n="repeats [37]"),48:t(1,47,A),49:t(1,47,A),50:t(0,49,G,n="repeats [40]"),51:t(0,50,G,p=1,n="vague summary"),52:t(0,n="repeats [37]"),53:t(0,52,A,n="repeats [48]"),54:t(0,52,A,n="summarizes earlier points"),
60:t(1),61:t(1,60,O,1),62:t(1),63:t(1,62,A),64:t(1,60,A),65:t(1,61,O,1),66:t(1,65,O,1),67:t(1,66,O,1),68:t(1,67,A),69:t(0,66,O,1,n="repeats [64]"),70:t(0,66,O,n="repeats [60],[65]"),71:t(1,70,A),72:t(0,71,G,n="agrees with compromise"),73:t(1,71,G),74:t(1,71,G,p=1),75:t(0,74,G,p=1,n="already favored A in [60]"),76:t(1,75,G,p=1),77:t(0,76,G,p=1,n="repeats [72]"),78:t(0,77,G,p=1,n="vote already given in [73]"),79:t(0,77,G,p=1,n="vote already given in [74]")}
pub={5:t(2,p=1),6:t(1,5,N),7:t(1,5,N),8:t(1,5,N),9:t(1,5,N),10:t(1),11:t(1,10,A),12:t(0,10,A,n="repeats [7]"),13:t(1,12,A),14:t(1,12,A),15:t(1,14,G),16:t(1,15,O,1),17:t(1,16,O,1),18:t(1,15,N),19:t(1,18,A),20:t(0,19,G,p=1,n="closing"),22:t(0,20,G,p=1,n="closing"),24:t(0,20,G,p=1,n="closing"),26:t(0,20,G,p=1,n="closing"),28:t(0,20,G,p=1,n="closing"),
39:t(2),40:t(2),41:t(2),42:t(2,41,A),43:t(2),44:t(1,43,A),45:t(1,41,O,1),46:t(1,45,O,1),47:t(1,45,O,1),48:t(1,44,A),49:t(0,48,G,n="repeats [39],[42]"),50:t(1,49,A),51:t(1,50,A),52:t(1,51,A),53:t(1,52,A),54:t(0,53,G,n="repeats [53]"),55:t(1,53,G),56:t(1,53,A),57:t(0,56,G,p=1,n="cheering"),58:t(0,56,G,n="repeats [53]"),
64:t(1),65:t(1,64,G),66:t(1,65,G),67:t(1,66,G),68:t(1,67,G),69:t(0,68,G,p=1,n="no new content"),71:t(0,69,G,p=1,n="sentiment"),73:t(0,71,G,p=1,n="restates consensus"),75:t(0,73,G,p=1,n="sentiment"),77:t(1,75,A)}
sing={5:t(1),6:t(1,5,A),7:t(1),8:t(1),9:t(1),10:t(1,7,A),11:t(1,10,A),12:t(1,10,N),13:t(1),14:t(1),15:t(1),16:t(1),17:t(1),18:t(1),19:t(2),
35:t(2),36:t(1),37:t(2),38:t(2),39:t(2),40:t(1,39,N),41:t(1,38,A),42:t(0,38,G,n="repeats [37]"),43:t(1),44:t(2,40,N),45:t(1,44,A),46:t(1),47:t(0,n="repeats [37]"),48:t(0,n="repeats [43]"),49:t(1),
60:t(1),61:t(1,60,O,1),62:t(2),63:t(1,62,A),64:t(1,62,O,1),65:t(1,64,O,1),66:t(1,64,O,1),67:t(1,64,O,1),68:t(1),69:t(0,65,A,n="repeats [64]"),70:t(1,69,A),71:t(1,70,G),72:t(0,n="repeats [62],[67]"),73:t(0,71,G,n="repeats [68]"),74:t(1,73,G)}
d='games/'
res={}
for f,m in [('shared_living_0001__multi-private',priv),('shared_living_0001__multi-public',pub),('shared_living_0001__single-batch-process',sing)]:
    out=[]
    for l in open(d+f+'.md'):
        mm=re.match(r'- \[(\d+)\] \*\*(\w+)\*\*',l)
        if not mm: continue
        s=int(mm[1]); c,r,ty,rb,p,n=m[s]
        e={"seq":s,"speaker":mm[2],"content":c,"resp":1 if r else 0,"resp_to":r,"resp_type":ty if r else None,"rebut":rb,"padded":p}
        if n or rb or p or c==0: e["note"]=n or ("opposes [%s]"%r if rb else "padded")
        out.append(e)
    assert len(out)==len(m),(f,len(out),len(m))
    res[f+'.md']=out
json.dump(res,open('out/sonnet_14.json','w'),ensure_ascii=False)
print({k:len(v) for k,v in res.items()})
