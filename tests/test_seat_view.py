"""The multi agent's user message is the seat view of the common log (DESIGN §7.4).

Five real SeatAgents (FakeLLM) play against the real server; afterwards every TALK call's user message
must equal ``view_from_rows(rows, ctx, seat, upto=<that talk row>)`` continued with the seat's own label,
and the writer view of the whole log must parse back through the single converter to the same rows.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest

from agent.base import FakeLLM, make_agent, run_client
from common.convert.single_markdown import convert
from common.logwriter import read_log
from common.setup import GameContext
from common.transcript import view_from_rows
from server.base.runner import run_game


def play_with_real_agents(ctx: GameContext, log_dir: Path):
    port_ev = threading.Event()
    box: dict = {}

    def on_listening(port: int) -> None:
        box["port"] = port
        port_ev.set()

    def server_main() -> None:
        try:
            box["game"] = asyncio.run(run_game(ctx, 0, log_dir, timeout=10, model_tag="fake",
                                               on_listening=on_listening, connect_timeout=20))
        except BaseException as e:  # noqa: BLE001
            box["error"] = e
        finally:
            port_ev.set()

    th = threading.Thread(target=server_main, daemon=True)
    th.start()
    assert port_ev.wait(10) and "error" not in box
    url = f"ws://127.0.0.1:{box['port']}"
    agents = [make_agent(ctx, s, FakeLLM(), log_dir) for s in range(1, 6)]
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
def test_talk_messages_equal_seat_view_of_log(setup_id, info_mode, tmp_path):
    ctx = GameContext.load(setup_id)
    ctx.setup.info_mode = info_mode
    game, rows, agents = play_with_real_agents(ctx, tmp_path)
    assert any(r.type == "result" for r in rows)
    checked = 0
    for ag in agents:
        name = ag.name
        for rec in ag.records:
            if rec["request"] != "TALK":
                continue
            row = next(r for r in rows if r.type in ("talk", "pass") and r.round == rec["round"]
                       and r.turn == rec["turn"] and r.agent == name)
            expected = (view_from_rows(rows, ctx, ag.seat, upto_seq=row.seq, ensure_turn=(row.round, row.turn)).render()
                        + f"\n- **{name}**:")
            assert rec["messages"][1]["content"] == expected, (name, rec["round"], rec["turn"])
            assert rec["messages"][0]["content"] == ag.system_prompt
            checked += 1
    assert checked >= 20
    # the writer view round-trips through the single converter
    writer = view_from_rows(rows, ctx, None).render()
    res = convert(writer, ctx, "roundtrip")
    assert not [v for v in res.violations if v["code"] not in ("format_noise",)], res.violations
    sig = lambda rs: [(r.round, r.turn, r.type, r.agent, r.target, r.text) for r in rs if r.type != "status"]  # noqa: E731
    assert sig(res.rows) == sig(rows)
