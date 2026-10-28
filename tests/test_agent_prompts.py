"""Multi-agent client: prompt assembly, notices, candidates, error handling, jsonl (no network, no LLM).

A fake server stub feeds Packet dicts straight into ``SeatAgent.handle_dict``; the last test replays
the same packets over a real websocket (``websockets`` sync server in a thread) to cover ``run_client``.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from agent.base import LLM_CALL_FIELDS, FakeLLM, build_system_prompt, make_agent, run_client
from agent.base.dump import dump_prompts
from common.logwriter import read_jsonl
from common.protocol import ACK, T_FORCE_SKIP
from common.render import identity_block, make_env, role_block, rules_context, shared_block
from common.transcript import SeatTranscript
from common.setup import GameContext

AIWOLF = "aiwolf_0001"
LIVING = "shared_living_0001"
PANEL = "candidate_selection_0001"
TITLES = ["Cost of last year's camp", "Travel time by coach", "Coach access", "Lodge capacity",
          "Weather in August", "Kitchen facilities", "Pitch hire fees", "Nearby alternatives",
          "Booking deadlines", "Member survey"]


# ---- fakes ------------------------------------------------------------------------------------
class ScriptedLLM:
    """Returns queued replies in order; records every call."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[tuple[list[dict[str, str]], int]] = []

    def complete(self, messages, max_tokens):
        self.calls.append(([dict(m) for m in messages], max_tokens))
        text = self.replies.pop(0) if self.replies else "Skip"
        return text, {"finish_reason": "stop", "usage": {"prompt_tokens": 10, "completion_tokens": 3,
                                                        "total_tokens": 13}, "model": "scripted"}


class FailingLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, messages, max_tokens):
        self.calls += 1
        raise RuntimeError("endpoint down")


# ---- packet stub ---------------------------------------------------------------------------------
def info(ctx: GameContext, seat: int, day: int, game_id: str = "g1", status: dict[str, str] | None = None,
         **extra: Any) -> dict[str, Any]:
    me = ctx.name_of_seat(seat)
    d = {"game_id": game_id, "day": day, "agent": me,
         "status_map": status or {n: "ALIVE" for n in ctx.names},
         "role_map": {me: ctx.role_of_seat(seat)}}
    d.update(extra)
    return d


def talk(idx: int, day: int, turn: int, agent: str, text: str, skip=False, over=False) -> dict[str, Any]:
    return {"idx": idx, "day": day, "turn": turn, "agent": agent, "text": text, "skip": skip, "over": over}


def pkt(request: str, inf: dict[str, Any] | None = None, talks: list[dict] | None = None,
        setting: dict | None = None) -> dict[str, Any]:
    return {"request": request, "info": inf, "setting": setting, "talk_history": talks,
            "whisper_history": None}


def make(setup: str, seat: int, llm, tmp_path: Path):
    ctx = GameContext.load(setup)
    return ctx, make_agent(ctx, seat, llm, tmp_path)


def expected_system(ctx: GameContext, seat: int) -> str:
    env = make_env()
    return "\n\n".join([role_block(env, ctx, "multi", seat)] +
                       [shared_block(env, ctx, b) for b in ("setting", "structure", "schedule", "action")] +
                       ["## Your profile\n" + identity_block(env, ctx, seat)])


# ---- tests --------------------------------------------------------------------------------------
@pytest.mark.parametrize("setup,seat", [(AIWOLF, 3), (LIVING, 1), (PANEL, 5)])
def test_system_prompt_is_concatenation_of_shared_blocks(setup, seat, tmp_path):
    ctx, ag = make(setup, seat, FakeLLM(), tmp_path)
    exp = expected_system(ctx, seat)
    assert build_system_prompt(ctx, seat) == exp
    assert ag.messages[0] == {"role": "system", "content": exp}
    name = ctx.name_of_seat(seat)
    assert exp.startswith(f"You are {name}, one of the participants")
    assert f"\n\n## Your profile\nName: {name}\n" in exp
    assert exp.count("\n\n") >= 5


def test_name_request_returns_connection_name(tmp_path):
    _, ag = make(AIWOLF, 4, FakeLLM(), tmp_path)
    assert ag.handle_dict(pkt("NAME")) == "seat4"
    assert ag.view.render() == "# aiwolf_0001"  # nothing known yet


