"""The experimental conditions (DESIGN §13): M1 reveal, S-online writer, the plan block and its deviations.

- the M1 / S-online system prompts are the single writer's with the role paragraph swapped;
- S-online: five real agents sharing the writer view play against the real server, and every TALK / VOTE /
  action user message equals the writer view rebuilt from the log (byte for byte) plus the label;
- scenarios: the canned plan validates, broken plans are rejected, deviations of a played game are found,
  and the CLIs (gen_scenarios --fake, run_multi --fake --writer --scenario, single --fake --scenario) wire up.
"""
from __future__ import annotations

import asyncio
import copy
import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from agent.base import FakeLLM, build_system_prompt, run_client
from agent.base.registry import make_game_agents
from common import ROOT
from common.conditions import multi_tag
from common.convert.single_markdown import convert
from common.logwriter import read_jsonl, read_log
from common.render import make_env, role_block, scenario_block, system_prompt
from common.scenario import find_scenario_deviations, scenario_view, validate_scenario
from common.setup import GameContext
from common.transcript import view_from_rows
from server.base.runner import run_game
from single.base import build_messages
from single.base.fake import canned_scenario

PY = sys.executable


def _swap_role(text: str, old: str, new: str) -> str:
    assert text.startswith(old + "\n\n")
    return new + text[len(old):]


@pytest.mark.parametrize("setup_id", ["aiwolf_0001", "candidate_selection_0001"])
def test_reveal_and_online_prompts_are_the_single_prompt_with_another_role(setup_id):
    ctx = GameContext.load(setup_id)
    env = make_env()
    single_sys = build_messages(ctx)[0]["content"]
    for seat in range(1, 6):
        m1 = build_system_prompt(ctx, seat, reveal=True)
        assert m1 == _swap_role(single_sys, role_block(env, ctx, "single"), role_block(env, ctx, "multi", seat))
        on = build_system_prompt(ctx, seat, writer=True)
        assert on == _swap_role(single_sys, role_block(env, ctx, "single"), role_block(env, ctx, "online"))
        assert "## Participants" in m1 and "## Your profile" not in m1
    if ctx.domain != "aiwolf":
        assert "## Hidden information" in single_sys
    m0 = build_system_prompt(ctx, 2)
    assert "## Your profile" in m0 and "## Participants" not in m0 and "## Hidden information" not in m0


def test_condition_tags():
    from common.conditions import condition_tag, parse_condition
    assert condition_tag("single", generation="batch-stepped", plan="process") == "single-batch-stepped-process"
    assert parse_condition("single-batch-stepped-process") == {"tag": "single-batch-stepped-process", "method": "single",
                                                              "generation": "batch-stepped", "information": "public",
                                                              "plan": "process", "dir": "single-batch-stepped"}
    assert parse_condition("multi-private-process")["dir"] == "multi-private"
    assert multi_tag(plan="process") == "multi-private-process" and multi_tag(plan="outline") == "multi-public-outline"
    with pytest.raises(ValueError):
        condition_tag("multi", information="private", plan="outline")
    with pytest.raises(ValueError):
        parse_condition("single-stepped")
    assert multi_tag(seat_stepped=True) == "multi-private-stepped" and multi_tag(reveal=True, seat_stepped=True) == "multi-public-stepped"
    assert parse_condition("multi-private-stepped-process") == {"tag": "multi-private-stepped-process", "method": "multi",
                                                               "information": "private", "generation": "batch-stepped",
                                                               "plan": "process", "dir": "multi-private-stepped"}
    assert condition_tag("multi", information="public", generation="batch-stepped") == "multi-public-stepped"


