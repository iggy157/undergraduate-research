"""Server tests for the aiwolf domain (scripted agents, no LLM)."""
from __future__ import annotations

import pytest
from conftest import make_ctx, play
from log_checks import check_all_common, rounds_played, status_of_round
from scripted_agent import DISCONNECT, NO_REPLY, living

from common.protocol import Role
from common.tiebreak import tally

SETUP = "aiwolf_0001"


@pytest.fixture(scope="module")
def game(tmp_path_factory):
    return play(make_ctx(SETUP), tmp_path_factory.mktemp("log"))


def _species(ctx, name: str) -> str:
    return str(Role(ctx.role_of_name(name)).species)


def test_common_log_shape(game):
    check_all_common(game, "vote_day")
    assert not game.game.aborted
    assert rounds_played(game.rows)[0] == 0


def test_day0_has_talk_and_divine_only(game):
    rows = game.rows
    assert [r for r in rows if r.type == "talk" and r.round == 0]
    assert not [r for r in rows if r.type == "vote" and r.round == 0]
    acts = [r for r in rows if r.type == "action" and r.round == 0]
    assert [r.extra["action"] for r in acts] == ["divine"]


def test_pass_normalisation(game):
    rows = game.rows
    ctx = game.ctx
    seat2, seat3, seat4, seat5 = (ctx.name_of_seat(i) for i in (2, 3, 4, 5))
    p = {(r.agent, r.turn): r for r in rows if r.type == "pass" and r.round == 0}
    assert p[(seat2, 2)].text == "Skip" and p[(seat2, 2)].extra == {
        "forced": False, "empty": False, "raw": "skip.", "norm": [{"code": "pass_punct", "token": "Skip", "raw": "skip."}]}
    assert p[(seat4, 2)].text == "Skip" and p[(seat4, 2)].extra["forced"] is True
    assert p[(seat3, 3)].text == "Over" and p[(seat3, 3)].extra["empty"] is False
    assert p[(seat5, 3)].text == "Over" and p[(seat5, 3)].extra["empty"] is True
    # Over seats get no turn 4 that round
    assert not [r for r in rows if r.round == 0 and r.turn == 4 and r.agent in (seat3, seat5)]
    # utterances are never truncated; mentions are detected
    long = next(r for r in rows if r.type == "talk" and r.round == 0 and r.agent == ctx.name_of_seat(1) and r.turn == 4)
    assert long.extra["words"] == 60
    t1 = [r for r in rows if r.type == "talk" and r.round == 0 and r.turn == 1]
    assert all(len(r.extra["mentions"]) == 1 for r in t1)