def test_notices_are_static_ack_without_llm_call(tmp_path):
    llm = ScriptedLLM([])
    ctx, ag = make(AIWOLF, 2, llm, tmp_path)
    assert ag.handle_dict(pkt("INITIALIZE", info(ctx, 2, 0), setting={})) == ACK
    assert ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 0))) == ACK
    assert ag.handle_dict(pkt("DAILY_FINISH", info(ctx, 2, 0), talks=[talk(0, 0, 1, ctx.names[0], "hi")])) == ACK
    assert ag.handle_dict(pkt("FINISH", info(ctx, 2, 1))) == ACK
    assert llm.calls == [] and ag.records == []
    assert not ag.raw_jsonl_path().exists() or ag.raw_jsonl_path().read_text() == ""
    # notices only update the seat view (no notice text ever reaches the model)
    assert ag.view.render() == f"# aiwolf_0001\n## Day 0\n### Talk\n#### Turn 1 of 4\n- **{ctx.names[0]}**: hi"


def test_talk_message_is_seat_view_plus_own_label(tmp_path):
    llm = ScriptedLLM(["I think we should all share what we know.", "Over"])
    ctx, ag = make(AIWOLF, 3, llm, tmp_path)
    me = ctx.name_of_seat(3)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 3, 0)))
    a, b = ctx.speaking_order_names[0], ctx.speaking_order_names[1]
    talks = [talk(0, 0, 1, a, "Good morning."), talk(1, 0, 1, b, "Skip", skip=True)]
    reply = ag.handle_dict(pkt("TALK", info(ctx, 3, 0, remain_count=4), talks=talks))
    assert reply == "I think we should all share what we know."
    msgs = llm.calls[0][0]
    assert [m["role"] for m in msgs] == ["system", "user"]
    assert msgs[1]["content"] == ("# aiwolf_0001\n## Day 0\n### Talk\n#### Turn 1 of 4\n"
                                  f"- **{a}**: Good morning.\n- **{b}**: Skip\n- **{me}**:")
    assert llm.calls[0][1] == 1024  # multi_talk ceiling
    # second TALK of the day -> turn 2; the diff brings our own utterance back (shown once, in the transcript)
    mine = talk(2, 0, 1, me, "I think we should all share what we know.")
    ag.handle_dict(pkt("TALK", info(ctx, 3, 0), talks=[mine, talk(3, 0, 1, ctx.speaking_order_names[3], "Over", over=True)]))
    user2 = llm.calls[1][0][-1]["content"]
    assert user2.endswith(f"- **{me}**: I think we should all share what we know.\n"
                          f"- **{ctx.speaking_order_names[3]}**: Over\n#### Turn 2 of 4\n- **{me}**:")
    assert user2.count("I think we should all share") == 1
    # the same packet again (a repeated diff) changes nothing
    ag.absorb_talks(type("P", (), {"talk_history": [type("T", (), dict(day=0, idx=2, turn=1, agent=me,
                     text="dup", skip=False, over=False))()]})())
    assert ag.view.render().count("dup") == 0


def test_aiwolf_day1_morning_has_only_the_seers_divination(tmp_path):
    llm = ScriptedLLM(["Kenji", "Mizuki"])  # DIVINE, then VOTE (a living candidate: invalid replies leave no line)
    ctx, ag = make(AIWOLF, 3, llm, tmp_path)  # seat 3 = Benjamin, SEER in aiwolf_0001
    me = ctx.name_of_seat(3)
    assert ctx.role_of_seat(3) == "SEER"
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DIVINE", info(ctx, 3, 0)))  # provisional own line
    assert ag.view.render().endswith("### Action\n- divine: Benjamin -> Kenji")
    dead = ctx.names[0]
    status = {n: ("DEAD" if n == dead else "ALIVE") for n in ctx.names}
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(
        ctx, 3, 1, status=status, executed_agent=dead, attacked_agent=None,
        divine_result={"day": 0, "agent": me, "target": ctx.names[1], "result": "HUMAN"}),
        talks=[talk(5, 0, 2, ctx.names[4], "Over", over=True)]))
    # night 0 had no vote and no attack: nothing about them (the packet's executed_agent is ignored on purpose)
    assert ag.view.render() == ("# aiwolf_0001\n## Day 0\n### Talk\n#### Turn 2 of 4\n"
                                f"- **{ctx.names[4]}**: Over\n### Action\n- divine: {me} -> {ctx.names[1]} (human)\n"
                                "## Day 1\n### Talk")
    reply = ag.handle_dict(pkt("VOTE", info(ctx, 3, 1, status=status)))
    assert reply == "Mizuki"
    user = llm.calls[1][0][-1]["content"]
    living = [n for n in ctx.names if n != dead]
    assert user == (rules_context(ctx)["vote_request_sentence"] + "\nCandidates: " + ", ".join(living)
                    + "\n\n" + ag.view.render().rsplit("\n### Vote", 1)[0] + f"\n### Vote\n- {me} ->")
    assert ag.view.render().endswith(f"### Vote\n- {me} -> Mizuki")  # provisional own vote
    assert llm.calls[1][1] == 64  # multi_vote


