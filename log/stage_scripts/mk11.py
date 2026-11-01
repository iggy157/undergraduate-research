import re,json
A,Ad,O,G='answer','add','object','agree'
N=None
d={}
d['candidate_selection_0002__single-online.md']={
5:(1,N,N,0,0,''),6:(1,N,N,0,0,''),7:(1,N,N,0,0,''),8:(1,N,N,0,0,''),9:(1,N,N,0,0,''),
10:(1,9,Ad,0,0,''),11:(1,10,A,0,0,''),12:(0,11,G,0,1,'agreement, repeats [11]'),13:(0,12,G,0,1,'agreement plus enthusiasm'),
14:(0,12,G,0,1,'repeats agreement'),15:(0,14,G,0,1,'repeats agreement'),17:(0,15,G,0,1,'repeats agreement'),18:(0,17,G,0,1,'repeats agreement'),
20:(0,18,G,0,1,'closing remark'),
35:(1,N,N,0,0,''),36:(2,N,N,0,0,''),37:(2,N,N,0,0,''),38:(2,N,N,0,0,''),39:(2,N,N,0,0,''),
40:(2,37,Ad,0,0,''),41:(1,40,A,0,0,''),42:(0,40,G,0,0,'repeats [37]'),43:(1,40,Ad,0,0,''),44:(1,43,A,0,0,''),
45:(1,44,Ad,0,0,''),46:(1,45,Ad,0,0,''),47:(0,46,Ad,0,0,'repeats credit-line point [37]'),
48:(1,46,O,1,0,''),49:(1,48,Ad,0,0,''),50:(0,49,G,0,1,'restates the dilemma of [45]'),
51:(1,50,Ad,0,0,''),52:(1,51,Ad,0,0,''),53:(0,51,G,0,1,'repeats [48]'),54:(0,53,G,0,1,'repeats earlier criteria'),
60:(1,N,N,0,0,''),61:(1,N,N,0,0,''),62:(1,61,O,1,0,''),63:(2,N,N,0,0,''),64:(2,63,O,1,0,''),
65:(1,62,Ad,0,0,''),66:(1,65,A,0,0,''),67:(1,65,A,0,0,''),68:(1,67,O,0,0,''),69:(1,68,A,0,0,''),
70:(0,69,G,0,1,'repeats own stance of [60]'),71:(1,70,Ad,0,0,''),72:(0,67,G,0,0,'repeats [67]'),73:(1,69,A,0,0,''),
74:(0,73,G,0,0,'repeats [69]'),75:(1,74,G,0,1,'restates reasons'),76:(1,75,G,0,0,''),77:(1,76,G,0,0,''),78:(1,77,G,0,0,''),79:(1,78,G,0,0,'')}
d['candidate_selection_0003__multi-private-process.md']={
5:(1,N,N,0,0,''),6:(1,5,Ad,0,0,''),7:(1,5,Ad,0,0,''),8:(1,7,Ad,0,0,''),9:(1,8,Ad,0,0,''),
10:(1,6,Ad,0,1,'closing sentence adds nothing'),11:(0,10,G,0,1,'restates own plan from [6]'),12:(1,11,O,0,0,''),
13:(1,12,Ad,0,0,''),14:(1,13,Ad,0,0,''),15:(0,14,O,1,0,'repeats utility priority of [5]'),
16:(1,15,Ad,0,0,''),17:(0,16,O,1,0,'repeats staff point of [12]'),18:(0,17,O,1,0,'repeats [13]'),
19:(1,15,O,0,1,'sentiment opening'),20:(0,19,O,1,1,'repeats utility priority of [5]'),
21:(0,20,G,0,1,'agreement and closing'),22:(0,20,G,0,1,'agreement and closing'),23:(0,20,G,0,1,'agreement and closing'),24:(0,20,G,0,1,'closing sentiment'),
35:(2,N,N,0,0,''),36:(2,N,N,0,0,''),37:(2,N,N,0,0,''),38:(2,N,N,0,0,''),39:(2,N,N,0,0,''),
40:(1,36,Ad,0,0,''),41:(1,40,Ad,0,0,''),42:(1,41,O,1,0,''),43:(1,42,O,1,0,''),44:(1,41,O,1,0,''),
45:(1,44,O,1,0,''),46:(0,45,Ad,0,0,'repeats off-site cost of [41]'),47:(0,46,O,1,0,'repeats [42]'),
48:(0,47,O,1,0,'repeats [43]'),49:(1,48,Ad,0,0,''),50:(1,49,Ad,0,0,''),51:(1,50,Ad,0,0,''),52:(1,51,Ad,0,0,''),
53:(0,52,Ad,0,0,'repeats [38]'),54:(1,53,Ad,0,0,''),
60:(2,N,N,0,0,''),61:(2,60,Ad,0,0,''),62:(1,61,O,0,0,''),63:(1,62,O,1,0,''),64:(1,63,Ad,0,0,''),
65:(1,64,Ad,0,0,''),66:(1,65,Ad,0,0,''),67:(1,66,O,1,0,''),68:(0,67,O,1,0,'repeats [63]'),
69:(1,67,O,1,0,''),70:(1,69,O,1,0,''),71:(1,70,Ad,0,0,''),72:(0,71,O,1,0,'repeats [67]'),
73:(0,72,O,1,0,'repeats [63]'),74:(0,72,O,1,0,'repeats [64]'),75:(1,74,Ad,0,0,''),76:(1,75,G,0,0,''),
77:(1,75,O,1,0,''),78:(1,77,O,1,0,''),79:(1,78,G,0,1,'closing quip')}
d['candidate_selection_0003__multi-private.md']={
5:(1,N,N,0,0,''),6:(1,5,Ad,0,0,''),7:(1,N,N,0,0,''),8:(1,N,N,0,0,''),9:(1,8,Ad,0,0,''),
10:(0,9,G,0,1,'no new content'),11:(0,10,G,0,1,'summary pleasantry'),12:(0,11,G,0,1,'agreement, no new content'),
13:(0,12,G,0,1,'agreement, no new content'),14:(0,13,G,0,1,'pleasantry'),15:(0,14,G,0,1,'repeats readiness'),
16:(0,15,G,0,1,'repeats readiness'),17:(0,16,G,0,1,'repeats readiness'),18:(0,17,G,0,1,'repeats readiness'),19:(0,18,G,0,1,'pleasantry'),
35:(2,N,N,0,0,''),36:(2,N,N,0,0,''),37:(2,N,N,0,0,''),38:(2,N,N,0,0,''),39:(2,N,N,0,0,''),
40:(1,36,Ad,0,0,''),41:(1,40,Ad,0,0,''),42:(1,41,Ad,0,0,''),43:(1,42,Ad,0,0,''),44:(1,43,Ad,0,1,'sentiment framing'),
45:(1,44,Ad,0,0,''),46:(0,45,G,0,0,'repeats [41]'),47:(0,46,Ad,0,0,'repeats [37]/[42]'),
48:(0,47,O,1,0,'repeats [43]'),49:(0,48,Ad,0,1,'repeats [39]/[44]'),50:(1,49,Ad,0,0,''),
51:(0,50,G,0,0,'repeats [41] and [50]'),52:(0,50,Ad,0,0,'repeats [47]'),53:(0,52,Ad,0,0,'repeats [38]'),54:(0,53,G,0,1,'summary pleasantry'),
60:(2,N,N,0,0,''),61:(1,60,Ad,0,0,''),62:(1,60,Ad,0,0,''),63:(2,60,Ad,0,0,''),64:(2,60,Ad,0,0,''),
65:(1,61,A,0,0,''),66:(1,65,Ad,0,0,''),67:(0,66,G,0,1,'repeats [62]'),68:(0,66,Ad,0,0,'repeats [63]'),
69:(0,68,G,0,1,'sentiment, repeats earlier points'),70:(1,69,G,0,1,'restates reasons'),71:(1,70,G,0,0,''),
72:(1,71,G,0,1,'restates [62]'),73:(1,72,G,0,1,'restates [63]'),74:(1,73,G,0,1,'sentiment opening'),
75:(0,74,G,0,1,'satisfaction, restates reasons'),77:(0,75,G,0,1,'satisfaction statement'),79:(0,77,G,0,1,'satisfaction statement'),
81:(0,79,G,0,1,'satisfaction statement'),83:(0,81,G,0,1,'closing remark')}
out={}
for f,m in d.items():
    L=[]
    for line in open('games/'+f):
        x=re.match(r'- \[(\d+)\] \*\*(\w+)\*\*',line)
        if not x: continue
        s=int(x[1]);c,rt,ty,rb,pd,note=m[s]
        e={"seq":s,"speaker":x[2],"content":c,"resp":0 if rt is None else 1,"resp_to":rt,"resp_type":ty,"rebut":rb,"padded":pd}
        if note: e["note"]=note
        L.append(e)
    assert len(L)==len(m),(f,len(L),len(m))
    out[f]=L
json.dump(out,open('out/sonnet_11.json','w'),ensure_ascii=False)
