"""Assertions on a finished game's common log, shared by the per-domain server tests."""
from __future__ import annotations

from collections import Counter

from common.schema import ROW_TYPES, LogRow
from common.violations import find_truncations, find_violations

HEADER_FIELDS = ("game_id", "setup_id", "domain", "method", "model", "model_tag", "info_mode", "setup_path",
                 "setup_sha1", "started_at", "finished_at", "participants", "speaking_order", "card_pool",
                 "n_options", "n_unique_cards", "outcome", "rules_hash")
_PHASE = {"TALK": 0, "VOTE": 1, "DIVINE": 2, "INVESTIGATE": 2, "ATTACK": 3}


def rounds_played(rows: list[LogRow]) -> list[int]:
    return sorted({r.round for r in rows if r.type in ("talk", "pass")})


def status_of_round(rows: list[LogRow], rnd: int) -> dict[str, bool]:
    st = [r for r in rows if r.type == "status" and r.round == rnd]
    assert len(st) == 5, f"round {rnd}: expected 5 status rows, got {len(st)}"
    assert {r.extra["seat"] for r in st} == set(range(1, 6))
    for r in st:
        assert set(r.extra) == {"seat", "role", "alive"}
        assert r.text == ("ALIVE" if r.extra["alive"] else "DEAD")
    return {r.agent: bool(r.extra["alive"]) for r in st}


def check_rows_basic(run) -> None:
    rows = run.rows
    assert rows, "empty log"
    assert [r.seq for r in rows] == list(range(len(rows))), "seq must be 0..n-1 in file order"
    assert all(r.type in ROW_TYPES for r in rows)
    names = set(run.ctx.names)
    for r in rows:
        assert r.agent == "" or r.agent in names, r
        if r.type in ("talk", "pass"):
            assert r.turn is not None and 1 <= r.turn <= 4, r
        else:
            assert r.turn is None, r
    # status rows at every round start, before any talk of that round
    for rnd in rounds_played(rows):
        st = [r for r in rows if r.type == "status" and r.round == rnd]
        first_talk = next(r for r in rows if r.type in ("talk", "pass") and r.round == rnd)
        assert len(st) == 5 and all(r.seq < first_talk.seq for r in st), f"round {rnd} status rows"
    # status rows before FINISH (round = last played + 1), then the result row last
    assert rows[-1].type == "result", "result row must be the last row"
    last = rounds_played(rows)[-1]
    final_status = [r for r in rows if r.type == "status" and r.round == last + 1]
    assert len(final_status) == 5, "5 status rows expected right before FINISH"
    assert all(r.seq > max(x.seq for x in rows if x.type in ("talk", "pass", "vote", "action"))
               for r in final_status)
    assert sum(1 for r in rows if r.type == "result") == 1
    # talk extras
    for r in rows:
        if r.type == "talk":
            assert set(r.extra) >= {"words", "mentions", "raw_differs"}
            assert r.text == r.text.strip() and r.text
            assert r.extra["words"] == len(r.text.split())
        elif r.type == "pass":
            assert r.text in ("Skip", "Over")
            assert set(r.extra) >= {"forced", "empty"}


def check_turns(run) -> None:
    """Fixed speaking order, <= 4 turns, each living non-Over seat exactly once per turn."""
    rows = run.rows
    order = run.ctx.speaking_order_names
    for rnd in rounds_played(rows):
        alive = status_of_round(rows, rnd)
        over: set[str] = set()
        for turn in range(1, 5):
            trs = [r for r in rows if r.type in ("talk", "pass") and r.round == rnd and r.turn == turn]
            expected = [n for n in order if alive[n] and n not in over]
            assert [r.agent for r in trs] == expected, (rnd, turn, [r.agent for r in trs], expected)
            for r in trs:
                if r.type == "pass" and r.text == "Over":
                    over.add(r.agent)
        assert not [r for r in rows if r.type in ("talk", "pass") and r.round == rnd and r.turn > 4]


def check_votes(run, request: str) -> list[int]:
    """Every living seat votes exactly once in each vote round; invalid votes have target ''."""
    rows = run.rows
    vote_rounds = sorted({r.round for r in rows if r.type == "vote"})
    for rnd in vote_rounds:
        alive = status_of_round(rows, rnd)
        vrs = [r for r in rows if r.type == "vote" and r.round == rnd]
        assert sorted(r.agent for r in vrs) == sorted(n for n, a in alive.items() if a)
        for r in vrs:
            assert set(r.extra) >= {"request", "raw", "valid", "tie"}
            assert r.extra["request"] == request
            assert r.text == ""
            if r.extra["valid"]:
                assert r.target != ""
            else:
                assert r.target == ""
        assert len({r.extra["tie"] for r in vrs}) == 1
    return vote_rounds