def test_aiwolf_day2_morning_votes_execution_attack(tmp_path):
    ctx, ag = make(AIWOLF, 1, ScriptedLLM([]), tmp_path)  # seat 1 = Possessed (not the Seer, not the Wolf)
    n = ctx.names
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 1, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 1)))
    assert ag.view.render() == "# aiwolf_0001\n## Day 0\n### Talk\n## Day 1\n### Talk"  # nothing for a non-Seer
    votes = [{"day": 1, "agent": n[0], "target": n[2]}, {"day": 1, "agent": n[1], "target": n[3]},
             {"day": 1, "agent": n[2], "target": n[2]}, {"day": 1, "agent": n[4], "target": n[2]}]
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 2, executed_agent=n[2], attacked_agent=n[3], vote_list=votes)))
    assert ag.view.render().endswith(
        f"## Day 1\n### Talk\n### Vote\n- {n[0]} -> {n[2]}\n- {n[1]} -> {n[3]}\n- {n[2]} -> {n[2]}\n- {n[4]} -> {n[2]}\n"
        f"- execution: {n[2]}\n### Action\n- attacked: {n[3]}\n## Day 2\n### Talk")
    # a failed attack and no valid votes: the expected lines say so
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 3, executed_agent=None, attacked_agent=None, vote_list=[])))
    assert ag.view.render().endswith("## Day 2\n### Talk\n### Vote\n- execution: no one\n### Action\n- attacked: no one\n## Day 3\n### Talk")


def test_werewolf_sees_its_own_attack_line(tmp_path):
    ctx, ag = make(AIWOLF, 4, ScriptedLLM(["Minako"]), tmp_path)  # seat 4 = Shizue, WEREWOLF
    assert ctx.role_of_seat(4) == "WEREWOLF"
    me = ctx.name_of_seat(4)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 4, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 4, 1)))
    ag.handle_dict(pkt("ATTACK", info(ctx, 4, 1)))
    assert ag.view.render().endswith(f"## Day 1\n### Talk\n### Action\n- attack: {me} -> Minako")
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 4, 2, executed_agent=ctx.names[0], attacked_agent="Minako")))
    assert ag.view.render().endswith(f"- execution: {ctx.names[0]}\n### Action\n- attack: {me} -> Minako\n## Day 2\n### Talk")


def test_wire_reply_is_raw(tmp_path):
    """The server normalises and keeps ``raw`` itself: the agent must send the LLM text unmodified."""
    llm = ScriptedLLM(["  Hello there.\n", "\nover.\n", " Kenji "])
    ctx, ag = make(AIWOLF, 3, llm, tmp_path)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 3, 0)))
    assert ag.handle_dict(pkt("TALK", info(ctx, 3, 0))) == "  Hello there.\n"
    assert ag.handle_dict(pkt("TALK", info(ctx, 3, 0))) == "\nover.\n"
    assert ag.handle_dict(pkt("VOTE", info(ctx, 3, 1))) == " Kenji "
    assert [r["response"] for r in ag.records] == ["  Hello there.\n", "\nover.\n", " Kenji "]
    assert all(r["ts"].endswith("+00:00") for r in ag.records)


