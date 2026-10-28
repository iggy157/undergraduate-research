"""Domain strategy interface. One small subclass per domain (server/aiwolf, server/candidate_selection)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from common.tiebreak import Tally

if TYPE_CHECKING:  # pragma: no cover
    from .game import Game


class DomainLogic:
    """Hooks called by ``Game`` (server/base/game.py). ``info`` hooks return extra ``info`` keys."""

    vote_request = "vote"  # value of the vote row's extra.request

    def __init__(self, game: Game):
        self.game = game
        self.ctx = game.ctx
        self.rules = game.ctx.rules
        self.first_round = int(self.rules.get("first_round", 1))
        self.last_round = int(self.rules["rounds_total"])
        self.abort_reason: str | None = None

    # ---- schedule -------------------------------------------------------------------------
    def rounds(self) -> range:
        return range(self.first_round, self.last_round + 1)

    def has_vote(self, round_no: int) -> bool:
        raise NotImplementedError

    # ---- info extensions ------------------------------------------------------------------
    def init_info(self, seat: int) -> dict[str, Any]:
        return {}

    def daily_init_info(self, seat: int, round_no: int) -> dict[str, Any]:
        return {}

    def finish_info(self, seat: int) -> dict[str, Any]:
        return {}

    # ---- phases ---------------------------------------------------------------------------
    def parse_vote(self, seat: int, raw: str | None) -> str | None:
        raise NotImplementedError

    async def after_vote(self, round_no: int, t: Tally) -> None:
        pass

    async def actions(self, round_no: int) -> None:
        """Private actions after talk (+vote) of ``round_no``; only called while not finished."""

    def finished(self) -> bool:
        raise NotImplementedError

    def conclude(self) -> None:
        """Called once after the last round when the game did not finish by itself."""

    def abort(self, reason: str) -> None:
        self.abort_reason = reason

    def write_result(self) -> None:
        raise NotImplementedError

    def outcome(self) -> dict[str, Any]:
        raise NotImplementedError

    # ---- header helpers -------------------------------------------------------------------
    def private_seed(self, seat: int) -> str:
        return self.ctx.role_of_seat(seat)

    def header_fields(self) -> dict[str, Any]:
        # same values as the single method writes for aiwolf (no cards): [] and 0, not null
        return {"card_pool": [], "n_options": 0, "n_unique_cards": 0}


def make_logic(domain: str, game: Game) -> DomainLogic:
    if domain == "aiwolf":
        from server.aiwolf import AiwolfLogic
        return AiwolfLogic(game)
    if domain == "candidate_selection":
        from server.candidate_selection import CandidateSelectionLogic
        return CandidateSelectionLogic(game)
    if domain == "shared_living":
        from server.shared_living import SharedLivingLogic
        return SharedLivingLogic(game)
    raise ValueError(f"unknown domain {domain!r}")


__all__ = ["DomainLogic", "make_logic"]