def test_plan_block_is_appended_identically_for_every_condition():
    ctx = GameContext.load("aiwolf_0001")
    sc = canned_scenario(ctx)
    assert validate_scenario(sc, ctx) == []
    plan = scenario_block(make_env(), ctx, sc)
    assert plan.startswith("## Plan\n") and "Outcome: the village wins." in plan
    for n in ctx.names:
        assert f"- {n}: " in plan
    assert build_messages(ctx, scenario=sc)[0]["content"] == build_messages(ctx)[0]["content"] + "\n\n" + plan
    for seat in (1, 4):
        assert build_system_prompt(ctx, seat, reveal=True, scenario=sc) == build_system_prompt(ctx, seat, reveal=True) + "\n\n" + plan
        assert build_system_prompt(ctx, seat, writer=True, scenario=sc) == build_system_prompt(ctx, seat, writer=True) + "\n\n" + plan
        # without reveal only the own part is shown (not a study condition, but the block must stay consistent)
        own = system_prompt(make_env(), ctx, "multi", seat, scenario=sc)
        assert f"- {ctx.name_of_seat(seat)}: " in own
        assert sum(1 for n in ctx.names if f"\n- {n}: " in own.split("Each participant's part:")[1]) == 1


def test_granularity_views_are_derived_by_deletion():
    ctx = GameContext.load("aiwolf_0001")
    sc = canned_scenario(ctx)
    assert sc["granularity"] == "turn" and validate_scenario(sc, ctx) == []
    env = make_env()
    turn = scenario_block(env, ctx, scenario_view(sc, "turn"))
    outline = scenario_block(env, ctx, scenario_view(sc, "outline"))
    outcome = scenario_block(env, ctx, scenario_view(sc, "outcome"))
    assert "  - Turn 1: " in turn and "  - Turn" not in outline and "  - Turn" not in outcome
    assert "Each participant's part:" in turn and "Each participant's part:" in outline
    assert "Each participant's part:" not in outcome and "introduces themselves" not in outcome
    assert "Executed:" in outcome and "Votes:" in outcome and "Outcome: the village wins." in outcome
    # the outline is the turn view minus the turn lines; the outcome is the outline minus public text and parts
    assert outline == "\n".join(ln for ln in turn.splitlines() if not ln.startswith("  - Turn"))
    assert validate_scenario(scenario_view(sc, "outline"), ctx) == []
    process = scenario_block(env, ctx, scenario_view(sc, "process"))
    assert "Votes:" not in process and "Executed:" not in process and "Night:" not in process and "Outcome:" not in process
    assert "introduces themselves" in process and "Each participant's part:" in process
    assert validate_scenario(scenario_view(sc, "process"), ctx) == []
    with pytest.raises(ValueError):
        scenario_view(scenario_view(sc, "outline"), "turn")
    with pytest.raises(ValueError):
        scenario_view(scenario_view(sc, "process"), "outcome")
    leaky = copy.deepcopy(sc)
    leaky["periods"][1]["public"] += " Shizue is executed."
    assert any("states an outcome" in e for e in validate_scenario(leaky, ctx))
    bad = copy.deepcopy(sc)
    bad["periods"][1]["turns"][0]["lines"][ctx.names[0]] = ctx.rules["pass_over"]
    assert any("already said" in e for e in validate_scenario(bad, ctx))
    bad = copy.deepcopy(sc)
    bad["periods"][1]["turns"][1]["lines"]["Nobody"] = "hi"
    assert any("unknown name" in e for e in validate_scenario(bad, ctx))


def test_scenario_validation_rejects_inconsistent_plans():
    ctx = GameContext.load("aiwolf_0001")
    sc = canned_scenario(ctx)
    bad = copy.deepcopy(sc)
    bad["periods"][1]["executed"] = ctx.names[0] if ctx.names[0] != bad["periods"][1]["executed"] else ctx.names[1]
    assert any("does not follow from the votes" in e for e in validate_scenario(bad, ctx))
    bad = copy.deepcopy(sc)
    bad["final"]["winner"] = "WEREWOLF"
    assert any("final.winner" in e for e in validate_scenario(bad, ctx))
    bad = copy.deepcopy(sc)
    del bad["seats"][ctx.names[2]]
    assert any("no line for" in e for e in validate_scenario(bad, ctx))
    bad = copy.deepcopy(sc)
    bad["periods"][0]["divine"] = bad["periods"][0]["divine"] and ctx.names[2]  # the Seer divining itself?
    seer = next(n for n in ctx.names if ctx.role_of_name(n) == "SEER")
    bad["periods"][0]["divine"] = seer
    assert any("divine target" in e for e in validate_scenario(bad, ctx))
    dctx = GameContext.load("shared_living_0001")
    dsc = canned_scenario(dctx)
    assert validate_scenario(dsc, dctx) == []
    bad = copy.deepcopy(dsc)
    bad["periods"][-1]["votes"][dctx.names[0]] = "Z"
    assert any("not allowed" in e for e in validate_scenario(bad, dctx))


