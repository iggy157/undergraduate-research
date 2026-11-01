import json
# seq speaker content resp resp_to type rebut padded note
A = """
5|Servas|1|0|||0|1|opening pleasantry
6|Asuka|1|1|5|add|0|0|
7|Minako|1|0|||0|0|
8|Mio|1|0|||0|1|opening excitement
9|Toshio|1|0|||0|0|
10|Servas|0|0|||0|1|general sentiment, no new point
11|Asuka|0|1|10|add|0|0|restates [6] focus
12|Minako|1|1|11|add|0|1|closing look-forward line
13|Mio|0|1|12|agree|0|1|restates [8] with sentiment
14|Toshio|1|1|13|add|0|0|
15|Servas|0|0|||0|1|platitude
16|Asuka|1|1|15|object|1|0|rejects Servas's spirit framing
17|Minako|1|1|16|add|0|0|
18|Mio|0|0|||0|1|restates hiring worry with filler
19|Toshio|1|1|17|add|0|0|
20|Servas|0|0|||0|1|general sentiment
21|Asuka|0|0|||0|0|ritual readiness statement
23|Minako|0|1|21|agree|0|0|agrees to proceed, restates focus
25|Mio|0|1|23|agree|0|1|agreement with enthusiasm filler
27|Toshio|0|0|||0|1|restates [14]; closing filler
39|Servas|2|0|||0|0|
40|Asuka|2|0|||0|0|
41|Minako|2|0|||0|0|
42|Mio|2|0|||0|0|
43|Toshio|2|0|||0|0|
44|Servas|1|0|||0|1|sentiment line 'true peace comes from clarity'
45|Asuka|1|1|44|object|1|0|counters Servas's opacity concern
46|Minako|1|1|45|object|1|0|argues stability depends on liquidity
47|Mio|1|1|46|add|0|0|
48|Toshio|1|1|47|object|1|0|dismisses exhaustion as poor planning
49|Servas|1|0|||0|1|closing maxim restates point
50|Asuka|1|1|49|object|1|0|counters slow-audit preference
51|Minako|1|1|50|add|0|0|
52|Mio|1|1|51|add|0|0|
53|Toshio|1|1|51|add|0|0|
54|Servas|0|0|||0|1|repeats [49]
55|Asuka|1|0|||0|0|
56|Minako|1|1|55|add|0|0|
57|Mio|0|1|56|agree|0|1|restates [47]; repeated burnout line
58|Toshio|1|1|56|add|0|0|
64|Servas|2|0|||0|0|
65|Asuka|2|1|64|object|1|0|disagrees with Ledger Bridge
66|Minako|2|1|65|object|1|0|cautions against Clinic Scheduler
67|Mio|2|1|66|add|0|0|
68|Toshio|2|1|66|add|0|0|
69|Servas|0|1|68|agree|0|0|restates [64] choice
70|Asuka|1|1|68|object|1|0|disputes efficiency priority
71|Minako|1|1|70|object|1|0|retention meaningless without funding
72|Mio|1|1|70|object|1|0|argues against Clinic staffing
73|Toshio|1|1|70|object|1|0|argues deployment first
74|Servas|0|0|||0|1|restates [64]/[69] with sentiment
75|Asuka|1|1|73|object|1|0|start vs finish rebuttal
76|Minako|0|1|75|object|1|0|restates [71]; opposes Asuka
77|Mio|0|1|75|object|1|0|restates [72]; opposes Asuka
78|Toshio|1|1|75|object|1|0|argues churn manageable
79|Servas|1|0|||0|1|ritual opening and 'light heart'
80|Asuka|1|0|||0|0|
81|Minako|1|0|||0|0|
82|Mio|1|0|||0|0|
83|Toshio|1|0|||0|0|
"""
B = """
5|Servas|1|0|||0|1|opening pleasantry
6|Asuka|1|1|5|add|0|0|
7|Minako|1|0|||0|0|
8|Mio|1|0|||0|1|opening excitement
9|Toshio|1|0|||0|0|
10|Servas|0|1|8|agree|0|1|compliment and general sentiment
11|Asuka|1|1|10|object|1|0|rejects sentiment, refocus on data
12|Minako|1|1|11|add|0|0|
13|Mio|1|1|12|add|0|1|closing excitement line
14|Toshio|1|1|13|add|0|0|
15|Servas|0|0|||0|1|platitude
16|Asuka|1|1|15|object|1|0|integrity is not a feeling
17|Minako|1|1|16|add|0|0|
18|Mio|1|1|17|add|0|1|self-description filler
19|Toshio|1|1|18|object|1|0|optimism cannot bypass delays
20|Servas|0|0|||0|1|general sentiment
21|Asuka|0|0|||0|0|restates data-focus
23|Minako|0|1|21|agree|0|0|agrees to proceed, restates focus
25|Mio|0|0|||0|0|restates own task
27|Toshio|0|0|||0|1|restates task; look-forward filler
39|Servas|2|0|||0|0|
40|Asuka|2|0|||0|0|
41|Minako|2|0|||0|0|
42|Mio|2|1|41|agree|0|0|
43|Toshio|2|0|||0|0|
44|Servas|1|1|43|add|0|0|
45|Asuka|1|1|44|add|0|0|
46|Minako|1|1|45|add|0|0|
47|Mio|1|1|46|add|0|0|
48|Toshio|1|1|47|add|0|0|
49|Servas|1|0|||0|1|opening 'delicate balance' and 'gift' sentiment
50|Asuka|1|1|49|object|1|0|simplicity is not a gift
51|Minako|0|1|50|object|1|0|restates [46]; opposes simplicity focus
52|Mio|0|1|51|add|0|0|restates [47]
53|Toshio|1|1|52|object|1|0|capacity is irrelevant
54|Servas|0|0|||0|1|general sentiment
55|Asuka|1|1|54|object|1|0|wisdom comes from data, not easing burdens
56|Minako|1|1|55|add|0|0|
57|Mio|0|1|56|add|0|0|restates [47]/[52]
58|Toshio|1|0|||0|0|
64|Servas|2|0|||0|0|
65|Asuka|2|1|64|add|0|0|
66|Minako|2|1|65|add|0|0|
67|Mio|2|1|66|add|0|0|
68|Toshio|2|0|||0|0|
69|Servas|0|1|68|agree|0|1|celebrates alignment
70|Asuka|0|1|69|add|0|0|restates [65]
71|Minako|0|1|70|agree|0|0|restates [66]
72|Mio|0|1|71|agree|0|1|enthusiasm filler
73|Toshio|0|0|||0|0|readiness, no new point
74|Servas|1|0|||0|1|unity sentiment
75|Asuka|1|0|||0|0|
76|Minako|1|1|75|agree|0|0|
77|Mio|1|0|||0|1|'so happy we all agree'
78|Toshio|1|0|||0|0|
79|Servas|0|0|||0|1|repeats vote with blessing sentiment
80|Asuka|0|0|||0|0|repeats vote
81|Minako|0|0|||0|0|repeats vote
82|Mio|0|0|||0|1|repeats vote with cheer
83|Toshio|0|0|||0|0|repeats vote
"""
C = """
5|Servas|1|0|||0|1|opening pleasantry
6|Asuka|1|1|5|add|0|0|
7|Minako|1|0|||0|0|
8|Mio|1|0|||0|1|opening excitement
9|Toshio|1|0|||0|0|
10|Servas|1|0|||0|0|
11|Asuka|1|1|10|answer|0|0|
12|Minako|0|1|11|agree|0|1|echoes [11]; 'I am satisfied' redundant
13|Mio|0|1|12|agree|0|1|agreement with enthusiasm filler
14|Toshio|0|1|13|agree|0|0|agreement only
16|Servas|0|1|14|agree|0|1|look-forward filler
18|Asuka|0|1|16|agree|0|0|agrees to proceed
20|Minako|0|1|18|agree|0|1|agreement plus look-forward line
22|Mio|0|1|20|agree|0|1|farewell
34|Servas|2|0|||0|0|
35|Asuka|2|0|||0|0|
36|Minako|2|0|||0|0|
37|Mio|2|0|||0|0|
38|Toshio|2|0|||0|0|
39|Servas|1|1|36|add|0|0|
40|Asuka|1|1|36|add|0|0|
41|Minako|1|1|40|add|0|0|
42|Mio|1|0|||0|0|
43|Toshio|2|1|42|answer|0|0|
44|Servas|1|1|43|add|0|0|
45|Asuka|1|1|43|add|0|0|
46|Minako|0|1|45|agree|0|0|restates [45] and [36]
47|Mio|1|1|46|add|0|1|closing 'trickier than I thought'
48|Toshio|1|1|47|answer|0|0|
49|Servas|1|1|48|add|0|0|
50|Asuka|1|1|49|add|0|0|
51|Minako|1|1|50|add|0|0|
52|Mio|1|1|51|add|0|0|
53|Toshio|1|1|52|add|0|0|
59|Servas|2|0|||0|0|
60|Asuka|2|1|59|add|0|0|
61|Minako|2|0|||0|0|
62|Mio|1|0|||0|0|
63|Toshio|1|0|||0|0|
64|Servas|1|0|||0|1|opening remark on alignment
65|Asuka|1|0|||0|0|
66|Minako|1|1|65|agree|0|0|
67|Mio|0|0|||0|1|repeats vote, says so twice
68|Toshio|0|0|||0|1|repeats [63] vote twice
69|Servas|0|0|||0|0|restates choice
71|Asuka|0|1|69|agree|0|0|agreement only
73|Minako|0|1|71|agree|0|1|repeats vote and agreement
75|Mio|0|0|||0|1|repeats vote with cheer
77|Toshio|0|1|75|agree|0|0|repeats vote
"""
def parse(s):
    out=[]
    for line in s.strip().splitlines():
        seq,sp,c,r,rt,ty,rb,pd,note=line.split('|')
        o={"seq":int(seq),"speaker":sp,"content":int(c),"resp":int(r),
           "resp_to":int(rt) if rt else None,"resp_type":ty or None,
           "rebut":int(rb),"padded":int(pd)}
        if note: o["note"]=note
        assert (o["resp"]==1)==(o["resp_to"] is not None)
        if o["rebut"]: assert o["resp"]
        out.append(o)
    return out
res={"candidate_selection_0002__multi-private-process.md":parse(A),
     "candidate_selection_0002__multi-private.md":parse(B),
     "candidate_selection_0002__multi-public.md":parse(C)}
json.dump(res,open('/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot8v2/out/opus_09.json','w'),ensure_ascii=False,indent=1)
print({k:len(v) for k,v in res.items()})
