"""Round-2 audit A: scenario leaks, option_perm consistency, condition diffs (read-only)."""
from __future__ import annotations
import csv, difflib, glob, json, re, sys
from pathlib import Path

ROOT = Path("/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
sys.path.insert(0, str(ROOT))
from common import render, scenario as S  # noqa
from common.setup import GameContext  # noqa
from single.base.prompt import build_messages, make_single_env  # noqa
from agent.base.prompts import build_system_prompt, make_agent_env  # noqa

LOG = ROOT / "log/_pilot6"
SETUPS = ["aiwolf_0001", "aiwolf_0002", "aiwolf_0003", "candidate_selection_0001", "candidate_selection_0002",
          "candidate_selection_0003", "shared_living_0001", "shared_living_0002", "shared_living_0003"]
DOM = lambda s: s.rsplit("_", 1)[0]
CONDS = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "single-batch-process", "multi-private-process"]
CDIR = {"single-batch-process": "single-batch", "multi-private-process": "multi-private"}


def games(setup, cond):
    d = LOG / DOM(setup) / CDIR.get(cond, cond)
    return sorted(p for p in d.glob(f"{setup}__{cond}__*") if p.is_dir())


def rows_of(g: Path):
    p = next(g.glob("*.jsonl"))
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def log_rows(g: Path):
    p = next(g.glob("*.log"))
    with open(p, encoding="utf-8", newline="") as f:
        return [dict(zip(["seq", "round", "turn", "type", "agent", "target", "text", "extra"], r)) for r in csv.reader(f)]


def plan_of(system: str) -> str:
    i = system.find("\n## Plan")
    return system[i + 1:] if i >= 0 else ""


sec = lambda t: print("\n" + "=" * 100 + "\n# " + t + "\n" + "=" * 100)

# ----------------------------------------------------------------------------------------------------------------
sec("1. scenarios at process granularity: validator + rendering + log Plan equality")
env_s, env_a = make_single_env(), make_agent_env()
for sid in SETUPS:
    ctx = GameContext.load(sid)
    path = S.scenario_path(ctx.domain, sid)
    sc = S.load_scenario(path)
    errs_file = S.validate_scenario(sc, ctx)
    pv = S.scenario_view(sc, "process")
    errs_proc = S.validate_scenario(pv, ctx)
    print(f"\n--- {sid}  file_gran={sc.get('granularity')} sha1={S.scenario_sha1(path)} mtime={path.stat().st_mtime:.0f}"
          f"  validator(file)={len(errs_file)} validator(process view)={len(errs_proc)}")
    for e in errs_file + errs_proc:
        print("   ERR", e)
    full = render.scenario_block(env_s, ctx, pv)
    print(full)
    # extra leak scan beyond the validator
    names = list(ctx.names)
    opts = ctx.options()
    txt = full
    hits = []
    for o in opts:
        for w in re.findall(r"[A-Za-z]{4,}", o["name"]):
            if re.search(r"\b" + re.escape(w) + r"\b", txt, re.I):
                hits.append(f"option word {w!r} (of {o['label']}: {o['name']})")
    roles = ["seer", "werewolf", "possessed", "villager", "wolf"]
    for r in roles:
        if ctx.domain == "aiwolf" and re.search(r"\b" + r + r"s?\b", txt, re.I):
            hits.append(f"role word {r!r}")
    for n in names:
        c = len(re.findall(r"\b" + n + r"\b", txt))
        if c > 1:
            hits.append(f"name {n} x{c} (1 = own seat label)")
    print("   SCAN:", hits or "clean")
    # log equality: single-batch-process (full plan) and multi-private-process (seat part)
    for cond in ("single-batch-process", "multi-private-process"):
        for g in games(sid, cond):
            rows = rows_of(g)
            h = rows[0]
            calls = [r for r in rows if r["kind"] == "llm_call"]
            ok = 0
            seen_seats = set()
            for c in calls:
                sysm = c["messages"][0]["content"]
                if cond == "single-batch-process":
                    exp = full
                else:
                    seat = int(c["seat"]); seen_seats.add(seat)
                    exp = render.scenario_block(env_a, ctx, pv, [seat])
                if plan_of(sysm) == exp:
                    ok += 1
                elif ok == 0:
                    print("   MISMATCH in", g.name, c.get("seat"), "\n", "\n".join(difflib.unified_diff(exp.splitlines(), plan_of(sysm).splitlines(), lineterm="", n=0)))
            print(f"   {cond}: Plan in log == render(process{'' if cond.startswith('single') else ', own seat'}) {ok}/{len(calls)} calls; "
                  f"header.scenario={h['scenario']} sha1_match_disk={h['scenario']['sha1'] == S.scenario_sha1(path)}; seats={sorted(seen_seats)}")
            if cond == "multi-private-process":
                # own part only? check no other name's part present
                bad = 0
                for c in calls:
                    pl = plan_of(c["messages"][0]["content"])
                    part = pl.split("Each participant's part:")[-1]
                    nm = re.findall(r"^- (\w+):", part, re.M)
                    if nm != [ctx.name_of_seat(int(c["seat"]))]:
                        bad += 1
                print(f"   multi-private-process: seat part names == own only: {len(calls) - bad}/{len(calls)}")