def test_aiwolf_divine_lists_living_others(tmp_path):
    llm = ScriptedLLM(["Kenji"])
    ctx, ag = make(AIWOLF, 3, llm, tmp_path)
    me = ctx.name_of_seat(3)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 3, 0)))
    ag.handle_dict(pkt("DIVINE", info(ctx, 3, 0)))
    user = llm.calls[0][0][-1]["content"]
    others = [n for n in ctx.names if n != me]
    head = rules_context(ctx)["action_request_sentences"]["DIVINE"] + "\n" + "\n".join(f"- {n}" for n in others)
    assert user == head + "\n\n# aiwolf_0001\n## Day 0\n### Talk\n### Action\n- divine: " + me + " ->"
    assert llm.calls[0][1] == 64  # multi_action


def test_investigate_lists_titles_and_round_sections(tmp_path):
    llm = ScriptedLLM([f"{TITLES[0]}; {TITLES[3]}", "B"])
    ctx, ag = make(LIVING, 2, llm, tmp_path)
    me = ctx.name_of_seat(2)
    rc = rules_context(ctx)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 2, 1, problem=ctx.problem_of_seat(2), card_titles=TITLES)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 1)))
    reply = ag.handle_dict(pkt("INVESTIGATE", info(ctx, 2, 1)))
    assert reply == f"{TITLES[0]}; {TITLES[3]}"
    user = llm.calls[0][0][-1]["content"]
    assert user == (rc["action_request_sentences"]["INVESTIGATE"] + "\n" + "\n".join(f"- {t}" for t in TITLES)
                    + f"\n\n# shared_living_0001\n## Round 1\n### Talk\n### Action\n- investigate: {me} ->")
    assert ag.view.render().endswith(f"- investigate: {me} -> {TITLES[0]}; {TITLES[3]}")  # provisional
    # round 2: findings (and the investigation line as the server resolved it)
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 2, investigate_result=[
        {"card_id": "card_01", "title": TITLES[0], "text": "It cost 90,000 yen."},
        {"card_id": "card_04", "title": TITLES[3], "text": "Sleeps 30."}])))
    assert ag.view.render() == ("# shared_living_0001\n## Round 1\n### Talk\n### Action\n"
                                f"- investigate: {me} -> {TITLES[0]}; {TITLES[3]}\n"
                                f"## Round 2\n### Findings\n- {TITLES[0]}: It cost 90,000 yen.\n- {TITLES[3]}: Sleeps 30.\n### Talk")
    # round 3: options
    opts = [{"label": "A", "name": "Lake Lodge", "summary": "Cheap and near."},
            {"label": "B", "name": "Mountain Hut", "summary": "Far but roomy."}]
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 3, options=opts)))
    assert ag.view.render().endswith("## Round 3\n### Options\n- A: Lake Lodge. Cheap and near.\n- B: Mountain Hut. Far but roomy.\n### Talk")
    reply = ag.handle_dict(pkt("VOTE", info(ctx, 2, 3)))
    assert reply == "B"
    assert llm.calls[1][0][-1]["content"].startswith(rc["vote_request_sentence"] + "\nCandidates: A, B\n\n")
    assert llm.calls[1][0][-1]["content"].endswith(f"### Talk\n### Vote\n- {me} ->")


def test_candidate_selection_uses_candidate_noun(tmp_path):
    ctx, ag = make(PANEL, 1, ScriptedLLM([]), tmp_path)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 1, 1, card_titles=TITLES)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 3, options=[
        {"label": "A", "name": "X", "summary": "s."}])))
    assert "\n## Round 3\n### Options\n- A: X. s.\n### Talk" in ag.view.render()
    assert "candidate" in rules_context(ctx)["vote_request_sentence"]


def test_no_findings_when_nothing_was_looked_into(tmp_path):
    ctx, ag = make(LIVING, 2, ScriptedLLM([]), tmp_path)
    me = ctx.name_of_seat(2)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 2, 1, problem=ctx.problem_of_seat(2), card_titles=TITLES)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 2, investigate_result=[])))
    assert ag.view.render() == f"# shared_living_0001\n## Round 1\n### Talk\n### Action\n- investigate: {me} -> none\n## Round 2\n### Talk"