def play(ctx: GameContext, log_dir: Path, *, writer: bool = False, reveal: bool = False, stepped: bool = False,
         scenario=None, scenario_info=None, seat_stepped: bool = False):
    port_ev = threading.Event()
    box: dict = {}
    condition = multi_tag(reveal=reveal, writer=writer, stepped=stepped, plan=(scenario or {}).get("granularity") if scenario else None,
                          seat_stepped=seat_stepped)

    def on_listening(port: int) -> None:
        box["port"] = port
        port_ev.set()

    def server_main() -> None:
        try:
            box["game"] = asyncio.run(run_game(ctx, 0, log_dir, timeout=10, model_tag="fake", on_listening=on_listening,
                                               connect_timeout=20, condition=condition,
                                               scenario=scenario, scenario_info=scenario_info))
        except BaseException as e:  # noqa: BLE001
            box["error"] = e
        finally:
            port_ev.set()

    th = threading.Thread(target=server_main, daemon=True)
    th.start()
    assert port_ev.wait(10) and "error" not in box
    url = f"ws://127.0.0.1:{box['port']}"
    if seat_stepped:
        from agent.base.registry import make_agent
        agents = [make_agent(ctx, s, FakeLLM(), log_dir, reveal=reveal, scenario=scenario, seat_stepped=True) for s in range(1, 6)]
    else:
        agents = make_game_agents(ctx, FakeLLM, log_dir, writer=writer, reveal=reveal, stepped=stepped, scenario=scenario)
    threads = [threading.Thread(target=run_client, args=(url, a), kwargs={"connect_timeout": 20}, daemon=True)
               for a in agents]
    for t in threads:
        t.start()
    th.join(120)
    for t in threads:
        t.join(10)
    assert "error" not in box, box.get("error")
    game = box["game"]
    rows = read_log(game.game_dir / f"{game.game_id}.log")
    return game, rows, agents


@pytest.mark.parametrize("setup_id,info_mode", [("aiwolf_0001", "dynamic"), ("candidate_selection_0001", "dynamic"),
                                                ("shared_living_0001", "fixed")])
def test_online_writer_messages_equal_the_writer_view_of_the_log(setup_id, info_mode, tmp_path):
    ctx = GameContext.load(setup_id)
    ctx.setup.info_mode = info_mode
    game, rows, agents = play(ctx, tmp_path, writer=True)
    assert any(r.type == "result" for r in rows)
    assert "__single-online__" in game.game_id and game.game_dir.parent.name == "single-online"
    shared = agents[0].view
    assert all(a.view is shared for a in agents) and shared.seat is None
    checked = {"TALK": 0, "VOTE": 0, "ACTION": 0}
    for ag in agents:
        name = ag.name
        assert ag.system_prompt == build_system_prompt(ctx, ag.seat, writer=True)
        for rec in ag.records:
            req = rec["request"]
            user = rec["messages"][1]["content"]
            if req == "TALK":
                row = next(r for r in rows if r.type in ("talk", "pass") and r.round == rec["round"]
                           and r.turn == rec["turn"] and r.agent == name)
                exp = view_from_rows(rows, ctx, None, upto_seq=row.seq, ensure_turn=(row.round, row.turn)).render() + f"\n- **{name}**:"
                assert user == exp, (name, rec["round"], rec["turn"])
                checked["TALK"] += 1
            elif req == "VOTE":
                row = next(r for r in rows if r.type == "vote" and r.round == rec["round"] and r.agent == name)
                v = view_from_rows(rows, ctx, None, upto_seq=row.seq)
                tail = ("\n" if v.section_open(row.round, "vote") else "\n### Vote\n") + f"- {name} ->"
                assert user.endswith("\n\n" + v.render() + tail), (name, rec["round"])
                checked["VOTE"] += 1
            else:
                kind = {"DIVINE": "divine", "ATTACK": "attack", "INVESTIGATE": "investigate"}[req]
                row = next(r for r in rows if r.type == "action" and r.round == rec["round"] and r.agent == name
                           and r.extra.get("action") == kind)
                v = view_from_rows(rows, ctx, None, upto_seq=row.seq)
                tail = ("\n" if v.section_open(row.round, "action") else "\n### Action\n") + f"- {kind}: {name} ->"
                assert user.endswith("\n\n" + v.render() + tail), (name, rec["round"], req)
                checked["ACTION"] += 1
    assert checked["TALK"] >= 20 and checked["VOTE"] >= 3
    if info_mode == "dynamic":
        assert checked["ACTION"] >= 1
    # the live shared view at the end equals the writer view of the whole log (minus the result line)
    final = view_from_rows(rows, ctx, None).render()
    assert shared.render().split("\n## Result")[0] == final.split("\n## Result")[0]


