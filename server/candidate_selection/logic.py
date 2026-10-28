"""Discussion domains (candidate_selection / shared_living) on top of the common loop.

Round 1: talk -> INVESTIGATE (dynamic: each seat picks 2 titles; fixed: fixed_assignment, no
request). Round 2: DAILY_INITIALIZE carries the seat's own findings. Round 3: DAILY_INITIALIZE
reveals the options; after the talk every seat votes for one label; the most voted (tie-break:
common.tiebreak) is adopted and written as the result row.
"""
from __future__ import annotations

from typing import Any

from common.protocol import Request
from common.tiebreak import Tally
from server.base.domain import DomainLogic
from server.base.parse import match_option, parse_investigate


class DiscussionLogic(DomainLogic):
    vote_request = "vote_final"

    def __init__(self, game):
        super().__init__(game)
        self.investigated: dict[int, list[dict[str, Any]]] = {}
        self.tally: Tally | None = None
        self.adopted: str | None = None
        self.reason: str | None = None
        self._done = False
        slot = self.ctx.roles["PARTICIPANT"]["action"]
        self.choose = int(slot.get("choose", 2))
        self.investigate_round = self.first_round  # "after_round_1"

    @property
    def dynamic(self) -> bool:
        return self.ctx.setup.info_mode == "dynamic"

    # ---- schedule -------------------------------------------------------------------------
    def has_vote(self, round_no: int) -> bool:
        return round_no == self.last_round

    # ---- info -----------------------------------------------------------------------------
    def init_info(self, seat: int) -> dict[str, Any]:
        out: dict[str, Any] = {"problem": self.ctx.problem_of_seat(seat)}
        if self.dynamic:
            out["card_titles"] = [c["title"] for c in self.ctx.card_pool()]
        return out

    def daily_init_info(self, seat: int, round_no: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if round_no == self.investigate_round + 1:
            out["investigate_result"] = [{"card_id": c["card_id"], "title": c["title"], "text": c["text"]}
                                         for c in self.investigated.get(seat, [])]
        if round_no == self.last_round:
            out["options"] = self.ctx.options()
        return out

    def finish_info(self, seat: int) -> dict[str, Any]:
        return {"options": self.ctx.options(), "adopted": self.adopted,
                "vote_list": self.game.vote_lists.get(self.last_round)}

    # ---- vote -----------------------------------------------------------------------------
    def parse_vote(self, seat: int, raw: str | None) -> str | None:
        return match_option(raw, self.ctx.options())

    async def after_vote(self, round_no: int, t: Tally) -> None:
        self.tally = t
        self.adopted = t.chosen
        self._done = True

    # ---- investigate ----------------------------------------------------------------------
    async def actions(self, round_no: int) -> None:
        if round_no != self.investigate_round:
            return
        g = self.game
        if not self.dynamic:
            for seat in self.ctx.setup.speaking_order:
                cards = [c for c in self.ctx.fixed_cards_of_seat(seat) if c]
                self.investigated[seat] = cards
                g.writer.action(round_no, "investigate", g.name(seat), "", self._titles_text(cards),
                                cards=[c["card_id"] for c in cards], parse="fixed")
            return
        titles = [c["title"] for c in self.ctx.card_pool()]
        packets = {s: g.packet(Request.INVESTIGATE, s, round_no, card_titles=titles)
                   for s in self.ctx.setup.speaking_order if g.alive[s]}
        replies: dict[int, str | None] = {}
        for s in packets:  # speaking order, one after another (see Game.vote_phase)
            replies[s] = await g.ask(s, packets[s])
        for seat in packets:
            raw = replies[seat]
            cards, parse = parse_investigate(raw, self.ctx.card_pool(), self.choose)
            self.investigated[seat] = cards
            extra: dict[str, Any] = {"cards": [c["card_id"] for c in cards], "parse": parse}
            if raw is None:
                extra["timeout"] = True
            elif parse != "ok":
                extra["raw"] = raw
            g.writer.action(round_no, "investigate", g.name(seat), "", self._titles_text(cards), **extra)

    @staticmethod
    def _titles_text(cards: list[dict[str, Any]]) -> str:
        # fixed mode may run on data whose titles are still empty (DESIGN §9-9): fall back to the id
        return "; ".join(c["title"] or c["card_id"] for c in cards)

    # ---- end of game ----------------------------------------------------------------------
    def finished(self) -> bool:
        return self._done

    def abort(self, reason: str) -> None:
        super().abort(reason)
        self.reason = reason

    def write_result(self) -> None:
        self.game.writer.result(self.last_round, self.adopted or "", **self.outcome())

    def outcome(self) -> dict[str, Any]:
        t = self.tally
        out: dict[str, Any] = {"adopted": self.adopted, "tally": t.counts if t else {}, "tie": bool(t and t.tie)}
        if self.reason is not None:
            out["reason"] = self.reason
        return out

    # ---- header ---------------------------------------------------------------------------
    def private_seed(self, seat: int) -> str:
        return self.ctx.problem_of_seat(seat) or ""

    def header_fields(self) -> dict[str, Any]:
        ids = {c["card_id"] for cards in self.investigated.values() for c in cards}
        return {"card_pool": [{"card_id": c["card_id"], "title": c["title"], "origin_seat": c.get("origin_seat")}
                              for c in self.ctx.card_pool()],
                "n_options": len(self.ctx.options()), "n_unique_cards": len(ids)}


__all__ = ["DiscussionLogic"]