def test_llm_exception_on_talk_yields_forceskip_and_empty_for_vote_action(tmp_path):
    llm = FailingLLM()
    ctx, ag = make(AIWOLF, 1, llm, tmp_path)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 1, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 1, 0)))
    assert ag.handle_dict(pkt("TALK", info(ctx, 1, 0))) == T_FORCE_SKIP
    assert ag.handle_dict(pkt("VOTE", info(ctx, 1, 1))) == ""
    assert ag.handle_dict(pkt("ATTACK", info(ctx, 1, 1))) == ""
    assert llm.calls == 3
    recs = list(read_jsonl(ag.raw_jsonl_path()))
    assert [r["request"] for r in recs] == ["TALK", "VOTE", "ATTACK"]
    assert all(r["error"].startswith("RuntimeError: endpoint down") for r in recs)
    assert all(r["response"] is None for r in recs)


def test_jsonl_records_have_required_fields(tmp_path):
    llm = ScriptedLLM(["Hello all.", "x"])
    ctx, ag = make(AIWOLF, 5, llm, tmp_path)
    gid = "aiwolf_0001__multi-private__fake__20261027T000000"
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 5, 0, game_id=gid)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 5, 0, game_id=gid)))
    ag.handle_dict(pkt("TALK", info(ctx, 5, 0, game_id=gid), talks=[talk(0, 0, 1, ctx.names[0], "yo")]))
    ag.handle_dict(pkt("VOTE", info(ctx, 5, 1, game_id=gid)))
    path = tmp_path / "aiwolf" / "multi-private" / gid / "raw" / "agent.5.jsonl"
    assert ag.raw_jsonl_path() == path and path.exists()
    recs = list(read_jsonl(path))
    assert len(recs) == 2
    for r in recs:
        assert r["kind"] == "llm_call"
        for f in LLM_CALL_FIELDS:
            assert f in r, f
    assert [r["seq"] for r in recs] == [1, 2]
    assert recs[0]["seat"] == 5 and recs[0]["request"] == "TALK" and recs[0]["round"] == 0 and recs[0]["turn"] == 1
    assert recs[1]["request"] == "VOTE" and recs[1]["round"] == 1 and recs[1]["turn"] is None
    assert recs[0]["response"] == "Hello all." and recs[0]["error"] is None and recs[0]["truncated"] is False
    assert recs[0]["finish_reason"] == "stop" and recs[0]["usage"]["total_tokens"] == 13
    assert isinstance(recs[0]["latency_ms"], int)
    msgs = recs[0]["messages"]
    assert [m["role"] for m in msgs] == ["system", "user"]  # always rebuilt: no growing chat history
    assert msgs[0]["content"] == build_system_prompt(ctx, 5)
    assert msgs[1]["content"] == f"# aiwolf_0001\n## Day 0\n### Talk\n#### Turn 1 of 4\n- **{ctx.names[0]}**: yo\n- **{ctx.name_of_seat(5)}**:"
    assert [m["role"] for m in recs[1]["messages"]] == ["system", "user"]
    assert ag.records == recs  # pure-python records mirror the file


def test_persona_mismatch_is_rejected(tmp_path):
    ctx, ag = make(AIWOLF, 1, FakeLLM(), tmp_path)
    bad = info(ctx, 1, 0)
    bad["agent"] = ctx.name_of_seat(2)
    with pytest.raises(ValueError):
        ag.handle_dict(pkt("INITIALIZE", bad))


def test_fake_llm_canned_replies(tmp_path):
    ctx, ag = make(AIWOLF, 2, FakeLLM(), tmp_path)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 2, 0)))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 0)))
    t = ag.handle_dict(pkt("TALK", info(ctx, 2, 0)))
    assert t and t not in ("Skip", "Over")
    assert ag.handle_dict(pkt("VOTE", info(ctx, 2, 1))) == ctx.names[0]
    assert ag.handle_dict(pkt("ATTACK", info(ctx, 2, 1))) == next(n for n in ctx.names if n != ctx.name_of_seat(2))
    ctx2, ag2 = make(LIVING, 3, FakeLLM(), tmp_path)
    ag2.handle_dict(pkt("INITIALIZE", info(ctx2, 3, 1, card_titles=TITLES)))
    assert ag2.handle_dict(pkt("INVESTIGATE", info(ctx2, 3, 1))) == f"{TITLES[0]}; {TITLES[1]}"


