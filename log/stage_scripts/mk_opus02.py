import json,sys
# seq speaker resp rebut empty ignore misattr reversal note
g7="""5 Servas 0 0 1 0 0 0
6 Midori 0 0 1 0 0 0
7 Kenji 0 0 0 0 0 0
8 Benjamin 1 0 0 0 0 0
9 Toshio 1 0 0 0 0 0
10 Servas 0 0 0 0 0 0
11 Midori 1 0 0 0 0 0
12 Kenji 1 0 0 0 0 0
13 Benjamin 1 0 0 0 0 0
14 Toshio 1 0 0 0 0 0
15 Servas 0 0 0 0 0 0
16 Midori 0 0 0 0 0 0
17 Kenji 0 0 0 0 0 0
18 Benjamin 0 0 0 0 0 0
19 Toshio 0 0 0 0 0 0
20 Servas 0 0 1 0 0 0
21 Midori 0 0 1 0 0 0
22 Kenji 0 0 1 0 0 0
23 Benjamin 0 0 1 0 0 0
24 Toshio 0 0 1 0 0 0
35 Servas 0 0 0 0 0 0
36 Midori 1 0 0 0 0 0
37 Kenji 1 0 0 0 0 0
38 Benjamin 1 0 0 0 0 0
39 Toshio 1 0 0 0 0 0
40 Servas 1 0 0 0 0 0
41 Midori 1 0 0 0 0 0
42 Kenji 1 0 0 0 0 0
43 Benjamin 1 0 1 0 0 0
44 Toshio 1 0 0 0 0 0
45 Servas 1 0 0 0 0 0
46 Midori 1 0 0 0 0 0
47 Kenji 1 0 1 0 0 0
48 Benjamin 1 0 1 0 0 0
49 Toshio 1 1 0 0 0 0 disputes 'rare specimen' in [48]
50 Servas 0 0 1 0 0 0
51 Midori 1 0 1 0 0 0
52 Kenji 1 0 1 0 0 0
53 Benjamin 1 0 1 0 0 0
54 Toshio 0 0 1 0 0 0
60 Servas 0 0 0 0 0 0
61 Midori 1 0 0 0 0 0
62 Kenji 1 0 0 0 0 0
63 Benjamin 1 0 0 0 0 0
64 Toshio 1 0 0 0 0 0
65 Servas 1 0 1 0 0 0
66 Midori 1 0 1 0 0 0
67 Kenji 1 0 1 0 0 0
68 Benjamin 1 0 1 0 0 0
69 Toshio 1 0 1 0 0 0
70 Servas 0 0 1 0 0 0
71 Midori 0 0 1 0 0 0
72 Kenji 0 0 1 0 0 0
73 Benjamin 0 0 1 0 0 0
74 Toshio 0 0 1 0 0 0
75 Servas 0 0 1 0 0 0
76 Midori 0 0 1 0 0 0
77 Kenji 0 0 1 0 0 0
78 Benjamin 0 0 1 0 0 0
79 Toshio 0 0 1 0 0 0"""
g8="""5 Servas 0 0 0 0 0 0
6 Asuka 1 0 0 0 0 0
7 Minako 0 0 0 0 0 0
8 Mio 0 0 0 0 0 0
9 Toshio 0 0 0 0 0 0
10 Servas 1 0 1 0 0 0
11 Asuka 1 1 0 0 0 0 pushes back on Servas's sentiment in [10]
12 Minako 1 1 0 0 0 0 qualifies Asuka's [11] with 'however'
13 Mio 1 1 0 0 0 0 counters Minako's [12]
14 Toshio 1 1 0 0 0 0 counters [12]-[13]
15 Servas 1 0 0 0 0 0
16 Asuka 1 1 0 1 0 0 rebuts [15]; ignores Minako's objection [12]
17 Minako 1 1 0 1 0 0 qualifies [16]; ignores Mio's objection [13]
18 Mio 1 0 0 0 0 0
19 Toshio 1 1 0 0 0 0 rebuts Mio's optimism [18]
20 Servas 0 0 1 1 0 0 ignores Asuka's objection [16]
21 Asuka 0 0 1 1 0 0 ignores Minako's objection [17]
23 Minako 0 0 1 0 0 0
25 Mio 0 0 1 1 0 0 ignores Toshio's objection [19]
27 Toshio 0 0 1 0 0 0
39 Servas 0 0 0 0 0 0
40 Asuka 0 0 0 0 0 0
41 Minako 0 0 0 0 0 0
42 Mio 1 0 0 0 0 0
43 Toshio 0 0 0 0 0 0
44 Servas 1 0 0 0 0 0
45 Asuka 1 0 0 0 0 0
46 Minako 1 1 0 0 0 0 objects that lean software still carries liquidity risk
47 Mio 1 0 0 0 0 0
48 Toshio 1 0 0 0 0 0
49 Servas 1 0 0 0 0 0
50 Asuka 1 1 0 1 0 0 rebuts [49]; ignores Minako's objection [46]
51 Minako 1 1 0 1 0 0 rebuts [50]; ignores Mio's objection [47]
52 Mio 1 0 1 0 0 0
53 Toshio 1 1 0 0 0 0 rebuts Mio's capacity point [52]
54 Servas 1 0 1 1 0 0 ignores Asuka's objection [50]
55 Asuka 1 1 0 1 0 0 rebuts [54]; ignores Minako's objection [51]
56 Minako 1 1 1 1 0 0 repeats solvency point; ignores Mio's objection [52]
57 Mio 1 0 1 1 0 0 ignores Toshio's objection [53]
58 Toshio 1 0 0 0 0 0
64 Servas 0 0 0 0 0 0
65 Asuka 1 0 0 0 0 0
66 Minako 1 0 0 0 0 0
67 Mio 1 0 0 0 0 0
68 Toshio 1 0 0 0 0 0
69 Servas 1 0 1 0 0 0
70 Asuka 1 0 1 0 0 0
71 Minako 1 0 1 0 0 0
72 Mio 1 0 1 0 0 0
73 Toshio 1 0 1 0 0 0
74 Servas 0 0 1 0 0 0
75 Asuka 0 0 1 0 0 0
76 Minako 0 0 1 0 0 0
77 Mio 0 0 1 0 0 0
78 Toshio 0 0 1 0 0 0
79 Servas 0 0 1 0 0 0
80 Asuka 0 0 1 0 0 0
81 Minako 0 0 1 0 0 0
82 Mio 0 0 1 0 0 0
83 Toshio 0 0 1 0 0 0"""
g9="""5 Toshio 0 0 0 0 0 0
6 Victoria 1 0 0 0 0 0
7 George 0 0 0 0 0 0
8 Mizuki 0 0 0 0 0 0
9 Benjamin 1 0 0 0 0 0
10 Toshio 1 0 1 0 0 0
11 Victoria 1 0 1 0 0 0
12 George 1 0 1 0 0 0
13 Mizuki 1 0 1 0 0 0
14 Benjamin 1 0 1 0 0 0
15 Toshio 0 0 1 0 0 0
16 Victoria 1 0 1 0 0 0
17 George 1 0 1 0 0 0
18 Mizuki 1 0 1 0 0 0
19 Benjamin 1 0 1 0 0 0
35 Toshio 0 0 0 0 0 0
36 Victoria 0 0 0 0 0 0
37 George 0 0 0 0 0 0
38 Mizuki 0 0 0 0 0 0
39 Benjamin 1 0 0 0 0 0
40 Toshio 1 0 0 0 0 0
41 Victoria 1 0 0 0 0 0
42 George 1 0 0 0 0 0
43 Mizuki 1 0 0 0 0 0
44 Benjamin 1 0 0 0 0 0
45 Toshio 1 1 0 0 0 0 'not an excuse for stagnation' opposes [44]
46 Victoria 1 0 1 0 0 0
47 George 0 0 1 1 0 0 ignores Mizuki's counterpoint [43]
48 Mizuki 1 1 1 0 0 0 repeats [43] against George's [47]
49 Benjamin 1 0 1 0 0 0
50 Toshio 1 0 1 0 0 0
51 Victoria 1 0 0 0 0 0
52 George 1 0 0 0 0 0
53 Mizuki 1 0 0 0 0 0
54 Benjamin 1 0 1 0 0 0
60 Toshio 0 0 0 0 0 0
61 Victoria 1 1 0 0 0 0 raises timetable objection to Plan A from [60]
62 George 1 0 0 0 0 0
63 Mizuki 1 0 0 0 0 0
64 Benjamin 1 0 0 0 0 0
65 Toshio 1 0 0 0 0 0
66 Victoria 1 0 0 0 0 0
67 George 1 0 1 0 0 0
68 Mizuki 1 0 1 0 0 0
69 Benjamin 1 0 1 0 0 0
70 Toshio 0 0 1 0 0 0
71 Victoria 0 0 1 0 0 0
72 George 0 0 1 0 0 0
73 Mizuki 0 0 1 0 0 0
74 Benjamin 0 0 1 0 0 0
75 Toshio 0 0 1 0 0 0
77 Victoria 0 0 1 0 0 0
79 George 0 0 1 0 0 0
81 Mizuki 0 0 1 0 0 0
83 Benjamin 0 0 1 0 0 0"""
keys=["resp","rebut","empty","ignore","misattr","reversal"]
out={}
for name,g in [("game_007.md",g7),("game_008.md",g8),("game_009.md",g9)]:
    L=[]
    for line in g.split("\n"):
        p=line.split(" ",8)
        d={"seq":int(p[0]),"speaker":p[1]}
        for k,v in zip(keys,p[2:8]): d[k]=int(v)
        d["note"]=p[8] if len(p)>8 else ""
        L.append(d)
    out[name]=L
json.dump(out,open(sys.argv[1],"w"),ensure_ascii=False,indent=1)