@pytest.mark.parametrize("setup_id", ["aiwolf_0001", "candidate_selection_0001"])
def test_stepped_messages_are_the_batch_prompt_plus_the_writer_view_as_assistant(setup_id, tmp_path):
    ctx = GameContext.load(setup_id)
    game, rows, agents = play(ctx, tmp_path, stepped=True)
    assert any(r.type == "result" for r in rows)
    assert "__single-batch-stepped__" in game.game_id and game.game_dir.parent.name == "single-batch-stepped"
    batch = build_messages(ctx)
    checked = 0
    for ag in agents:
        name = ag.name
        for rec in ag.records:
            msgs = rec["messages"]
            assert msgs[0] == batch[0] and msgs[1] == batch[1] and msgs[2]["role"] == "assistant"
            assert rec["continuation"] == "fake"
            req = rec["request"]
            if req == "TALK":
                row = next(r for r in rows if r.type in ("talk", "pass") and r.round == rec["round"]
                           and r.turn == rec["turn"] and r.agent == name)
                exp = view_from_rows(rows, ctx, None, upto_seq=row.seq, ensure_turn=(row.round, row.turn)).render() + f"\n- **{name}**:"
                assert msgs[2]["content"] == exp, (name, rec["round"], rec["turn"])
                assert rec["stop"] == ag.stop_talk
            else:
                assert rec["stop"] == ["\n"]
                assert msgs[2]["content"].endswith("->")
            checked += 1
    assert checked >= 25
    # the stepped prefix is what the batch writer would have written: it round-trips through the converter
    writer = view_from_rows(rows, ctx, None).render()
    res = convert(writer, ctx, "roundtrip")
    assert not [v for v in res.violations if v["code"] not in ("format_noise",)], res.violations


def test_private_process_plan_condition(tmp_path):
    ctx = GameContext.load("shared_living_0001")
    sc = scenario_view(canned_scenario(ctx), "process")
    game, rows, agents = play(ctx, tmp_path, scenario=sc, scenario_info={"path": "p", "sha1": "s", "granularity": "process"})
    assert "__multi-private-process__" in game.game_id
    for ag in agents:
        sysp = ag.system_prompt
        assert "## Plan" in sysp and "## Your profile" in sysp and "## Participants" not in sysp
        own = ctx.name_of_seat(ag.seat)
        part = sysp.split("Each participant's part:")[1]
        assert f"- {own}: " in part and sum(1 for n in ctx.names if f"\n- {n}: " in part) == 1


def test_deviations_are_recorded_with_the_violations(tmp_path):
    ctx = GameContext.load("aiwolf_0001")
    sc = canned_scenario(ctx)
    game, rows, agents = play(ctx, tmp_path, reveal=True, scenario=sc, scenario_info={"path": "x", "sha1": "y", "granularity": "turn"})
    recs = list(read_jsonl(game.game_dir / f"{game.game_id}.jsonl"))
    header = recs[0]
    assert header["condition"] == "multi-public-turn" and header["method"] == "multi" and header["pipeline"] == "server"
    assert header["axes"] == {"method": "multi", "generation": "online", "information": "public", "plan": "turn"}
    assert header["scenario"] == {"path": "x", "sha1": "y", "granularity": "turn"}
    items = next(r for r in recs if r.get("kind") == "violations")["items"]
    devs = [v for v in items if v["code"] == "scenario_deviation"]
    assert devs and all(v["kind"] == "deviation" for v in devs)
    assert devs == find_scenario_deviations(rows, ctx, sc)
    # FakeLLM votes for the first candidate, the plan says everyone votes the wolf: at least the votes differ
    assert any(v["detail"]["what"] in ("vote", "execution", "winner") for v in devs)
    for ag in agents:
        assert ag.system_prompt == build_system_prompt(ctx, ag.seat, reveal=True, scenario=sc)