def test_dump_prompts_contains_system_and_talk(capsys):
    ctx = GameContext.load(AIWOLF)
    out = dump_prompts(ctx, 3)
    assert build_system_prompt(ctx, 3) in out
    assert "#### Turn 1 of 4" in out and out.endswith(f"- **{ctx.name_of_seat(3)}**:")
    assert "no name labels, headings, stage directions or commentary" in out


def test_dump_prompts_checks_dynamic_titles():
    """Same gate as a real run: dynamic mode with empty card titles is an error, not empty bullets."""
    ctx = GameContext.load(LIVING)
    for c in ctx.instance["card_pool"]:
        c["title"] = ""  # the pre-§9-9 state
    with pytest.raises(ValueError, match="needs card titles"):
        dump_prompts(ctx, 1)
    ctx.setup.info_mode = "fixed"
    assert "=== system" in dump_prompts(ctx, 1)


def test_discussion_round2_findings_without_titles(tmp_path):
    ctx, ag = make(LIVING, 2, ScriptedLLM([]), tmp_path)
    ctx.setup.info_mode = "fixed"
    me = ctx.name_of_seat(2)
    ag.handle_dict(pkt("INITIALIZE", info(ctx, 2, 1, problem=ctx.problem_of_seat(2))))
    ag.handle_dict(pkt("DAILY_INITIALIZE", info(ctx, 2, 2, investigate_result=[
        {"card_id": "card_01", "title": "", "text": "It cost 90,000 yen."},
        {"card_id": "card_04", "title": "Lodge capacity", "text": "Sleeps 30."}])))
    assert ag.view.render() == (f"# shared_living_0001\n## Round 1\n### Talk\n### Action\n- investigate: {me} -> Lodge capacity\n"
                                "## Round 2\n### Findings\n- It cost 90,000 yen.\n- Lodge capacity: Sleeps 30.\n### Talk")


# ---- websocket round trip --------------------------------------------------------------------------
def test_run_client_replays_packets_over_websocket(tmp_path):
    websockets = pytest.importorskip("websockets.sync.server")
    ctx = GameContext.load(AIWOLF)
    seat = 3
    gid = "aiwolf_0001__multi-private__fake__20261027T000001"
    script = [
        pkt("NAME"),
        pkt("INITIALIZE", info(ctx, seat, 0, game_id=gid), setting={}),
        pkt("DAILY_INITIALIZE", info(ctx, seat, 0, game_id=gid)),
        pkt("TALK", info(ctx, seat, 0, game_id=gid), talks=[talk(0, 0, 1, ctx.names[0], "hello")]),
        pkt("TALK", info(ctx, seat, 0, game_id=gid), talks=[]),
        pkt("DIVINE", info(ctx, seat, 0, game_id=gid)),
        pkt("DAILY_FINISH", info(ctx, seat, 0, game_id=gid)),
        pkt("DAILY_INITIALIZE", info(ctx, seat, 1, game_id=gid, attacked_agent=ctx.names[4])),
        pkt("VOTE", info(ctx, seat, 1, game_id=gid)),
        pkt("FINISH", info(ctx, seat, 1, game_id=gid)),
    ]
    replies: list[str] = []

    def handler(conn):
        for p in script:
            conn.send(json.dumps(p))
            replies.append(conn.recv())
        conn.close()

    server = websockets.serve(handler, "127.0.0.1", 0)
    port = server.socket.getsockname()[1]
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        ag = make_agent(ctx, seat, FakeLLM(), tmp_path)
        rc = run_client(f"ws://127.0.0.1:{port}", ag, connect_timeout=10)
    finally:
        server.shutdown()
    assert rc == 0
    assert replies[0] == "seat3"
    assert replies[1] == ACK and replies[2] == ACK and replies[6] == ACK and replies[7] == ACK and replies[9] == ACK
    assert replies[3] not in ("", "Skip", "Over")
    assert replies[5] in ctx.names and replies[5] != ctx.name_of_seat(seat)
    assert replies[8] in ctx.names
    recs = list(read_jsonl(tmp_path / "aiwolf" / "multi-private" / gid / "raw" / "agent.3.jsonl"))
    assert [r["request"] for r in recs] == ["TALK", "TALK", "DIVINE", "VOTE"]
    assert [r["turn"] for r in recs] == [1, 2, None, None]
