import json,re
B="/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot8v2/"
# seq: (content, to, type, rebut, padded, note)
A={}
A["candidate_selection_0002__multi-private-process.md"]="""
5 1 - - 0 0 
6 1 5 add 0 0
7 1 - - 0 0
8 1 - - 0 1 greeting and enthusiasm filler
9 1 - - 0 0
10 0 9 add 0 1 pleasantry, no judgement
11 1 10 object 0 0
12 1 11 add 0 0
13 0 12 agree 0 1 agreement plus sentiment
14 1 12 add 0 0
15 0 14 add 0 1 sentiment only
16 1 15 object 1 0 contradicts Servas on spirit vs numbers
17 1 16 add 0 0
18 0 17 add 0 1 restates workload worry
19 1 17 add 0 0
20 0 - - 0 1 closing pleasantry
21 0 - - 0 1 restates data focus
23 0 21 agree 0 1 repeats agreement
25 0 23 agree 0 1 ritual
27 0 - - 0 0 repeats [14]
39 1 - - 0 0
40 2 - - 0 0
41 2 - - 0 0
42 2 - - 0 0
43 2 - - 0 0
44 0 43 add 0 1 restates [39] opacity worry
45 1 44 object 0 0
46 1 45 add 0 0
47 1 46 add 0 0
48 1 47 object 1 0 rejects exhaustion concern
49 0 48 add 0 1 restates [44] preference
50 1 49 object 1 0 counters audit preference with churn
51 1 50 object 1 0 counters churn point with liquidity
52 0 51 agree 0 1 echoes [51] and [47]
53 1 51 object 1 0 says software also stalls
54 0 53 add 0 1 restates [49]
55 1 54 object 0 0
56 1 55 add 0 0
57 0 56 agree 0 1 repeats [47]
58 1 56 add 0 0
64 2 - - 0 0
65 2 64 object 1 0
66 2 65 object 1 0 favors Ledger over Clinic
67 1 66 add 0 0
68 2 66 add 0 0
69 1 68 add 0 0
70 1 68 object 1 0
71 1 70 object 1 0
72 0 70 object 1 0 repeats [67]
73 1 70 object 1 0
74 0 73 agree 0 1 repeats [69] preference
75 1 73 object 1 0
76 0 75 object 1 0 repeats [71]
77 0 75 object 1 0 repeats [67]
78 1 75 object 1 0
79 0 78 agree 0 1 vote repeats stated preference
80 0 78 object 0 0 repeats [65] and [70]
81 0 - - 0 0 repeats [71]
82 0 - - 0 0 repeats [72]
83 0 80 object 0 0 repeats [68]
"""
A["candidate_selection_0002__multi-private.md"]="""
5 1 - - 0 0
6 1 5 add 0 0
7 1 - - 0 0
8 1 - - 0 1 excitement filler
9 1 - - 0 0
10 0 8 add 0 1 pleasantry
11 1 10 object 0 0
12 1 11 add 0 0
13 1 12 add 0 0
14 1 13 add 0 0
15 0 14 add 0 1 sentiment only
16 1 15 object 1 0 rejects integrity as feeling
17 1 16 add 0 0
18 0 17 add 0 1 cheerleading
19 1 18 object 1 0 optimism cannot bypass delays
20 0 - - 0 1 closing pleasantry
21 0 - - 0 1 restates data focus
23 0 21 agree 0 1 ritual
25 0 - - 0 1 ritual
27 0 - - 0 0 repeats [9]
39 2 - - 0 0
40 2 - - 0 0
41 2 - - 0 0
42 2 41 add 0 0
43 2 - - 0 0
44 1 43 add 0 0
45 1 44 add 0 0
46 1 45 add 0 0
47 1 46 add 0 0
48 1 47 add 0 0
49 0 48 add 0 1 restates desire for simplicity
50 1 49 object 1 0
51 1 50 object 1 0
52 0 51 add 0 1 repeats [47]
53 1 52 object 1 0 capacity irrelevant
54 0 53 add 0 1 sentiment only
55 1 54 object 1 0
56 1 55 add 0 0
57 0 56 agree 0 1 repeats [47]
58 1 57 add 0 0
64 2 - - 0 0
65 1 64 agree 0 0
66 1 65 agree 0 0
67 1 66 agree 0 0
68 1 67 add 0 0
69 0 68 agree 0 1 sentiment of alignment
70 0 69 add 0 1 repeats [65]
71 0 70 agree 0 1 repeats [66]
72 0 71 agree 0 1 cheering
73 0 71 agree 0 1 repeats consensus
74 0 73 agree 0 1 sentiment
75 0 - - 0 0 repeats [65]
76 0 - - 0 0 repeats [66]
77 0 - - 0 1 cheering
78 0 - - 0 0 repeats [68]
79 0 - - 0 1 blessing
80 0 - - 0 0 repeats [75]
81 0 - - 0 0 repeats [76]
82 0 - - 0 1 cheering
83 0 - - 0 0 repeats [78]
"""
A["candidate_selection_0002__multi-public.md"]="""
5 1 - - 0 0
6 1 5 add 0 0
7 1 - - 0 0
8 1 - - 0 1 excitement filler
9 1 - - 0 0
10 1 9 add 0 0
11 1 10 answer 0 0
12 0 11 agree 0 0 repeats agreement
13 0 10 answer 0 1 cheering
14 0 10 answer 0 0 repeats agreement
16 0 14 agree 0 1 closing pleasantry
18 0 16 agree 0 0 ritual
20 0 18 agree 0 1 ritual
22 0 20 agree 0 1 farewell
34 2 - - 0 0
35 2 - - 0 0
36 2 - - 0 0
37 2 - - 0 0
38 2 - - 0 0
39 1 36 add 0 0
40 1 36 add 0 0
41 1 40 agree 0 0
42 1 41 add 0 0
43 1 42 answer 0 0
44 1 43 add 0 0
45 1 43 add 0 0
46 1 45 add 0 0
47 0 46 add 0 1 restates tradeoffs already discussed
48 1 47 answer 0 0
49 1 48 add 0 0
50 1 49 add 0 0
51 0 50 agree 0 0 repeats [50] reasoning
52 0 50 agree 0 1 repeats agreement
53 1 52 add 0 0
59 2 - - 0 0
60 1 59 agree 0 0
61 1 59 agree 0 0
62 1 61 agree 0 0
63 1 62 agree 0 0
64 0 63 agree 0 1 repeats [59]
65 0 64 agree 0 0 repeats [60]
66 0 65 agree 0 0 repeats [61]
67 0 66 agree 0 1 repeats own vote
68 0 67 agree 0 1 repeats own vote
69 0 68 agree 0 1 restates consensus
71 0 69 agree 0 1 repeats agreement
73 0 71 agree 0 1 repeats [61]
75 0 73 agree 0 1 cheering
77 0 75 agree 0 1 repeats own vote
"""
out={}
for f,t in A.items():
    txt=open(B+"games/"+f).read()
    sp={int(m.group(1)):m.group(2) for m in re.finditer(r"^- \[(\d+)\] \*\*(\w+)\*\*",txt,re.M)}
    L=[]
    for ln in t.strip().split("\n"):
        p=ln.split(" ",6); s=int(p[0]); c=int(p[1]); to=None if p[2]=="-" else int(p[2])
        ty=None if p[3]=="-" else p[3]; note=p[6] if len(p)>6 else ""
        d={"seq":s,"speaker":sp[s],"content":c,"resp":1 if to else 0,"resp_to":to,"resp_type":ty,"rebut":int(p[4]),"padded":int(p[5])}
        if note: d["note"]=note
        elif c==0 or d["rebut"] or d["padded"]: d["note"]="see context"
        L.append(d)
    assert sorted(sp)==[d["seq"] for d in L],(f,set(sp)^{d["seq"] for d in L})
    out[f]=L
json.dump(out,open(B+"out/sonnet_09.json","w"),ensure_ascii=False)