# ----------------------------------------------------------------------------------------------------------------
sec("2. option_perm consistency (candidate_selection_0001, shared_living_0002)")
for sid in ("candidate_selection_0001", "shared_living_0002"):
    ctx = GameContext.load(sid)
    opts = ctx.options()
    print(f"\n--- {sid} setup.option_perm={ctx.setup.option_perm} instance={ctx.setup.instance_id}")
    for o in opts:
        print(f"   shown {o['label']} <- orig {o['orig_label']}: {o['name']}")
    inst_order = [o["label"] for o in ctx.instance["topic"]["options"]]
    print("   instance order:", inst_order)
    hidden = render.hidden_block(env_s, ctx)
    hid_opts = re.findall(r"^- ([A-D]): (.+?)\.", hidden, re.M)
    print("   hidden.jinja options:", hid_opts)
    assert hid_opts == [(o["label"], o["name"]) for o in opts]
    for cond in CONDS:
        for g in games(sid, cond):
            rows = rows_of(g)
            h = rows[0]
            calls = [r for r in rows if r["kind"] == "llm_call"]
            # system Hidden information
            sys0 = calls[0]["messages"][0]["content"]
            hs = re.findall(r"^- ([A-D]): (.+?)\.", sys0[sys0.find("## Hidden information"):sys0.find("Cards")] if "## Hidden information" in sys0 else "", re.M)
            # seat views: ### Options in any user message
            optviews = set()
            for c in calls:
                for m in c["messages"][1:]:
                    u = m["content"]
                    if "### Options" in u:
                        seg = u[u.find("### Options"):]
                        seg = seg.split("\n\n")[0]
                        optviews.add(tuple(re.findall(r"^- ([A-D]): (.+?)\.", seg, re.M)))
            # vote rows and result
            lr = log_rows(g)
            votes = [(r["agent"], r["target"]) for r in lr if r["type"] == "vote"]
            res = [r["text"] for r in lr if r["type"] == "result"]
            # batch raw output's Options? (single-batch writes votes with labels)
            exp = [(o["label"], o["name"]) for o in opts]
            print(f"   {cond:24s} header.option_perm={h['option_perm']} sys_hidden={'==perm' if hs == exp else ('none' if not hs else hs)} "
                  f"views={'==perm' if optviews == {tuple(exp)} else (optviews or 'none')} votes={[t for _, t in votes]} result={res} "
                  f"outcome={h['outcome'].get('adopted') if h.get('outcome') else None}")
            cands = sorted({c["messages"][-1]["content"].splitlines()[1] for c in calls if c["request"] == "VOTE"}) if cond not in ("single-batch","single-batch-process") else []
            if cands: print("      VOTE candidates line(s):", cands)
            # check seat-view options text equals the hidden list line text exactly
            for c in calls:
                for m in c["messages"][1:]:
                    u = m["content"]
                    if "### Options" in u:
                        seg = u[u.find("### Options"):].split("\n\n")[0]
                        lines = [l for l in seg.splitlines()[1:] if re.match(r"^- [A-D]: ", l)]
                        hl = [l for l in hidden.splitlines() if re.match(r"^- [A-D]: ", l)]
                        if lines != hl:
                            print("      NOTE: Options lines differ from hidden list lines:", "\n       " + "\n       ".join(lines[:4]), "\n       vs", "\n       ".join(hl[:4]))
                        break
                else:
                    continue
                break

