import re,json
A,O,D,N='add','object','agree','answer'
def P(s):  # seq:content:resp_to:type:rebut:padded:note
    r=[]
    for l in s.strip().split('\n'):
        f=l.split('|'); seq,c,rt,ty,rb,pd=f[:6]; note=f[6] if len(f)>6 else ''
        r.append((int(seq),int(c),int(rt) if rt else None,ty or None,int(rb),int(pd),note))
    return r
D1=P("""5|2|||0|0
6|1|5|add|0|1|general excitement sentiment
7|1|6|object|1|0
8|0|7|agree|0|0|repeats Toshio's point
9|1|6|add|0|1|cheerleading filler
10|2|9|answer|0|0
11|1|10|answer|0|0
12|1|11|object|1|0
13|1|12|add|0|1|thanks and apology filler
14|1|12|agree|0|1|flattery filler
15|1|14|answer|0|0
16|0|15|agree|0|1|agreement only, filler
17|1|15|add|0|0
18|0|17|agree|0|0|agrees with baseline idea
19|1|18|agree|0|1|filler before question
20|0|19|answer|0|1|closing pleasantry
21|0|||0|1|farewell
23|0|||0|1|farewell
25|0|||0|1|farewell
27|0|||0|1|farewell
35|1|||0|0
36|1|35|add|0|1|filler exclamations
37|2|36|answer|0|1|repeats earlier Seer-risk remark
38|1|37|add|0|0
39|1|37|object|1|1|repeats denial
40|2|39|add|0|0
41|1|37|add|0|1|filler
42|1|40|answer|0|0
43|2|37|add|0|0
44|0|43|add|1|1|repeats denial from [39]
45|1|43|answer|0|0
46|1|44|object|1|1|filler remarks
47|1|44|object|1|1|repeats certainty
48|1|47|add|0|0
49|1|48|object|0|1|repeats pleas
50|1|49|object|1|0
51|1|50|agree|0|1|farewell filler
52|1|50|agree|0|1|restates reasoning
53|1|52|agree|0|1|restates reasoning
54|1|53|object|1|1|repeats denial""")
D2=P("""5|2|||0|0
6|1|||0|0
7|1|6|object|1|0
8|0|7|agree|0|0|echoes calm approach
9|0|5|agree|0|1|friendliness filler
10|2|6|object|0|0
11|1|10|answer|0|0
12|1|10|answer|0|0
13|0|12|agree|0|0|agrees with Toshio
14|0|||0|1|enthusiasm filler
15|1|||0|0
16|1|15|add|0|1|playful filler
17|1|15|agree|0|0
18|0|17|agree|0|0|vague agreement
19|0|||0|1|trust filler
20|0|||0|1|ritual wrap-up
21|0|||0|1|farewell
31|1|||0|0
32|1|31|add|0|0
33|1|32|add|0|0
34|1|33|add|0|0
35|1|33|object|1|0
36|1|35|add|0|0
37|1|35|add|0|1|jokes
38|1|36|add|0|0
39|1|38|agree|0|0
40|0|38|object|1|0|repeats denial from [35]
41|1|38|add|0|0
42|1|40|add|0|0
43|1|41|answer|0|0
44|1|42|object|1|0
45|1|43|object|1|0
46|2|42|add|0|0
47|1|46|object|1|1|plea filler
48|0|46|agree|0|0|repeats target
49|1|48|add|0|0
50|0|49|object|1|0|repeats plea""")
D3=P("""5|1|||0|0
6|0|||0|1|no substance
7|1|5|add|0|0
8|0|7|agree|0|0|agrees
9|0|6|agree|0|1|enthusiasm only
10|1|6|object|0|0
11|0|10|answer|0|0|restates intent to suspect
14|1|11|object|0|0
15|1|||0|0
16|1|15|add|0|0
17|1|16|object|1|0
18|1|16|object|1|0
19|1|18|add|0|0
20|1|19|answer|0|0
21|0|||0|1|filler
31|1|||0|0
32|0|31|add|0|1|no information given
33|2|||0|0
34|1|33|add|0|0
35|1|33|object|1|0
36|1|33|add|0|0
37|0|33|add|0|1|reaction only
38|1|34|answer|0|0
39|0|38|agree|0|0|repeats Jonathan's [34] point
40|1|38|object|1|0
41|1|38|add|0|0
42|1|38|object|1|0
43|0|42|object|1|0|repeats accusation
44|0|41|agree|0|0|restates [41]
45|0|||0|0|repeats denial
46|1|43|agree|0|0
47|1|||0|0
48|1|||0|0
49|1|||0|0
50|0|||0|0|complaint only""")
base='games/'
out={}
for fn,rows in [('aiwolf_0002__multi-public',D1),('aiwolf_0002__single-batch-process',D2),('aiwolf_0002__single-batch-stepped',D3)]:
    txt=open(base+fn+'.md').read()
    sp={int(m.group(1)):m.group(2) for m in re.finditer(r'^- \[(\d+)\] \*\*(.+?)\*\*:',txt,re.M)}
    assert sorted(sp)==[r[0] for r in rows],fn
    L=[]
    for seq,c,rt,ty,rb,pd,note in rows:
        d={"seq":seq,"speaker":sp[seq],"content":c,"resp":1 if rt else 0,"resp_to":rt,"resp_type":ty if rt else None,"rebut":rb,"padded":pd}
        if rb or pd or c==0: d["note"]=note or "see text"
        L.append(d)
    out[fn+'.md']=L
json.dump(out,open('out/sonnet_03.json','w'),indent=1)