def test_execute_divine_attack_consistency(game):
    rows, ctx = game.rows, game.ctx
    for rnd in rounds_played(rows):
        alive = status_of_round(rows, rnd)
        dead = {n for n, a in alive.items() if not a}
        # dead players never speak or vote afterwards
        assert not [r for r in rows if r.round >= rnd and r.type in ("talk", "pass", "vote") and r.agent in dead]
        votes = [r for r in rows if r.type == "vote" and r.round == rnd]
        acts = {r.extra["action"]: r for r in rows if r.type == "action" and r.round == rnd}
        if rnd >= 1:
            assert votes and "execute" in acts
            t = tally({r.agent: (r.target or None) for r in votes}, ctx.setup.setup_id, rnd)
            ex = acts["execute"]
            assert ex.agent == "" and ex.target == t.chosen and ex.text == t.chosen
            assert ex.extra["role"] == ctx.role_of_name(t.chosen) and ex.extra["tie"] == t.tie
            assert all(r.extra["tie"] == t.tie for r in votes)
            assert alive[t.chosen]
            for r in votes:
                assert r.extra["valid"] and alive[r.target]
        if "divine" in acts:
            d = acts["divine"]
            assert ctx.role_of_name(d.agent) == "SEER" and alive[d.agent]
            assert d.target != d.agent and d.extra["valid"] is True
            assert d.text == _species(ctx, d.target)
            seer = game.by_name(d.agent)
            if rnd + 1 in seer.divine_results:  # delivered next morning, to the seer only
                assert seer.divine_results[rnd + 1] == {"day": rnd, "agent": d.agent, "target": d.target, "result": d.text}
            for a in game.agents:
                if a.name != d.agent:
                    assert rnd + 1 not in a.divine_results
        if "attack" in acts:
            a = acts["attack"]
            assert rnd >= 1 and ctx.role_of_name(a.agent) == "WEREWOLF"
            assert {k: v for k, v in a.extra.items() if k != "raw"} == {"action": "attack", "success": True, "no_target": False}
            assert a.extra.get("raw")  # the reply as sent (the stepped writer may add a result after the name)
            assert a.target != a.agent and a.target != acts["execute"].target
            nxt = status_of_round(rows, rnd + 1)
            assert nxt[a.target] is False
            for ag in game.agents:
                assert ag.attacked_seen.get(rnd + 1, a.target) == a.target
        if rnd >= 1:
            nxt = status_of_round(rows, rnd + 1)
            assert nxt[acts["execute"].target] is False
            for ag in game.agents:
                assert ag.executed_seen.get(rnd + 1, acts["execute"].target) == acts["execute"].target


def test_win_condition_and_result(game):
    rows, ctx = game.rows, game.ctx
    last = rounds_played(rows)[-1]
    final = status_of_round(rows, last + 1)
    wolves = sum(1 for n, a in final.items() if a and _species(ctx, n) == "WEREWOLF")
    humans = sum(1 for n, a in final.items() if a and _species(ctx, n) == "HUMAN")
    expected = "VILLAGE" if wolves == 0 else ("WEREWOLF" if wolves >= humans else "NONE")
    res = rows[-1]
    assert res.type == "result" and res.round == last and res.agent == "" and res.target == ""
    assert res.text == expected and res.extra["winner"] == expected
    assert res.extra["villagers"] == humans and res.extra["werewolves"] == wolves
    assert res.extra.get("reason") is None
    assert game.game.outcome["winner"] == expected
    # with the default script (everyone votes for the alphabetically first living player) the
    # werewolf of aiwolf_0001 survives and wins on day 2
    assert expected == "WEREWOLF" and last == 2
    # FINISH reveals every role; INITIALIZE only one's own
    for a in game.agents:
        assert a.finish_info["role_map"] == {ctx.name_of_seat(s): ctx.role_of_seat(s) for s in range(1, 6)}
        assert a.role == ctx.role_of_seat(a.seat)
        assert set(a.finish_info["status_map"]) == set(ctx.names)
    h = game.header
    assert h["card_pool"] == [] and h["n_options"] == 0 and h["n_unique_cards"] == 0
    assert h["model"] == "scripted" and h["model_tag"] == "scripted"
    assert h["participants"][0]["private_seed"] == ctx.role_of_seat(1)


def test_daily_initialize_carries_previous_votes(game):
    """Every seat's DAILY_INITIALIZE of day d >= 2 lists the valid votes of day d-1 in seat order
    (the multi agents render them as the 'Votes:' line; the single writer sees all votes anyway)."""
    rows, ctx = game.rows, game.ctx
    for a in game.agents:
        inits = [p for p in a.packets if p["request"] == "DAILY_INITIALIZE"]
        for p in inits:
            day = p["info"]["day"]
            prev = [r for r in rows if r.type == "vote" and r.round == day - 1 and r.extra["valid"]]
            if day <= 1:
                assert "vote_list" not in p["info"]
                continue
            assert prev, day
            assert p["info"]["vote_list"] == [{"day": day - 1, "agent": r.agent, "target": r.target} for r in prev]
            assert [v["agent"] for v in p["info"]["vote_list"]] == [n for n in ctx.speaking_order_names if n in {r.agent for r in prev}]


