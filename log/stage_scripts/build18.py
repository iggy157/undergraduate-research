import json,sys
N=None
A=dict(a="answer",d="add",o="object",g="agree")
def mk(rows):
    out=[]
    for r in rows:
        s,sp,c,rt,ty,rb,pd,*n=r
        out.append({"seq":s,"speaker":sp,"content":c,"resp":0 if rt is None else 1,"resp_to":rt,
          "resp_type":None if rt is None else A[ty],"rebut":rb,"padded":pd,"note":n[0] if n else ""})
    return out
f1=[
(5,"Rin",2,N,N,0,0),(6,"Midori",2,N,N,0,0),(7,"Shunichi",2,N,N,0,0),(8,"May",2,N,N,0,0),(9,"Asuka",2,N,N,0,0),
(10,"Rin",1,7,"d",0,0),(11,"Midori",1,10,"d",0,0),(12,"Shunichi",1,10,"a",0,0),(13,"May",2,12,"d",0,0),
(14,"Asuka",0,13,"a",0,0,"says only she has no information yet"),
(15,"Rin",2,N,N,0,0),(16,"Midori",2,15,"a",0,0),(17,"Shunichi",1,16,"d",1,0,"dismisses Rin's 'trash castles' from [15]"),
(18,"May",0,17,"g",0,0,"repeats her concern from [8]"),(19,"Asuka",1,18,"d",0,0),
(20,"Rin",0,N,N,0,0,"farewell and pleasantry"),(21,"Midori",0,N,N,0,1,"restates task with attached sentiment"),
(22,"Shunichi",0,N,N,0,1,"restates task with attached sentiment"),(23,"May",0,N,N,0,1,"restates task; closing filler"),
(24,"Asuka",0,N,N,0,1,"restates task; closing pleasantry"),
(35,"Rin",2,N,N,0,0),(36,"Midori",2,N,N,0,0),(37,"Shunichi",2,N,N,0,0),(38,"May",2,N,N,0,0),(39,"Asuka",2,N,N,0,0),
(40,"Rin",1,N,N,0,0),(41,"Midori",1,40,"d",0,0),(42,"Shunichi",2,40,"o",1,0,"argues Rin's short mornings lead to fighting"),
(43,"May",1,42,"d",0,0),(44,"Asuka",1,42,"d",0,0),(45,"Rin",1,44,"d",0,0),(46,"Midori",1,45,"d",0,0),
(47,"Shunichi",1,46,"o",1,0,"'The problem isn't just the money, Midori'"),(48,"May",2,47,"d",0,0),(49,"Asuka",2,48,"a",0,0),
(50,"Rin",1,49,"d",0,1,"opening sentiment sentence"),(51,"Midori",0,50,"g",0,0,"only agrees with [50]"),
(52,"Shunichi",1,50,"o",1,0,"argues against 'making it nicer' from [50]"),(53,"May",1,52,"d",1,0,"opposes Rin's [50] proposal"),
(54,"Asuka",1,52,"d",0,0),
(60,"Rin",1,N,N,0,0),(61,"Midori",1,N,N,0,0),(62,"Shunichi",1,N,N,0,0),(63,"May",1,N,N,0,0),(64,"Asuka",1,N,N,0,0),
(65,"Rin",0,64,"g",0,0,"celebrates agreement"),(66,"Midori",0,65,"g",0,0,"expresses relief only"),
(67,"Shunichi",1,N,N,0,0),(68,"May",1,67,"d",0,0),(69,"Asuka",1,67,"d",0,0),(70,"Rin",1,69,"d",0,0),
(71,"Midori",0,70,"g",0,0,"only agrees with [70]"),(72,"Shunichi",1,70,"o",1,0,"objects to a 'pretty' schedule"),
(73,"May",1,72,"o",1,0,"calls Shunichi a pessimist"),(74,"Asuka",1,70,"a",0,0),(75,"Rin",0,74,"g",0,0,"acknowledges [74]"),
(76,"Midori",1,N,N,0,1,"opening sentiment sentence"),(77,"Shunichi",0,76,"g",0,0,"joke accepting snacks"),
(78,"May",0,76,"g",0,0,"joke accepting snacks"),(79,"Asuka",1,N,N,0,1,"closing thanks"),
]
f2=[
(5,"Rin",1,N,N,0,1,"greeting and restated time point"),(6,"Toshio",1,5,"d",0,1,"second sentence restates the first"),
(7,"Mizuki",2,6,"d",0,0),(8,"Shion",2,7,"o",1,0,"'Fairness is a vague metric, Mizuki'"),(9,"Yumi",1,8,"d",0,1,"restates connection point"),
(10,"Rin",1,9,"d",0,0),(11,"Toshio",2,10,"d",0,0),(12,"Mizuki",2,11,"d",0,0),(13,"Shion",1,12,"d",0,0),(14,"Yumi",1,13,"d",0,0),
(15,"Rin",0,14,"g",0,1,"repeats her time concern from [10]"),(16,"Toshio",1,15,"d",0,1,"closing restatement of fiscal responsibility"),
(17,"Mizuki",1,16,"o",1,0,"budget should not dictate a hierarchy"),(18,"Shion",1,17,"d",0,0),(19,"Yumi",1,18,"d",0,0),
(20,"Rin",1,N,N,0,1,"closing sentiment"),(21,"Toshio",1,N,N,0,0),(22,"Mizuki",1,N,N,0,0),(23,"Shion",1,22,"d",0,0),
(24,"Yumi",1,N,N,0,1,"team-spirit sentiment attached"),
(35,"Rin",1,N,N,0,1,"restates the time point twice"),(36,"Toshio",2,35,"d",0,0),(37,"Mizuki",1,36,"d",0,0),(38,"Shion",2,37,"d",0,0),
(39,"Yumi",1,38,"d",0,0),(40,"Rin",1,38,"d",0,0),(41,"Toshio",1,40,"d",0,0),
(42,"Mizuki",1,41,"o",1,0,"challenges stability as hiding inequality"),(43,"Shion",1,42,"o",1,0,"rejects rotating into noise"),
(44,"Yumi",2,43,"d",0,0),(45,"Rin",1,44,"o",1,0,"'we can't let it make us slow'"),
(46,"Toshio",0,45,"g",0,0,"repeats his cost point from [41]"),(47,"Mizuki",1,46,"o",1,0,"argues fixed layout fixes the bad seat"),
(48,"Shion",1,47,"o",1,0,"'rotation is a flawed solution'"),(49,"Yumi",0,48,"o",1,1,"repeats [44]; closing sentiment"),
(50,"Rin",1,48,"d",0,1,"'I'm listening' opener and restated speed point"),(51,"Toshio",1,50,"d",0,1,"restates cost points within"),
(52,"Mizuki",1,51,"d",0,0),(53,"Shion",0,52,"o",1,0,"repeats [48]; opposes Mizuki's fairness"),
(54,"Yumi",1,53,"d",0,1,"'I hear you' opener and restated joiner point"),
(60,"Rin",2,N,N,0,0),(61,"Toshio",1,60,"d",0,0),(62,"Mizuki",1,61,"d",0,0),
(63,"Shion",2,62,"o",1,0,"calls hierarchy a social construct"),(64,"Yumi",1,63,"d",0,0),(65,"Rin",1,64,"a",0,0),
(66,"Toshio",1,64,"a",0,1,"last sentence restates budget point"),
(67,"Mizuki",0,66,"o",1,0,"repeats [62]; 'efficiency as a mask for unfairness'"),
(68,"Shion",1,67,"a",0,1,"repeated 'only logical choice' closing"),(69,"Yumi",1,68,"d",0,0),
(70,"Rin",0,69,"g",0,1,"repeats [60]/[65]"),(71,"Toshio",0,70,"g",0,1,"repeats cost points"),
(72,"Mizuki",1,71,"d",0,0),(73,"Shion",0,72,"d",0,1,"repeats physical priority and 'only rational path'"),
(74,"Yumi",0,72,"g",0,1,"agreement plus team-spirit sentiment"),
(75,"Rin",0,74,"g",0,1,"repeats preference from [60]; opener"),(76,"Toshio",0,N,N,0,1,"repeats earlier cost reasons"),
(77,"Mizuki",1,76,"d",0,0),(78,"Shion",0,N,N,0,1,"repeats earlier physical reasons"),
(79,"Yumi",0,N,N,0,1,"sentiment and repeated reasons"),
]
f3=[
(5,"Rin",1,N,N,0,1,"greeting and closing cheer"),(6,"Toshio",1,5,"d",0,0),(7,"Mizuki",1,6,"d",0,1,"thoroughness said twice"),
(8,"Shion",1,7,"d",0,0),(9,"Yumi",1,N,N,0,1,"opening and closing sentiment"),(10,"Rin",1,9,"d",0,0),
(11,"Toshio",1,N,N,0,0),(12,"Mizuki",1,N,N,0,0),(13,"Shion",1,N,N,0,0),(14,"Yumi",1,N,N,0,0),
(15,"Rin",0,14,"g",0,0,"general approval of the plan"),(16,"Toshio",0,15,"g",0,0,"comments on the plan without new point"),
(17,"Mizuki",1,16,"d",0,0),(18,"Shion",1,17,"o",1,0,"'Fairness is a convenient word, Mizuki'"),
(19,"Yumi",0,18,"o",1,1,"'don't be so gloomy'; general optimism"),(20,"Rin",0,N,N,0,0,"cheerleading only"),
(22,"Toshio",0,20,"g",0,0,"repeats wait-for-data and budget"),(24,"Mizuki",1,N,N,0,1,"waiting and looking-forward phrases"),
(26,"Shion",0,N,N,0,1,"repeats comfort-over-fairness from [18]"),(28,"Yumi",0,N,N,0,0,"cheerleading only"),
(40,"Rin",2,N,N,0,1,"closing filler sentence"),(41,"Toshio",2,N,N,0,0),(42,"Mizuki",2,N,N,0,0),
(43,"Shion",2,42,"d",0,1,"repeats comfort-is-requirement slogan"),(44,"Yumi",1,N,N,0,1,"'secret superpower' restates the point"),
(45,"Rin",2,41,"d",0,0),(46,"Toshio",1,45,"d",0,0),(47,"Mizuki",1,46,"o",1,0,"argues against prioritizing budget"),
(48,"Shion",1,47,"o",1,0,"'fairly usually means everyone is equally uncomfortable'"),
(49,"Yumi",1,46,"o",1,0,"argues closeness is worth the cost"),(50,"Rin",1,48,"o",1,0,"'you're making it sound so scary'"),
(51,"Toshio",1,49,"o",1,0,"'superpowers don't pay the bills'"),(52,"Mizuki",1,51,"d",0,0),(53,"Shion",1,52,"d",0,0),
(54,"Yumi",1,53,"d",0,0),(55,"Rin",1,54,"d",0,1,"closing cheer"),(56,"Toshio",1,55,"d",0,1,"restates budget priority"),
(57,"Mizuki",1,56,"d",0,0),(58,"Shion",1,57,"o",1,0,"'stop pretending that handling it is a strategy'"),
(59,"Yumi",0,58,"d",0,1,"general optimism; 'I'm so excited'"),
(65,"Rin",2,N,N,0,0),(66,"Toshio",2,N,N,0,0),(67,"Mizuki",2,65,"d",0,0),(68,"Shion",1,N,N,0,0),(69,"Yumi",1,68,"d",0,0),
(70,"Rin",2,69,"d",0,0),(71,"Toshio",1,70,"a",0,0),(72,"Mizuki",1,70,"a",0,0),(73,"Shion",1,70,"a",0,0),(74,"Yumi",2,70,"a",0,0),
(75,"Rin",1,74,"d",0,1,"restates time saving"),(76,"Toshio",1,75,"d",0,0),(77,"Mizuki",1,76,"d",0,0),(78,"Shion",1,77,"d",0,0),
(79,"Yumi",1,78,"g",0,1,"'so happy we all agree' opener"),(80,"Rin",0,79,"g",0,1,"repeats [75]"),
(81,"Toshio",0,N,N,0,1,"repeats [76]"),(82,"Mizuki",0,N,N,0,1,"repeats [77]"),(83,"Shion",0,82,"d",0,1,"repeats [78]"),
(84,"Yumi",0,N,N,0,1,"repeats [79]"),
]
d={"shared_living_0002__single-online.md":mk(f1),"shared_living_0003__multi-private-process.md":mk(f2),"shared_living_0003__multi-private.md":mk(f3)}
json.dump(d,open(sys.argv[1],"w"),ensure_ascii=False,indent=1)
for k,v in d.items(): print(k,len(v))
