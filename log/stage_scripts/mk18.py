import json
# seq,speaker,content,resp_to,type,rebut,padded,note
A=[
(5,"Rin",1,0,0,0,0,0,""),(6,"Midori",1,0,0,0,0,0,""),(7,"Shunichi",1,0,0,0,0,0,""),(8,"May",1,0,0,0,0,0,""),(9,"Asuka",1,0,0,0,0,0,""),
(10,"Rin",1,7,"add",0,0,0,""),(11,"Midori",0,10,"add",0,0,0,"repeats cost concern of [6]"),(12,"Shunichi",1,10,"answer",0,0,0,""),
(13,"May",2,9,"add",0,0,0,""),(14,"Asuka",0,13,"answer",0,0,0,"only says she has not looked yet"),
(15,"Rin",1,6,"add",0,0,0,""),(16,"Midori",1,15,"answer",0,0,0,""),(17,"Shunichi",0,16,"agree",0,1,"agrees, no new point"),
(18,"May",0,17,"add",0,0,0,"repeats [8]"),(19,"Asuka",0,18,"add",0,0,0,"repeats [9]"),
(20,"Rin",0,0,0,0,1,"farewell"),(21,"Midori",0,0,0,0,1,"restates plan, pleasantry"),(22,"Shunichi",0,0,0,0,1,"restates plan"),(23,"May",0,0,0,0,1,"restates plan"),(24,"Asuka",0,0,0,0,1,"restates plan"),
(35,"Rin",2,0,0,0,0,0,""),(36,"Midori",2,0,0,0,0,0,""),(37,"Shunichi",2,0,0,0,0,0,""),(38,"May",2,0,0,0,0,0,""),(39,"Asuka",2,0,0,0,0,0,""),
(40,"Rin",1,39,"add",0,0,0,""),(41,"Midori",1,40,"object",0,0,0,""),(42,"Shunichi",2,40,"object",1,0,0,""),(43,"May",1,42,"add",0,0,0,""),
(44,"Asuka",1,42,"add",0,0,0,""),(45,"Rin",1,44,"object",0,0,0,""),(46,"Midori",1,45,"add",0,0,0,""),(47,"Shunichi",1,46,"object",1,0,0,""),
(48,"May",2,44,"add",0,0,0,""),(49,"Asuka",1,48,"answer",0,0,0,""),(50,"Rin",1,49,"add",0,0,0,""),(51,"Midori",0,50,"agree",0,0,0,"agrees with [50]"),
(52,"Shunichi",1,50,"object",1,0,0,""),(53,"May",1,52,"add",0,0,0,""),(54,"Asuka",1,53,"add",0,0,0,""),
(60,"Rin",1,0,0,0,0,0,""),(61,"Midori",1,0,0,0,0,0,""),(62,"Shunichi",1,0,0,0,0,0,""),(63,"May",1,0,0,0,0,0,""),(64,"Asuka",1,0,0,0,0,0,""),
(65,"Rin",0,64,"agree",0,1,"celebration"),(66,"Midori",0,65,"add",0,1,"repeats [61]"),(67,"Shunichi",1,66,"add",0,0,0,""),(68,"May",1,67,"add",0,0,0,""),
(69,"Asuka",1,68,"add",0,0,0,""),(70,"Rin",1,69,"add",0,0,0,""),(71,"Midori",0,70,"agree",0,1,"pleasantry"),(72,"Shunichi",1,70,"object",0,0,0,""),
(73,"May",1,72,"object",1,0,0,""),(74,"Asuka",1,70,"answer",0,0,0,""),(75,"Rin",0,74,"agree",0,0,0,"acceptance"),(76,"Midori",1,0,0,0,0,0,""),
(77,"Shunichi",0,76,"agree",0,1,"joke"),(78,"May",0,76,"agree",0,1,"joke"),(79,"Asuka",1,78,"add",0,0,0,"")]
B=[
(5,"Rin",1,0,0,0,0,0,""),(6,"Toshio",1,5,"add",0,0,0,""),(7,"Mizuki",1,6,"add",0,0,0,""),(8,"Shion",1,7,"object",1,0,0,""),(9,"Yumi",1,8,"add",0,0,0,""),
(10,"Rin",1,9,"object",0,0,0,""),(11,"Toshio",1,10,"add",0,0,0,""),(12,"Mizuki",1,11,"add",0,0,0,""),(13,"Shion",1,12,"add",0,0,0,""),(14,"Yumi",1,13,"add",0,0,0,""),
(15,"Rin",0,14,"add",0,1,"repeats [10]"),(16,"Toshio",1,15,"add",0,0,0,""),(17,"Mizuki",1,16,"add",0,0,0,""),(18,"Shion",1,17,"add",0,0,0,""),(19,"Yumi",1,18,"add",0,0,0,""),
(20,"Rin",1,0,0,0,0,0,""),(21,"Toshio",1,0,0,0,0,0,""),(22,"Mizuki",1,0,0,0,0,0,""),(23,"Shion",1,22,"add",0,0,0,""),(24,"Yumi",1,0,0,0,0,0,""),
(35,"Rin",1,0,0,0,0,0,""),(36,"Toshio",1,35,"add",0,0,0,""),(37,"Mizuki",1,36,"add",0,0,0,""),(38,"Shion",1,37,"add",0,0,0,""),(39,"Yumi",1,38,"object",0,0,0,""),
(40,"Rin",1,39,"object",1,0,0,""),(41,"Toshio",1,40,"add",0,0,0,""),(42,"Mizuki",1,41,"add",0,0,0,""),(43,"Shion",1,42,"object",1,0,0,""),(44,"Yumi",1,43,"add",0,0,0,""),
(45,"Rin",0,44,"object",0,0,0,"repeats speed point of [40]"),(46,"Toshio",0,45,"add",0,0,0,"repeats [41]"),(47,"Mizuki",1,46,"object",0,0,0,""),(48,"Shion",1,47,"object",1,0,0,""),
(49,"Yumi",1,48,"add",0,0,0,""),(50,"Rin",1,49,"add",0,0,0,""),(51,"Toshio",1,50,"agree",0,0,0,""),(52,"Mizuki",0,51,"add",0,0,0,"repeats [42],[47]"),(53,"Shion",0,52,"object",0,0,0,"repeats [48]"),
(54,"Yumi",0,53,"add",0,0,0,"repeats [44],[49]"),
(60,"Rin",1,0,0,0,0,0,""),(61,"Toshio",1,60,"agree",0,0,0,""),(62,"Mizuki",0,61,"object",0,0,0,"repeats [42],[47]"),(63,"Shion",1,62,"object",1,0,0,""),
(64,"Yumi",1,63,"add",0,0,0,""),(65,"Rin",1,64,"answer",0,0,0,""),(66,"Toshio",1,64,"answer",0,0,0,""),(67,"Mizuki",0,66,"add",0,0,0,"repeats [62]"),(68,"Shion",0,67,"answer",0,0,0,"repeats [48]"),
(69,"Yumi",1,68,"agree",0,0,0,""),(70,"Rin",0,69,"add",0,0,0,"repeats [65]"),(71,"Toshio",0,70,"agree",0,1,"repeats [66]"),(72,"Mizuki",0,71,"add",0,0,0,"repeats [62]"),
(73,"Shion",0,72,"object",0,1,"repeats [63]"),(74,"Yumi",0,72,"agree",0,1,"agreement already given"),(75,"Rin",0,74,"agree",0,1,"restates preference for C"),
(76,"Toshio",0,0,0,0,1,"repeats [61]"),(77,"Mizuki",1,0,0,0,0,0,""),(78,"Shion",0,0,0,0,0,"repeats [63]"),(79,"Yumi",0,0,0,0,1,"repeats [69]")]
C=[
(5,"Rin",1,0,0,0,1,"greeting and enthusiasm"),(6,"Toshio",1,5,"add",0,0,0,""),(7,"Mizuki",1,6,"agree",0,0,0,""),(8,"Shion",1,6,"add",0,0,0,""),(9,"Yumi",0,8,"add",0,0,"general sentiment"),
(10,"Rin",1,9,"add",0,0,0,""),(11,"Toshio",1,0,0,0,0,0,""),(12,"Mizuki",1,0,0,0,0,0,""),(13,"Shion",1,0,0,0,0,0,""),(14,"Yumi",1,0,0,0,0,0,""),
(15,"Rin",0,14,"agree",0,1,"cheering"),(16,"Toshio",1,15,"add",0,0,0,""),(17,"Mizuki",1,16,"add",0,0,0,""),(18,"Shion",1,17,"object",1,0,0,""),(19,"Yumi",0,18,"object",1,1,"sentiment"),
(20,"Rin",0,0,0,0,1,"cheering"),(22,"Toshio",0,20,"agree",0,0,"agreement, repeats [16]"),(24,"Mizuki",0,0,0,0,0,"repeats [17]"),(26,"Shion",0,0,0,0,0,"repeats [18]"),(28,"Yumi",0,0,0,0,1,"cheering"),
(40,"Rin",2,0,0,0,0,0,""),(41,"Toshio",2,0,0,0,0,0,""),(42,"Mizuki",2,0,0,0,0,0,""),(43,"Shion",2,0,0,0,0,0,""),(44,"Yumi",1,0,0,0,0,0,""),
(45,"Rin",2,44,"add",0,0,0,""),(46,"Toshio",1,44,"object",0,0,0,""),(47,"Mizuki",1,46,"object",0,0,0,""),(48,"Shion",1,47,"object",1,0,0,""),(49,"Yumi",1,46,"object",1,0,0,""),
(50,"Rin",1,48,"object",1,0,0,""),(51,"Toshio",1,49,"object",1,0,0,""),(52,"Mizuki",0,51,"object",0,0,0,"repeats [47]"),(53,"Shion",0,52,"agree",0,0,0,"repeats [48]"),
(54,"Yumi",1,53,"object",1,0,0,""),(55,"Rin",0,54,"agree",0,0,0,"agrees with [54]"),(56,"Toshio",0,55,"add",0,0,0,"repeats [51]"),(57,"Mizuki",1,56,"add",0,0,0,""),
(58,"Shion",0,57,"object",1,0,0,"repeats [48]"),(59,"Yumi",0,58,"add",0,1,"repeats [54]"),
(65,"Rin",2,0,0,0,0,0,""),(66,"Toshio",1,65,"agree",0,0,0,""),(67,"Mizuki",1,66,"add",0,0,0,""),(68,"Shion",1,67,"add",0,0,0,""),(69,"Yumi",1,68,"agree",0,0,0,""),
(70,"Rin",1,69,"add",0,0,0,""),(71,"Toshio",1,70,"add",0,0,0,""),(72,"Mizuki",1,71,"add",0,0,0,""),(73,"Shion",1,72,"add",0,0,0,""),(74,"Yumi",1,70,"answer",0,0,0,""),
(75,"Rin",1,74,"agree",0,0,0,""),(76,"Toshio",1,75,"add",0,0,0,""),(77,"Mizuki",1,76,"add",0,0,0,""),(78,"Shion",1,77,"add",0,0,0,""),
(79,"Yumi",0,0,0,0,1,"repeats [74]"),(80,"Rin",0,0,0,0,1,"repeats [75]"),(81,"Toshio",0,0,0,0,1,"repeats [76]"),(82,"Mizuki",0,0,0,0,1,"vote already cast [77]"),
(83,"Shion",0,0,0,0,1,"repeats [78]"),(84,"Yumi",0,0,0,0,1,"repeats [79]")]
def conv(L):
    o=[]
    for t in L:
        if len(t)==9: s,sp,c,rt,ty,rb,pd,nt=t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[8]
        else: s,sp,c,rt,ty,rb,pd,nt=t
        raise
    return o