def test_tie_break_uses_common_tiebreak(log_dir):
    """Five different votes on day 1 -> 5-way tie resolved by common.tiebreak."""
    ctx = make_ctx("aiwolf_0002")

    def split_vote(agent, info):
        return living(info)[(agent.seat - 1) % len(living(info))]

    run = play(ctx, log_dir, per_seat={s: {"vote": split_vote} for s in range(1, 6)})
    check_all_common(run, "vote_day")
    votes = [r for r in run.rows if r.type == "vote" and r.round == 1]
    assert len({r.target for r in votes}) == 5
    t = tally({r.agent: r.target for r in votes}, "aiwolf_0002", 1)
    assert t.tie
    ex = next(r for r in run.rows if r.type == "action" and r.round == 1 and r.extra["action"] == "execute")
    assert ex.target == t.chosen and ex.extra["tie"] is True
    assert all(r.extra["tie"] is True for r in votes)


def test_invalid_vote_and_invalid_actions(log_dir):
    ctx = make_ctx(SETUP)
    seer_seat = next(s for s in range(1, 6) if ctx.role_of_seat(s) == "SEER")
    wolf_seat = next(s for s in range(1, 6) if ctx.role_of_seat(s) == "WEREWOLF")
    per_seat = {
        2: {"vote": lambda agent, info: "Nobody"},
        seer_seat: {"act": lambda agent, info, req: "???"},
        wolf_seat: {"act": lambda agent, info, req: agent.name},  # self-attack is invalid
    }
    run = play(ctx, log_dir, per_seat=per_seat)
    check_all_common(run, "vote_day")
    bad = [r for r in run.rows if r.type == "vote" and r.agent == ctx.name_of_seat(2)]
    assert bad and all(r.extra["valid"] is False and r.target == "" and r.extra["raw"] == "Nobody" for r in bad)
    div = [r for r in run.rows if r.type == "action" and r.extra["action"] == "divine"]
    assert div and all(r.extra["valid"] is False and r.target == "" and r.text == "" for r in div)
    att = [r for r in run.rows if r.type == "action" and r.extra["action"] == "attack"]
    assert att and all(r.extra["no_target"] is True and r.extra["success"] is False and r.target == "" for r in att)
    # nobody dies at night, so the game is decided by executions alone
    assert not run.game.aborted


def test_talk_timeout_becomes_forced_skip(log_dir):
    ctx = make_ctx(SETUP)

    def sleepy(agent, info, turn):
        return NO_REPLY if (info.day == 0 and turn == 2) else f"{agent.name} here."

    run = play(ctx, log_dir, per_seat={1: {"talk": sleepy}}, timeout=0.5)
    check_all_common(run, "vote_day")
    r = next(r for r in run.rows if r.round == 0 and r.turn == 2 and r.agent == ctx.name_of_seat(1))
    assert r.type == "pass" and r.text == "Skip" and r.extra["forced"] is True and r.extra["timeout"] is True
    assert not run.game.aborted


def test_disconnect_aborts_with_none(log_dir):
    ctx = make_ctx(SETUP)

    def crash(agent, info, turn):
        return DISCONNECT if (info.day == 1 and turn == 2) else f"{agent.name} here."

    run = play(ctx, log_dir, per_seat={3: {"talk": crash}})
    assert run.game.aborted
    res = run.rows[-1]
    assert res.type == "result" and res.text == "NONE" and res.extra["winner"] == "NONE"
    assert res.extra["reason"] == f"disconnect:{ctx.name_of_seat(3)}"
    assert run.header["outcome"]["winner"] == "NONE"
    # status rows still precede FINISH and the other agents still get FINISH
    assert len([r for r in run.rows if r.type == "status" and r.round == 2]) == 5
    for a in run.agents:
        if a.seat != 3:
            assert a.error is None and a.finish_info is not None
