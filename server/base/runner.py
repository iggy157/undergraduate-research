"""Run one game end to end: open the lobby, wait for the five seats, play, close."""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from common.setup import GameContext

from .game import Game
from .transport import Lobby

log = logging.getLogger("server.runner")


async def run_game(ctx: GameContext, port: int, log_dir: str | Path, timeout: float = 600.0,
                   model_tag: str = "scripted", host: str = "127.0.0.1",
                   on_listening: Callable[[int], None] | None = None, game_id: str | None = None,
                   connect_timeout: float | None = None, model: str | None = None,
                   header_extra: dict[str, Any] | None = None, condition: str = "multi-private",
                   scenario: dict[str, Any] | None = None, scenario_info: dict[str, Any] | None = None) -> Game:
    """Serve on ``host:port`` (0 = any free port), wait for seat1..seat5, play the game.

    ``on_listening(port)`` is called once the socket is bound (tests use it with port 0).
    Returns the finished ``Game`` (``game.outcome``, ``game.aborted``, ``game.game_dir``).
    """
    ctx.check_dynamic_ready()
    lobby = Lobby(host, port, timeout)
    await lobby.start()
    try:
        log.info("listening on ws://%s:%d for setup %s", host, lobby.port, ctx.setup.setup_id)
        if on_listening is not None:
            on_listening(lobby.port)
        await lobby.wait_ready(connect_timeout)
        game = Game(ctx, lobby.conns, log_dir, model_tag=model_tag, timeout=timeout, game_id=game_id,
                    header_extra=header_extra, model=model, condition=condition, scenario=scenario,
                    scenario_info=scenario_info)
        await game.run()
        return game
    finally:
        await lobby.stop()


__all__ = ["run_game"]
