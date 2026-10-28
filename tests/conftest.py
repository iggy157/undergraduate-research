"""Shared harness: run the server in a thread on a free port with five scripted agents."""
from __future__ import annotations

import asyncio
import copy
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripted_agent import ScriptedAgent, run_seats_in_threads

from common.logwriter import read_jsonl, read_log
from common.schema import LogRow
from common.setup import GameContext, load_setup
from server.base.runner import run_game


@dataclass
class GameRun:
    game: Any
    rows: list[LogRow]
    records: list[dict[str, Any]]
    agents: list[ScriptedAgent]
    ctx: GameContext
    server_error: BaseException | None = None

    @property
    def header(self) -> dict[str, Any]:
        hs = [r for r in self.records if r.get("kind") == "header"]
        assert len(hs) == 1, "exactly one header record expected"
        return hs[0]

    def of_type(self, typ: str) -> list[LogRow]:
        return [r for r in self.rows if r.type == typ]

    def agent(self, seat: int) -> ScriptedAgent:
        return self.agents[seat - 1]

    def by_name(self, name: str) -> ScriptedAgent:
        return next(a for a in self.agents if a.name == name)


def make_ctx(setup_id: str, info_mode: str | None = None, titles: bool = False) -> GameContext:
    """Load a setup; optionally force info_mode and give the (currently empty) card titles a value."""
    s = load_setup(setup_id)
    if info_mode:
        s.info_mode = info_mode
    ctx = GameContext.load(s)
    if titles and ctx.instance is not None:
        ctx.instance = copy.deepcopy(ctx.instance)
        for i, c in enumerate(ctx.instance["card_pool"], 1):
            c["title"] = f"Card {i}: finding number {i}"
    return ctx


def play(ctx: GameContext, log_dir: Path, per_seat: dict[int, dict[str, Any]] | None = None,
         timeout: float = 5.0, model_tag: str = "scripted", agent_log_dir: bool = True,
         game_id: str | None = None) -> GameRun:
    port_ev = threading.Event()
    box: dict[str, Any] = {}

    def on_listening(port: int) -> None:
        box["port"] = port
        port_ev.set()

    def server_main() -> None:
        try:
            box["game"] = asyncio.run(run_game(ctx, 0, log_dir, timeout=timeout, model_tag=model_tag,
                                               on_listening=on_listening, game_id=game_id,
                                               connect_timeout=20))
        except BaseException as e:  # surfaced to the test
            box["error"] = e
        finally:
            port_ev.set()

    th = threading.Thread(target=server_main, name="server", daemon=True)
    th.start()
    assert port_ev.wait(10), "server did not start"
    if "error" in box:
        raise box["error"]
    url = f"ws://127.0.0.1:{box['port']}"
    agents = run_seats_in_threads(url, per_seat, log_dir=(log_dir if agent_log_dir else None))
    th.join(60)
    assert not th.is_alive(), "server thread still running"
    if "error" in box:
        raise box["error"]
    game = box["game"]
    rows = read_log(game.game_dir / f"{game.game_id}.log")
    records = list(read_jsonl(game.game_dir / f"{game.game_id}.jsonl"))
    return GameRun(game, rows, records, agents, ctx)


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    return tmp_path / "log"
