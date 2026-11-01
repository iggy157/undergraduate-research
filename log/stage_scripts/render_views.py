import sys, glob, json
sys.path.insert(0, "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
from common.logwriter import read_log
from common.setup import GameContext
from common.transcript import view_from_rows
LOG="log/_pilot5"
out=sys.argv[1]
for setup in ["aiwolf_0001","candidate_selection_0001"]:
    dom=setup.rsplit("_",1)[0]
    for f in sorted(glob.glob(f"{LOG}/{dom}/*/{setup}__*/*.jsonl")):
        if "/raw/" in f: continue
        h=json.loads(open(f).readline())
        cond=h["condition"]
        rows=list(read_log(f.replace(".jsonl",".log")))
        ctx=GameContext.load(setup); ctx.setup.info_mode=h["info_mode"]
        txt=view_from_rows(rows,ctx,None).render()
        open(f"{out}/{setup}__{cond}.writer.md","w").write(txt)
        # csv-ish dump
        with open(f"{out}/{setup}__{cond}.rows.txt","w") as g:
            for r in rows:
                g.write(f"{r.seq}\t{r.round}\t{r.turn}\t{r.type}\t{r.agent}\t{r.target}\t{r.text!r}\t{r.extra}\n")
        print(cond, len(rows), "rows", len(txt.splitlines()), "lines")
