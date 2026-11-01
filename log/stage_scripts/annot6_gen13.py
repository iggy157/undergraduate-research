import json,sys
# seq speaker resp rebut empty ignore misattr reversal note
D={
"game_040.md":"""5 Servas 0 0 0 0 0 0
6 Midori 0 0 0 0 0 0
7 Kenji 0 0 0 0 0 0
8 Benjamin 0 0 0 0 0 0
9 Toshio 0 0 0 0 0 0
25 Servas 0 0 0 0 0 0
26 Midori 0 0 0 0 0 0
27 Kenji 0 0 0 0 0 0
28 Benjamin 0 0 0 0 0 0
29 Toshio 0 0 0 0 0 0
31 Midori 0 0 0 0 0 0
32 Kenji 0 0 0 0 0 0
33 Benjamin 0 0 0 0 0 0
34 Toshio 1 0 0 0 0 0
35 Servas 1 0 0 0 0 0
36 Midori 1 0 0 0 0 0
37 Kenji 1 0 0 0 0 0
38 Benjamin 1 0 0 0 0 0
39 Toshio 1 0 0 0 0 0
40 Servas 0 0 1 0 0 0|ritual closing line
41 Midori 0 0 1 0 0 0|repeats agreement only
42 Kenji 0 0 1 0 0 0|no content
43 Benjamin 0 0 1 0 0 0|no content
44 Toshio 0 0 1 0 0 0|ritual line
50 Servas 0 0 0 0 0 0
51 Midori 1 0 0 0 0 0
52 Kenji 1 0 0 0 0 0
53 Benjamin 1 0 0 0 0 0
54 Toshio 1 0 0 0 0 0
55 Servas 1 0 0 0 0 0
56 Midori 1 0 0 0 0 0
57 Kenji 1 1 0 0 1 0|Benjamin never mentioned flooding and fires
58 Benjamin 1 0 0 0 0 0
59 Toshio 1 0 0 0 0 0
60 Servas 1 0 0 0 0 0
61 Midori 1 0 0 0 0 0
62 Kenji 1 0 0 0 0 0
63 Benjamin 1 0 0 0 0 0
64 Toshio 1 0 1 0 0 0|restates own [59]
65 Servas 0 0 1 0 0 0|vote restates [60]
66 Midori 0 0 1 0 0 0|vote restates [61]
67 Kenji 0 0 1 0 0 0|vote restates [62]
68 Benjamin 0 0 1 0 0 0|vote restates [63]
69 Toshio 0 0 1 0 0 0|vote restates [64]""",
"game_041.md":"""5 Servas 0 0 0 0 0 0
6 Asuka 0 0 0 0 0 0
7 Minako 0 0 0 0 0 0
8 Mio 0 0 0 0 0 0
9 Toshio 0 0 0 0 0 0
29 Servas 0 0 0 0 0 0
30 Asuka 0 0 0 0 0 0
31 Minako 0 0 0 0 0 0
32 Mio 0 0 0 0 0 0
33 Toshio 0 0 0 0 0 0
36 Minako 0 0 0 0 0 0
37 Mio 0 0 0 0 0 0
38 Toshio 0 0 0 0 0 0
39 Servas 1 0 0 0 0 0
40 Asuka 0 0 0 0 0 0
41 Minako 0 0 0 0 0 0
42 Mio 0 0 1 0 0 0|restates [32]/[37]
43 Toshio 1 0 0 0 0 0
44 Servas 1 0 1 0 0 0|platitude
45 Asuka 0 0 1 0 0 0|restates [40]
46 Minako 1 0 1 0 0 0|restates [41]
47 Mio 0 0 1 0 0 0|no content
48 Toshio 0 0 1 0 0 0|ritual line
54 Servas 0 0 0 0 0 1|calls others opaque, contradicting [29] that software is the opaque one
55 Asuka 0 0 0 0 0 0
56 Minako 0 0 0 0 0 0
57 Mio 1 1 0 0 0 0
58 Toshio 1 0 0 0 0 0
59 Servas 0 0 0 0 0 0
60 Asuka 1 0 0 0 0 0
61 Minako 0 0 1 0 0 0|restates [56]
62 Mio 1 0 1 0 0 0|restates [57]
63 Toshio 0 0 1 0 0 0|restates [58]
64 Servas 1 0 0 0 0 0
65 Asuka 1 0 0 0 0 0
66 Minako 0 0 1 0 0 0|restates [61]
67 Mio 0 0 1 0 0 0|restates [62]
68 Toshio 1 0 1 0 0 0|restates [63]
69 Servas 0 0 1 0 0 0|vote restates [64]
70 Asuka 0 0 1 0 0 0|vote restates
71 Minako 0 0 1 0 0 0|vote restates [66]
72 Mio 0 0 1 0 0 0|vote restates [67]
73 Toshio 0 0 1 0 0 0|vote restates [68]""",
"game_042.md":"""5 Toshio 0 0 0 0 0 0
6 Victoria 0 0 0 0 0 0
7 George 0 0 0 0 0 0
8 Mizuki 0 0 0 0 0 0
9 Benjamin 0 0 0 0 0 0
30 Toshio 0 0 0 0 0 0
31 Victoria 0 0 0 0 0 0
32 George 0 0 0 0 0 0
33 Mizuki 0 0 0 0 0 0
34 Benjamin 0 0 0 0 0 0
35 Toshio 1 0 0 0 0 0
36 Victoria 1 0 0 0 0 0
37 George 0 0 0 0 0 0
38 Mizuki 0 0 1 0 0 0|restates [33]
39 Benjamin 0 0 1 0 0 0|restates [34]
40 Toshio 1 0 0 0 0 0
41 Victoria 1 0 0 0 0 0
42 George 0 0 1 0 0 0|restates [37]
43 Mizuki 1 1 0 0 0 0
44 Benjamin 1 0 1 0 0 0|restates [34]/[39]
45 Toshio 1 0 1 0 0 0|summary restating [35]/[40]
46 Victoria 1 0 0 0 0 0
47 George 1 0 1 0 0 0|restates [37]/[42]
48 Mizuki 0 0 1 0 0 0|restates [38]
49 Benjamin 1 0 0 0 0 0
55 Toshio 0 0 0 0 0 0
56 Victoria 0 0 0 0 0 0
57 George 1 0 0 0 0 0
58 Mizuki 1 1 0 0 0 0
59 Benjamin 0 0 0 0 0 0
60 Toshio 1 0 0 0 0 0
61 Victoria 1 1 0 0 0 0
62 George 1 1 0 0 0 0
63 Mizuki 1 1 0 0 0 0
64 Benjamin 1 0 0 0 0 0
65 Toshio 1 0 0 0 0 0
66 Victoria 1 0 0 0 0 0
67 George 1 0 0 0 0 0
68 Mizuki 1 0 0 0 0 0
69 Benjamin 1 0 1 0 0 0|restates [64]
70 Toshio 0 0 1 0 0 0|vote restates [65]
71 Victoria 0 0 1 0 0 0|vote restates [66]
72 George 0 0 1 0 0 0|vote restates [67]
73 Mizuki 0 0 1 0 0 0|vote restates [68]
74 Benjamin 0 0 1 0 0 0|vote restates [69]"""}
K=["resp","rebut","empty","ignore","misattr","reversal"]
out={}
for f,t in D.items():
    L=[]
    for line in t.splitlines():
        a,_,note=line.partition("|")
        p=a.split()
        o={"seq":int(p[0]),"speaker":p[1]}
        for k,v in zip(K,p[2:8]): o[k]=int(v)
        o["note"]=note
        L.append(o)
    out[f]=L
json.dump(out,open(sys.argv[1],"w"),ensure_ascii=False,indent=1)