def test_cli_wiring_with_fake_llm(tmp_path):
    out = tmp_path / "scn"
    r = subprocess.run([PY, "scripts/gen_scenarios.py", "--setups", "aiwolf_0002,shared_living_0002", "--fake",
                        "--out-dir", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    sp = out / "aiwolf" / "aiwolf_0002.json"
    assert sp.is_file() and json.loads(sp.read_text())["source"]["generated_by"].endswith("gen_scenarios.py")
    log = tmp_path / "log"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    r = subprocess.run([PY, "scripts/run_multi.py", "--setup", "aiwolf_0002", "--fake", "--log-dir", str(log),
                        "--port", str(port), "--writer", "--scenario", str(sp)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    gdirs = list((log / "aiwolf" / "single-online").iterdir())
    assert len(gdirs) == 1 and "__single-online-process__" in gdirs[0].name
    header = list(read_jsonl(gdirs[0] / f"{gdirs[0].name}.jsonl"))[0]
    assert header["condition"] == "single-online-process" and header["method"] == "single" and header["pipeline"] == "server"
    assert header["scenario"]["granularity"] == "process" and header["scenario"]["file_granularity"] == "turn"

    r = subprocess.run([PY, "-m", "single", "--setup", "shared_living_0002", "--fake", "--log-dir", str(log),
                        "--scenario", str(out / "shared_living" / "shared_living_0002.json"), "--plan-granularity", "turn"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    sdirs = list((log / "shared_living" / "single-batch").iterdir())
    assert len(sdirs) == 1 and "__single-batch-turn__" in sdirs[0].name
    recs = list(read_jsonl(sdirs[0] / f"{sdirs[0].name}.jsonl"))
    assert recs[0]["condition"] == "single-batch-turn" and recs[0]["pipeline"] == "batch" and recs[0]["scenario"]["granularity"] == "turn"
    assert "## Plan" in recs[1]["messages"][0]["content"] and "  - Turn 1: " in recs[1]["messages"][0]["content"]


@pytest.mark.parametrize("setup_id", ["aiwolf_0001", "candidate_selection_0001"])
def test_seat_stepped_messages_are_the_participant_prompt_plus_the_batch_request_and_the_own_view(setup_id, tmp_path):
    """multi-private-stepped: system = the seat's own (private) participant prompt, user = the single-batch writing
    request, assistant = the seat's own view so far + its label; only the seat's own line reaches the server."""
    from agent.base.registry import make_agent
    ctx = GameContext.load(setup_id)
    game, rows, agents = play(ctx, tmp_path, seat_stepped=True)
    assert any(r.type == "result" for r in rows)
    assert "__multi-private-stepped__" in game.game_id and game.game_dir.parent.name == "multi-private-stepped"
    batch_user = build_messages(ctx)[1]
    checked = 0
    for ag in agents:
        plain = make_agent(ctx, ag.seat, FakeLLM(), tmp_path)  # the multi-private agent of the same seat
        assert ag.system_prompt == plain.system_prompt and ag.condition == "multi-private-stepped"
        for rec in ag.records:
            msgs = rec["messages"]
            assert msgs[0]["content"] == plain.system_prompt and msgs[1] == batch_user and msgs[2]["role"] == "assistant"
            assert rec["continuation"] == "fake"
            if rec["request"] == "TALK":
                row = next(r for r in rows if r.type in ("talk", "pass") and r.round == rec["round"]
                           and r.turn == rec["turn"] and r.agent == ag.name)
                exp = view_from_rows(rows, ctx, ag.seat, upto_seq=row.seq, ensure_turn=(row.round, row.turn)).render() + f"\n- **{ag.name}**:"
                assert msgs[2]["content"] == exp, (ag.name, rec["round"], rec["turn"])
                assert rec["stop"] == ag.stop_talk
            else:
                assert msgs[2]["content"].endswith("->")
            checked += 1
    assert checked >= 25
