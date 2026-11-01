import json, glob, os, sys
sys.path.insert(0, os.getcwd())
from common.setup import GameContext
from common.render import make_env
from common.scenario import load_scenario, scenario_path, scenario_view
from single.base.prompt import build_messages
from agent.base.prompts import build_system_prompt
root="log/_pilot5"
def rows(sid, cond):
    dom = sid.rsplit("_",1)[0]
    ds = sorted(glob.glob(f"{root}/{dom}/{cond.split('-process')[0]}/{sid}__{cond}__*"))
    gid=os.path.basename(ds[0])
    return [json.loads(l) for l in open(f"{ds[0]}/{gid}.jsonl")]
for sid in ["aiwolf_0001","candidate_selection_0001","shared_living_0001"]:
    ctx=GameContext.load(sid)
    sc=load_scenario(scenario_path(ctx.domain,sid)); proc=scenario_view(sc,"process")
    for cond in ["single-batch","single-batch-stepped","single-online","multi-public","multi-private","single-batch-process","multi-private-process"]:
        rs=rows(sid,cond); calls=[r for r in rs if r.get("kind")=="llm_call"]
        scn = proc if cond.endswith("process") else None
        ok_sys=ok_user=0; n=len(calls); bad=[]
        for c in calls:
            m=c["messages"]
            if cond.startswith("single-batch") and not cond.startswith("single-batch-stepped") or cond=="single-batch-process":
                exp=build_messages(ctx, scenario=scn)
                ok_sys += m[0]["content"]==exp[0]["content"]; ok_user += m[1]["content"]==exp[1]["content"]
            elif cond=="single-batch-stepped":
                exp=build_messages(ctx)
                ok_sys += m[0]["content"]==exp[0]["content"]; ok_user += m[1]["content"]==exp[1]["content"]
            elif cond=="single-online":
                exp=build_system_prompt(ctx, int(c["seat"]), writer=True, scenario=scn)
                ok_sys += m[0]["content"]==exp
            elif cond.startswith("multi-public"):
                exp=build_system_prompt(ctx, int(c["seat"]), reveal=True, scenario=scn)
                ok_sys += m[0]["content"]==exp
            else:
                exp=build_system_prompt(ctx, int(c["seat"]), scenario=scn)
                ok_sys += m[0]["content"]==exp
                if m[0]["content"]!=exp: bad.append(c["seat"])
        print(f"{sid:28s} {cond:24s} calls={n:3d} system==rerender {ok_sys}/{n}" + (f" user==rerender {ok_user}/{n}" if ok_user else "") + (f" bad seats {sorted(set(bad))}" if bad else ""))
