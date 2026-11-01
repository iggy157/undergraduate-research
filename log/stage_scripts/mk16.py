import json
S={'R':'Rin','M':'Midori','S':'Shunichi','Y':'May','A':'Asuka'}
# seq speaker content resp_to type rebut padded note
P="""5 R 2 - - 0 0 -
6 M 2 5 add 0 0 -
7 S 1 - - 0 0 -
8 Y 2 7 add 0 0 -
9 A 2 - - 0 0 -
10 R 1 8 add 0 0 -
11 M 0 10 add 0 1 repeats own ledger plan from [6]
12 S 1 11 object 1 0 -
13 Y 0 12 add 0 1 repeats own plan from [8]
14 A 1 13 add 0 0 -
15 R 1 - - 0 0 -
16 M 0 15 agree 0 1 repeats own ledger plan from [6]
17 S 1 15 object 1 0 -
18 Y 0 15 object 1 0 repeats labor focus from [8]
19 A 0 18 object 1 0 repeats own plan from [9]
20 R 0 - - 0 1 farewell and excitement
21 M 0 - - 0 1 farewell pleasantry
22 S 0 - - 0 1 closing quip
23 Y 0 - - 0 1 farewell quip
24 A 0 - - 0 1 farewell, repeats [9]
35 R 2 - - 0 0 -
36 M 2 35 add 0 0 -
37 S 2 36 object 0 0 -
38 Y 2 37 object 1 0 -
39 A 1 36 object 1 0 -
40 R 1 39 add 0 0 -
41 M 0 40 agree 0 1 repeats cost worry from [36]
42 S 1 39 add 0 0 -
43 Y 1 42 agree 0 0 -
44 A 1 42 object 1 0 -
45 R 1 43 add 0 0 -
46 M 0 45 add 0 0 repeats cost worry
47 S 1 44 object 1 0 -
48 Y 1 47 object 1 0 -
49 A 1 48 add 0 0 -
50 R 0 49 agree 0 1 agrees with [49] and sentiment
51 M 0 50 agree 0 1 repeats low-cost view from [41]
52 S 1 51 object 1 0 -
53 Y 0 52 object 1 0 repeats rotation point from [43]/[48]
54 A 0 52 object 1 0 repeats [49]
60 R 1 - - 0 0 -
61 M 1 60 agree 0 0 -
62 S 1 61 object 1 0 -
63 Y 1 62 object 1 0 -
64 A 1 62 add 0 0 -
65 R 1 64 agree 0 0 -
66 M 0 65 agree 0 1 repeats [61]
67 S 1 66 object 1 0 -
68 Y 0 67 object 1 0 repeats [63]
69 A 0 67 object 1 0 repeats [64]
70 R 1 67 object 1 0 -
71 M 0 70 agree 0 1 repeats [61]
72 S 1 71 agree 0 0 -
73 Y 0 72 agree 0 1 triumphant agreement
74 A 0 73 agree 0 1 repeats [64]
75 R 0 74 agree 0 1 repeats vote from [65]
76 M 0 75 agree 0 1 repeats [66]
77 S 1 76 add 0 0 -
78 Y 0 77 agree 0 1 repeats [63]
79 A 0 78 agree 0 1 repeats [64]"""
Q="""5 R 2 - - 0 0 -
6 M 1 5 add 0 0 -
7 S 1 - - 0 0 -
8 Y 1 - - 0 0 -
9 A 1 - - 0 0 -
10 R 1 8 add 0 0 -
11 M 1 10 answer 0 0 -
12 S 1 10 answer 1 0 -
13 Y 2 12 object 1 0 -
14 A 1 13 agree 0 0 -
15 R 1 - - 0 0 -
16 M 0 15 answer 0 1 repeats cost concern from [6]
17 S 1 16 object 1 0 -
18 Y 1 17 agree 0 0 -
19 A 1 18 object 1 0 -
20 R 0 - - 0 1 restates scouting plan
21 M 0 - - 0 1 closing pleasantry
22 S 0 - - 0 1 closing quip
23 Y 0 - - 0 1 farewell
24 A 0 - - 0 1 farewell, repeats [9]
35 R 2 - - 0 0 -
36 M 2 35 add 0 0 -
37 S 1 19 add 0 0 -
38 Y 2 37 add 0 0 -
39 A 1 37 add 0 0 -
40 R 1 38 add 0 0 -
41 M 0 40 add 0 1 repeats cost worry from [36]
42 S 1 40 object 1 0 -
43 Y 1 40 object 1 0 -
44 A 1 40 add 0 0 -
45 R 1 44 add 0 0 -
46 M 0 45 answer 0 1 repeats [41]
47 S 1 46 object 1 0 -
48 Y 1 47 add 0 0 -
49 A 1 48 add 0 0 -
50 R 0 49 add 0 1 repeats sharing/moving idea from [45]
51 M 0 50 agree 0 1 repeats [41]/[46]
52 S 1 50 object 1 0 -
53 Y 0 49 agree 0 1 no new point, just ready to vote
54 A 1 53 object 1 0 -
60 R 1 - - 0 0 -
61 M 1 60 answer 0 0 -
62 S 1 61 object 1 0 -
63 Y 1 62 agree 0 0 -
64 A 1 62 agree 0 0 -
65 R 1 64 agree 0 0 -
66 M 0 65 agree 0 1 repeats [61]
67 S 0 66 agree 0 1 repeats [62]
68 Y 0 67 agree 0 1 repeats vote [63]
69 A 0 68 agree 0 1 repeats [64]
70 R 0 69 agree 0 1 repeats vote
71 M 0 70 agree 0 1 repeats vote
72 S 0 71 agree 0 1 repeats vote
73 Y 0 72 agree 0 1 repeats vote
74 A 0 73 agree 0 1 repeats [64]
75 R 0 74 agree 0 1 repeats vote
76 M 0 75 agree 0 1 repeats vote
77 S 1 76 add 0 0 -
78 Y 0 77 agree 0 1 repeats [18]
79 A 0 78 agree 0 1 repeats [64]"""
T="""5 R 2 - - 0 0 -
6 M 1 - - 0 0 -
7 S 1 - - 0 0 -
8 Y 1 - - 0 0 -
9 A 1 - - 0 0 -
11 M 1 8 add 0 0 -
12 S 1 11 answer 0 0 -
13 Y 1 12 agree 0 0 -
14 A 0 12 agree 0 0 summarizes plan already agreed
15 R 0 14 agree 0 1 restates readiness
16 M 0 14 agree 0 1 pleasantry
17 S 1 15 agree 0 0 -
18 Y 0 - - 0 1 closing remark
19 A 0 - - 0 1 repeats [14]
20 R 0 - - 0 1 farewell
21 M 0 - - 0 1 farewell
22 S 0 - - 0 1 closing remark
23 Y 0 - - 0 1 farewell
24 A 0 - - 0 1 farewell
35 R 2 - - 0 0 -
36 M 2 35 add 0 0 -
37 S 2 - - 0 0 -
38 Y 2 - - 0 0 -
39 A 2 - - 0 0 -
40 R 1 37 add 0 0 -
41 M 1 39 add 0 0 -
42 S 0 41 agree 0 0 repeats [37]
43 Y 0 42 agree 0 0 repeats police point from [38]
44 A 1 43 add 0 0 -
45 R 1 44 add 0 0 -
46 M 1 45 answer 0 0 -
47 S 0 46 agree 0 0 repeats [37]/[42]
48 Y 0 47 agree 0 0 repeats [38]/[39]
49 A 1 48 add 0 0 -
50 R 1 49 add 0 0 -
51 M 0 50 agree 0 1 agrees, repeats [46]
52 S 0 51 agree 0 0 repeats [42]
53 Y 0 52 agree 0 0 summarizes earlier points
54 A 1 53 add 0 0 -
60 R 1 - - 0 0 -
61 M 1 60 agree 0 0 -
62 S 1 61 agree 0 0 -
63 Y 1 62 agree 0 0 -
64 A 1 63 agree 0 0 -
66 M 1 64 agree 0 0 -
68 S 1 66 add 0 0 -
70 Y 0 68 agree 0 0 repeats [68]
71 A 1 70 object 1 0 -
72 R 0 71 agree 0 1 pleasantry
74 A 0 - - 0 1 closing remark"""
def conv(P):
    o=[]
    for l in P.split("\n"):
        a=l.split(" ",7)
        sq,sp,c,rt,ty,rb,pd,nt=a
        o.append({"seq":int(sq),"speaker":S[sp],"content":int(c),"resp":0 if rt=='-' else 1,
          "resp_to":None if rt=='-' else int(rt),"resp_type":None if ty=='-' else ty,
          "rebut":int(rb),"padded":int(pd),**({"note":nt} if nt!='-' else {})})
    return o
d={"shared_living_0002__multi-private-process.md":conv(P),"shared_living_0002__multi-private.md":conv(Q),"shared_living_0002__multi-public.md":conv(T)}
json.dump(d,open("annot8v2/out/sonnet_16.json","w"),ensure_ascii=False)
print({k:len(v) for k,v in d.items()})
