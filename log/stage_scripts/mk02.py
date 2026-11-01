import json
B="/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot8v2/out/sonnet_02.json"
# seq,speaker,content,resp_to,type,rebut,padded,note
f1="""5 Minako 1 - - 0 0 ;
6 Shizue 1 5 add 0 1 general sentiment opener;
7 Mizuki 1 6 add 0 0 ;
8 Benjamin 1 7 add 0 0 ;
9 Kenji 0 - - 0 1 generic enthusiasm;
10 Minako 2 - - 0 0 ;
11 Shizue 1 10 answer 0 0 ;
12 Mizuki 1 10 answer 0 0 ;
13 Benjamin 1 12 add 0 0 ;
14 Kenji 1 10 add 0 0 ;
15 Minako 1 14 answer 0 0 ;
16 Shizue 0 15 agree 0 1 praise, no new point;
17 Mizuki 1 16 add 0 0 ;
18 Benjamin 0 17 agree 0 1 restates [17];
19 Kenji 0 17 agree 0 0 agreement only;
20 Minako 0 - - 0 0 closing;
21 Shizue 0 20 agree 0 1 farewell;
22 Mizuki 0 - - 0 0 repeats own plan/farewell;
23 Benjamin 0 - - 0 0 farewell;
24 Kenji 0 - - 0 0 farewell;
31 Minako 1 - - 0 0 ;
32 Shizue 1 31 answer 0 0 ;
33 Mizuki 1 31 add 0 0 ;
34 Benjamin 1 33 answer 0 0 ;
35 Kenji 0 34 agree 0 0 echoes [34];
36 Minako 1 34 add 0 0 ;
37 Shizue 1 36 answer 0 0 ;
38 Mizuki 1 37 object 0 0 ;
39 Benjamin 1 38 add 0 0 ;
40 Kenji 1 38 add 0 0 ;
41 Minako 0 40 add 0 1 urges answer to [40];
42 Shizue 1 40 answer 0 0 ;
43 Mizuki 1 42 object 1 0 ;
44 Benjamin 0 43 agree 0 1 repeats [43];
45 Kenji 2 43 add 0 0 ;
46 Minako 2 45 add 0 0 ;
47 Shizue 1 46 answer 0 0 ;
48 Mizuki 1 46 add 0 0 ;
49 Benjamin 1 46 add 0 0 ;
50 Kenji 1 46 agree 0 1 ;"""
f2="""5 Mizuki 2 - - 0 0 ;
6 Sakura 0 5 answer 0 1 greeting and fluff;
7 Toshio 1 5 add 0 0 ;
8 Jonathan 0 7 agree 0 1 restates [7];
9 Kenji 0 5 answer 0 1 generic enthusiasm;
10 Mizuki 1 9 add 0 0 ;
11 Sakura 1 10 object 0 1 ;
12 Toshio 1 11 add 0 0 ;
13 Jonathan 0 12 agree 0 0 repeats [12];
14 Kenji 1 10 add 0 0 ;
15 Mizuki 1 14 object 1 0 ;
16 Sakura 0 15 add 0 1 joke, no point;
17 Toshio 1 16 object 1 0 ;
18 Jonathan 0 17 agree 0 0 repeats [17];
19 Kenji 0 17 agree 0 1 generic reassurance;
20 Mizuki 0 - - 0 1 closing;
21 Sakura 0 - - 0 1 farewell;
22 Toshio 0 - - 0 0 farewell;
23 Jonathan 0 - - 0 0 farewell;
24 Kenji 0 - - 0 0 farewell;
31 Mizuki 1 - - 0 0 ;
32 Sakura 1 31 answer 0 1 ;
33 Toshio 1 31 answer 0 0 ;
34 Jonathan 0 33 agree 0 0 repeats [33];
35 Kenji 1 33 object 1 0 ;
36 Mizuki 2 35 add 0 0 ;
37 Sakura 1 36 object 1 1 ;
38 Toshio 1 36 answer 0 0 ;
39 Jonathan 0 38 agree 0 0 repeats [38];
40 Kenji 0 38 object 1 0 repeats [35];
41 Mizuki 2 40 object 1 0 ;
42 Sakura 1 40 add 0 1 ;
43 Toshio 2 42 object 1 0 ;
44 Jonathan 0 43 agree 0 0 repeats [43];
45 Kenji 0 44 agree 0 0 thanks only;
46 Mizuki 1 45 add 0 0 ;
47 Sakura 1 46 add 0 1 ;
48 Toshio 1 45 object 0 0 ;
49 Jonathan 1 48 agree 0 0 ;
50 Kenji 1 48 object 1 1 ;"""
f3="""5 Mizuki 1 - - 0 0 ;
6 Sakura 1 5 answer 0 1 ;
7 Toshio 2 6 object 1 0 ;
8 Jonathan 0 7 agree 0 1 restates [7];
9 Kenji 0 - - 0 1 generic enthusiasm;
10 Mizuki 1 9 add 0 0 ;
11 Sakura 1 10 add 0 0 ;
12 Toshio 1 11 object 1 0 ;
13 Jonathan 0 12 agree 0 0 repeats [12];
14 Kenji 0 12 agree 0 0 promises only;
15 Mizuki 1 - - 0 0 ;
16 Sakura 1 15 add 0 1 ;
17 Toshio 1 15 add 0 0 ;
18 Jonathan 0 17 agree 0 0 repeats [17];
19 Kenji 0 17 agree 0 0 agreement only;
20 Mizuki 0 - - 0 0 closing;
22 Sakura 0 - - 0 0 farewell;
24 Toshio 0 20 agree 0 0 farewell;
26 Jonathan 0 - - 0 0 farewell;
28 Kenji 0 - - 0 0 farewell;
36 Mizuki 1 - - 0 1 ;
37 Sakura 1 36 add 0 0 ;
38 Toshio 1 37 object 1 0 ;
39 Jonathan 0 38 agree 0 0 repeats [38];
40 Kenji 1 36 add 0 0 ;
41 Mizuki 1 40 answer 0 0 ;
42 Sakura 1 41 add 0 0 ;
43 Toshio 1 42 object 1 0 ;
44 Jonathan 0 43 agree 0 0 repeats [43];
45 Kenji 1 44 add 0 0 ;
46 Mizuki 2 45 answer 0 0 ;
47 Sakura 1 46 add 0 1 ;
48 Toshio 1 46 object 1 0 ;
49 Jonathan 0 46 object 1 0 repeats [48];
50 Kenji 2 46 object 1 0 ;
51 Mizuki 1 49 add 0 0 ;
52 Sakura 1 46 agree 0 0 ;
53 Toshio 2 51 object 1 0 ;
54 Jonathan 1 53 add 0 0 ;
55 Kenji 0 - - 0 1 no judgement;
69 Sakura 2 - - 0 0 ;
70 Jonathan 0 69 agree 0 0 repeats [69];
71 Kenji 0 70 agree 0 0 repeats [70];
72 Sakura 2 - - 0 0 ;
73 Jonathan 1 72 add 0 0 ;
74 Kenji 2 73 answer 0 0 ;
75 Sakura 1 74 add 0 0 ;
76 Jonathan 1 75 answer 0 0 ;
77 Kenji 1 76 object 1 0 ;
78 Sakura 1 77 add 0 1 ;
79 Jonathan 1 78 add 0 0 ;
80 Kenji 1 79 answer 0 0 ;"""
out={}
for name,t in [("aiwolf_0001__single-online.md",f1),("aiwolf_0002__multi-private-process.md",f2),("aiwolf_0002__multi-private.md",f3)]:
    L=[]
    for r in t.split(";\n") if False else t.rstrip(";").split(";\n"):
        p=r.split(" ",7); 
        seq,sp,c,rt,ty,rb,pd=p[:7]; note=p[7].strip() if len(p)>7 else ""
        d={"seq":int(seq),"speaker":sp,"content":int(c),"resp":0 if rt=="-" else 1,"resp_to":None if rt=="-" else int(rt),"resp_type":None if rt=="-" else ty,"rebut":int(rb),"padded":int(pd)}
        if note: d["note"]=note
        elif d["content"]==0 or d["rebut"] or d["padded"]: d["note"]="see line"
        L.append(d)
    out[name]=L
json.dump(out,open(B,"w"),ensure_ascii=False)
print({k:len(v) for k,v in out.items()})
