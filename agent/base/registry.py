"""Domain -> agent class."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from common.setup import GameContext
from common.transcript import SeatTranscript

from .llm import LLMClient
from .seat import SeatAgent


def agent_class(domain: str) -> type[SeatAgent]:
    if domain == "aiwolf":
        from agent.aiwolf import AiwolfAgent
        return AiwolfAgent
    if domain == "candidate_selection":
        from agent.candidate_selection import CandidateSelectionAgent
        return CandidateSelectionAgent
    if domain == "shared_living":
        from agent.shared_living import SharedLivingAgent
        return SharedLivingAgent
    raise ValueError(f"unknown domain {domain!r}")


def make_agent(ctx: GameContext, seat: int, llm: LLMClient, log_dir: Path | str,
               max_tokens: dict[str, int] | None = None, stop_talk: list[str] | None = None, *,
               reveal: bool = False, writer: bool = False, stepped: bool = False,
               scenario: dict[str, Any] | None = None, shared_view: SeatTranscript | None = None,
               lock: threading.RLock | None = None) -> SeatAgent:
    return agent_class(ctx.domain)(ctx, seat, llm, log_dir, max_tokens=max_tokens, stop_talk=stop_talk,
                                   reveal=reveal, writer=writer, stepped=stepped, scenario=scenario,
                                   shared_view=shared_view, lock=lock)


def make_game_agents(ctx: GameContext, llm_factory, log_dir: Path | str, max_tokens: dict[str, int] | None = None,
                     stop_talk: list[str] | None = None, *, reveal: bool = False, writer: bool = False,
                     stepped: bool = False, scenario: dict[str, Any] | None = None) -> list[SeatAgent]:
    """The five seats of one game in one process. In writer / stepped mode they share the writer view and a lock."""
    shared = SeatTranscript(ctx, None) if (writer or stepped) else None
    lock = threading.RLock()
    return [make_agent(ctx, s, llm_factory(), log_dir, max_tokens=max_tokens, stop_talk=stop_talk, reveal=reveal,
                       writer=writer, stepped=stepped, scenario=scenario, shared_view=shared, lock=lock)
            for s in range(1, 6)]
