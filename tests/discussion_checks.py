"""Checks shared by the candidate_selection and shared_living server tests."""
from __future__ import annotations

from conftest import make_ctx, play
from log_checks import check_all_common, rounds_played, status_of_round

from common.tiebreak import choose, tally


def investigate_rows(run):
    rows = [r for r in run.rows if r.type == "action"]
    assert all(r.extra["action"] == "investigate" for r in rows)
    assert all(r.round == 1 and r.target == "" for r in rows)
    assert sorted(r.agent for r in rows) == sorted(run.ctx.names)
    return {r.agent: r for r in rows}


def check_discussion_common(run) -> None:
    check_all_common(run, "vote_final")
    rows, ctx = run.rows, run.ctx
    assert not run.game.aborted
    assert rounds_played(rows) == [1, 2, 3]
    for rnd in (1, 2, 3, 4):
        assert all(status_of_round(rows, rnd).values())
    # votes only after round 3; result row from the tally
    votes = [r for r in rows if r.type == "vote"]
    assert votes and all(r.round == 3 for r in votes)
    t = tally({r.agent: (r.target or None) for r in votes}, ctx.setup.setup_id, 3)
    res = rows[-1]
    assert res.type == "result" and res.round == 3 and res.agent == "" and res.target == ""
    assert res.text == t.chosen and res.extra["adopted"] == t.chosen
    assert res.extra["tally"] == t.counts and res.extra["tie"] == t.tie
    assert t.chosen in ctx.option_labels()
    assert all(r.extra["tie"] == t.tie for r in votes)
    assert run.game.outcome == {"adopted": t.chosen, "tally": t.counts, "tie": t.tie}
    # information schedule as seen by the agents
    for a in run.agents:
        assert a.role == "PARTICIPANT"
        assert a.problem == ctx.problem_of_seat(a.seat)
        assert a.problem and "Concern" not in a.profile  # the seed travels in info.problem only
        assert a.options_seen_at == [3], "options must be revealed exactly at round 3 start"
        assert a.options == ctx.options()
        assert list(a.investigate_results) == [2], "findings arrive at round 2 start only"
        assert a.finish_info["options"] == ctx.options() and a.finish_info["adopted"] == t.chosen
        assert "executed_agent" not in a.finish_info
        days = [d for r, d in a.requests if r == "DAILY_INITIALIZE"]
        assert days == [1, 2, 3]
    inv = investigate_rows(run)
    for a in run.agents:
        got = a.investigate_results[2]
        assert [c["card_id"] for c in got] == inv[a.name].extra["cards"]
        for c in got:
            assert set(c) == {"card_id", "title", "text"} and c["text"] == ctx.card_by_id(c["card_id"])["text"]
    h = run.header
    assert h["n_options"] == len(ctx.options())
    assert [c["card_id"] for c in h["card_pool"]] == [c["card_id"] for c in ctx.card_pool()]
    assert set(h["card_pool"][0]) == {"card_id", "title", "origin_seat"}
    assert h["n_unique_cards"] == len({cid for r in inv.values() for cid in r.extra["cards"]})
    assert h["participants"][0]["private_seed"] == ctx.problem_of_seat(1)


def run_fixed(setup_id: str, log_dir):
    """info_mode=fixed must work on the real data (card titles still empty)."""
    ctx = make_ctx(setup_id, info_mode="fixed")
    run = play(ctx, log_dir)
    check_discussion_common(run)
    inv = investigate_rows(run)
    for seat in range(1, 6):
        r = inv[ctx.name_of_seat(seat)]
        assert r.extra["parse"] == "fixed"
        assert r.extra["cards"] == ctx.instance["fixed_assignment"][str(seat)]
        assert r.text == "; ".join(c["title"] or c["card_id"] for c in ctx.fixed_cards_of_seat(seat))
    for a in run.agents:
        assert a.card_titles == []
        assert "INVESTIGATE" not in [r for r, _ in a.requests]
    assert run.header["info_mode"] == "fixed" and run.header["n_unique_cards"] == 10
    return run