def check_talk_delivery(run) -> None:
    """Each agent receives every talk (Skip/Over included) exactly once through talk_history diffs."""
    talk_rows = [r for r in run.rows if r.type in ("talk", "pass")]
    expected = Counter((r.round, r.turn, r.agent) for r in talk_rows)
    for a in run.agents:
        got = Counter((t.day, t.turn, t.agent) for t in a.received_talks)
        assert got == expected, f"seat {a.seat} ({a.name}) talk diffs do not add up to the log"
        keys = [(t.day, t.idx) for t in a.received_talks]
        assert len(keys) == len(set(keys)), "duplicate (day, idx) in a seat's talk_history"
        for t in a.received_talks:
            if t.skip or t.over:
                assert t.text in ("Skip", "Over")
                assert t.skip != t.over


def check_agents_common(run) -> None:
    ctx = run.ctx
    for a in run.agents:
        assert a.error is None, f"seat {a.seat}: {a.error!r}"
        assert a.name == ctx.name_of_seat(a.seat)
        assert a.game_id == run.game.game_id
        assert a.profile and a.profile.startswith(f"Name: {a.name}\nAge: ")
        assert a.profile.count("\n") == 3, a.profile  # Name / Age / Gender / Personality, no private seed
        assert "Role:" not in a.profile and "Concern:" not in a.profile
        reqs = [r for r, _ in a.requests]
        assert reqs[0] == "INITIALIZE" and reqs[-1] == "FINISH"
        assert a.setting is not None and a.setting.agent_count == 5
        assert a.finish_info is not None and a.finish_info["game_id"] == run.game.game_id


def check_header(run) -> dict:
    h = run.header
    assert set(HEADER_FIELDS) <= set(h), sorted(set(HEADER_FIELDS) - set(h))
    ctx = run.ctx
    assert h["game_id"] == run.game.game_id
    assert h["setup_id"] == ctx.setup.setup_id and h["domain"] == ctx.domain and h["method"] == "multi"
    assert h["model"] == "scripted" and h["info_mode"] == ctx.setup.info_mode
    assert h["speaking_order"] == ctx.setup.speaking_order
    assert len(h["participants"]) == 5
    for p in h["participants"]:
        assert set(p) == {"seat", "name", "role_slot", "persona", "private_seed"}
        assert set(p["persona"]) == {"name", "age", "gender", "personality"}
        assert p["name"] == ctx.name_of_seat(p["seat"]) and p["role_slot"] == ctx.role_of_seat(p["seat"])
    assert len(h["rules_hash"]) == 40 and len(h["setup_sha1"]) == 40
    assert h["setup_path"] == f"setups/{ctx.domain}/{ctx.setup.setup_id}.json"
    assert h["started_at"] <= h["finished_at"] and h["started_at"].endswith("+00:00")
    assert h["outcome"] == run.game.outcome
    assert run.records[0]["kind"] == "header"
    return h


def check_llm_merge(run) -> None:
    calls = [r for r in run.records if r["kind"] == "llm_call"]
    assert calls, "merged llm_call records expected (scripted agents write raw/agent.<seat>.jsonl)"
    # global seq 0..n-1 in chronological order; the agent's own counter survives as seat_seq
    assert [c["seq"] for c in calls] == list(range(len(calls)))
    keys = [(c["round"], _PHASE[c["request"]], c["turn"] or 0) for c in calls]
    assert keys == sorted(keys), "merged llm_call records are not in game order"
    for seat in range(1, 6):
        mine = [c["seat_seq"] for c in calls if c["seat"] == seat]
        assert mine == sorted(mine) and len(set(mine)) == len(mine)
    assert {c["seat"] for c in calls} == set(range(1, 6))
    n_talk = sum(1 for r in run.rows if r.type in ("talk", "pass") and not r.extra.get("timeout"))
    assert sum(1 for c in calls if c["request"] == "TALK") == n_talk


def check_violations_record(run) -> list[dict]:
    """The server writes one ``violations`` record (last) = common codes on its rows + truncations."""
    vs = [r for r in run.records if r["kind"] == "violations"]
    assert len(vs) == 1 and run.records[-1] is vs[0]
    expected = find_violations(run.rows, run.ctx) + find_truncations(run.records)
    assert vs[0]["items"] == expected
    return vs[0]["items"]


def check_all_common(run, vote_request: str) -> None:
    check_rows_basic(run)
    check_turns(run)
    check_votes(run, vote_request)
    check_talk_delivery(run)
    check_agents_common(run)
    check_header(run)
    check_llm_merge(run)
    check_violations_record(run)