# ----------------------------------------------------------------------------------------------------------------
sec("3. condition diffs + re-render equality (aiwolf_0001, shared_living_0001)")
for sid in ("aiwolf_0001", "shared_living_0001"):
    ctx = GameContext.load(sid)
    path = S.scenario_path(ctx.domain, sid)
    pv = S.scenario_view(S.load_scenario(path), "process")
    systems = {}
    users = {}
    print(f"\n--- {sid}")
    for cond in CONDS:
        for g in games(sid, cond):
            rows = rows_of(g)
            calls = [r for r in rows if r["kind"] == "llm_call"]
            n_ok = 0; n_user_ok = 0
            for c in calls:
                sysm = c["messages"][0]["content"]
                if cond.startswith("single-batch"):
                    exp = build_messages(ctx, env_s, scenario=pv if cond.endswith("process") else None)
                    ok = sysm == exp[0]["content"]
                    uok = c["messages"][1]["content"] == exp[1]["content"]
                    n_user_ok += uok
                    key = (cond, None)
                else:
                    seat = int(c["seat"])
                    exp_s = build_system_prompt(ctx, seat, env_a, reveal=(cond == "multi-public"), writer=(cond == "single-online"),
                                                scenario=pv if cond.endswith("process") else None)
                    ok = sysm == exp_s
                    key = (cond, seat if cond.startswith("multi") else None)
                n_ok += ok
                systems.setdefault(key, sysm)
                if cond.startswith("single-batch") and key not in users:
                    users[key] = c["messages"][1]["content"]
                if sysm != systems[key]:
                    print("   system varies within condition!", g.name, c["seq"])
            print(f"   {g.name[:70]:70s} calls={len(calls):3d} system==rerender {n_ok}/{len(calls)}"
                  + (f" user==rerender {n_user_ok}/{len(calls)}" if cond.startswith("single-batch") else ""))
    # diffs
    base = systems[("single-batch", None)]
    def d(a, b, label):
        diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0))
        body = [l for l in diff[2:] if not l.startswith("@@")]
        print(f"\n   DIFF {label}: {len(body)} changed lines")
        for l in body[:40]:
            print("     ", l[:400])
    d(base, systems[("single-batch-stepped", None)], "single-batch -> single-batch-stepped")
    d(base, systems[("single-online", None)], "single-batch -> single-online")
    seat1 = min(s for c, s in systems if c == "multi-private")
    d(base, systems[("multi-public", seat1)], f"single-batch -> multi-public (seat {seat1})")
    d(systems[("multi-public", seat1)], systems[("multi-private", seat1)], f"multi-public -> multi-private (seat {seat1})")
    d(base, systems[("single-batch-process", None)], "single-batch -> single-batch-process")
    d(systems[("multi-private", seat1)], systems[("multi-private-process", seat1)], f"multi-private -> multi-private-process (seat {seat1})")
    # Plan text of single-batch-process vs union of multi-private-process seat parts
    full_plan = plan_of(systems[("single-batch-process", None)])
    for s in sorted(s for c, s in systems if c == "multi-private-process"):
        pl = plan_of(systems[("multi-private-process", s)])
        head = pl.split("Each participant's part:")[0]
        assert head == full_plan.split("Each participant's part:")[0], f"period lines differ for seat {s}"
    print("   Plan period lines identical across single-batch-process and all multi-private-process seats: OK")
    # users of single-batch family
    print("   user(single-batch)==user(stepped):", users[("single-batch", None)] == users[("single-batch-stepped", None)],
          " ==user(process):", users[("single-batch", None)] == users[("single-batch-process", None)])
    # stepped assistant/user structure of first call
    g = games(sid, "single-batch-stepped")[0]
    c0 = [r for r in rows_of(g) if r["kind"] == "llm_call"]
    print("   stepped roles:", [m["role"] for m in c0[0]["messages"]], "stop sets:", sorted({json.dumps(c.get("stop")) for c in c0}))
    for cond in ("single-online", "multi-public", "multi-private"):
        g = games(sid, cond)[0]
        cc = [r for r in rows_of(g) if r["kind"] == "llm_call"]
        print(f"   {cond}: requests={sorted({c['request'] for c in cc})} stop sets={sorted({json.dumps(c.get('stop')) for c in cc})} finish={sorted({c['finish_reason'] for c in cc})} max_comp={max(c['usage']['completion_tokens'] for c in cc)}")
        # first user of a VOTE and an ACTION call
        for req in ("VOTE", "DIVINE", "INVESTIGATE", "ATTACK"):
            v = [c for c in cc if c["request"] == req]
            if v:
                u = v[0]["messages"][-1]["content"]
                print(f"      {req} user head: {u.splitlines()[0][:120]!r} ... tail: {u.splitlines()[-1][:80]!r}")
    # single-batch stepped: divine validity (aiwolf)
    if ctx.domain == "aiwolf":
        for cond in ("single-batch-stepped", "single-online", "multi-public", "multi-private"):
            for g in games(sid, cond):
                lr = log_rows(g)
                acts = [(r["agent"], r["target"], json.loads(r["extra"])) for r in lr if r["type"] == "action" and json.loads(r["extra"]).get("action") == "divine"]
                print(f"   {cond}: divine rows {acts}")