def run_dynamic(setup_id: str, log_dir):
    """info_mode=dynamic with titles patched into a copy of the instance; exercises the parser."""
    ctx = make_ctx(setup_id, titles=True)
    titles = [c["title"] for c in ctx.card_pool()]

    def numbered_three(agent, info):  # 3 titles, numbered and quoted -> first 2 adopted
        return f'1. "{titles[4]}"\n2) {titles[3].upper()}.\n3. {titles[0]}'

    def one_title(agent, info):  # partial
        return titles[9]

    def garbage(agent, info):  # fail
        return "I would like to look into everything."

    def same_line(agent, info):  # ';' separator
        return f"{titles[2]}; {titles[1]}"

    per_seat = {2: {"investigate": same_line}, 3: {"investigate": numbered_three},
                4: {"investigate": one_title}, 5: {"investigate": garbage}}
    run = play(ctx, log_dir, per_seat=per_seat)
    check_discussion_common(run)
    ids = [c["card_id"] for c in ctx.card_pool()]
    inv = investigate_rows(run)
    n = ctx.name_of_seat
    assert inv[n(1)].extra == {"action": "investigate", "cards": ids[:2], "parse": "ok"}
    assert inv[n(1)].text == f"{titles[0]}; {titles[1]}"
    assert inv[n(2)].extra["cards"] == [ids[2], ids[1]] and inv[n(2)].extra["parse"] == "ok"
    assert inv[n(3)].extra["cards"] == [ids[4], ids[3]] and inv[n(3)].extra["parse"] == "ok"
    assert inv[n(3)].text == f"{titles[4]}; {titles[3]}"
    assert inv[n(4)].extra["cards"] == [ids[9]] and inv[n(4)].extra["parse"] == "partial"
    assert inv[n(5)].extra["cards"] == [] and inv[n(5)].extra["parse"] == "fail" and inv[n(5)].text == ""
    for a in run.agents:
        assert a.card_titles == titles
        assert [r for r, _ in a.requests].count("INVESTIGATE") == 1
    assert run.agent(5).investigate_results[2] == []
    assert run.header["n_unique_cards"] == 6
    return run


def run_tie(setup_id: str, log_dir):
    """A,A,B,B,C -> tie between A and B resolved by common.tiebreak.choose(setup_id, round 3)."""
    ctx = make_ctx(setup_id, info_mode="fixed")
    labels = ctx.option_labels()
    assert len(labels) >= 3
    plan = {1: labels[0], 2: labels[0], 3: labels[1], 4: labels[1], 5: labels[2]}

    def planned(agent, info):
        return plan[agent.seat]

    run = play(ctx, log_dir, per_seat={s: {"vote": planned} for s in plan})
    check_discussion_common(run)
    res = run.rows[-1]
    assert res.extra["tie"] is True
    assert res.text == choose([labels[0], labels[1]], ctx.setup.setup_id, 3)
    assert res.extra["tally"] == {labels[0]: 2, labels[1]: 2, labels[2]: 1}
    return run


def run_invalid_vote(setup_id: str, log_dir):
    ctx = make_ctx(setup_id, info_mode="fixed")
    labels = ctx.option_labels()
    forms = {1: f"Option {labels[1]}", 2: f"candidate {labels[1].lower()}.", 3: ctx.options()[1]["name"],
             4: "Z", 5: ""}
    run = play(ctx, log_dir, per_seat={s: {"vote": (lambda a, i, s=s: forms[s])} for s in forms})
    check_discussion_common(run)
    v = {r.agent: r for r in run.rows if r.type == "vote"}
    n = ctx.name_of_seat
    for s in (1, 2, 3):
        assert v[n(s)].target == labels[1] and v[n(s)].extra["valid"] is True
    for s in (4, 5):
        assert v[n(s)].target == "" and v[n(s)].extra["valid"] is False and v[n(s)].extra["raw"] == forms[s]
    assert run.rows[-1].text == labels[1] and run.rows[-1].extra["tally"] == {labels[1]: 3}
    return run
