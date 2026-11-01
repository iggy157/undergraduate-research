import sys, os, glob, json
sys.path.insert(0, "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
from common.logwriter import read_log
from common.transcript import view_from_rows
from common.setup import GameContext
domain, setup = sys.argv[1], sys.argv[2]
conds = sys.argv[3].split(",")
for c in conds:
    for d in sorted(glob.glob(f"log/_pilot5/{domain}/{c}/{setup}__*")):
        gid = os.path.basename(d)
        tag = gid.split("__")[1]
        if len(sys.argv) > 4 and tag != sys.argv[4]: continue
        recs = [json.loads(l) for l in open(os.path.join(d, gid + ".jsonl"))]
        h = recs[0]
        print("=" * 30, gid)
        print("header keys:", sorted(h.keys()))
        print("sampling:", h.get("sampling"), "model_info:", {k: h.get("model_info", {}).get(k) for k in list(h.get("model_info", {}))[:6]})
        rows = list(read_log(os.path.join(d, gid + ".log")))
        ctx = GameContext.load(h["setup_id"]); ctx.setup.info_mode = h["info_mode"]
        print(view_from_rows(rows, ctx, None, None))
