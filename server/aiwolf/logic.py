"""5-player werewolf on top of the common loop (DESIGN §4.5-7, IMPLEMENTATION_NOTES §3).

Day 0: talk + divine only. Day >= 1: talk -> vote -> execute -> (divine, attack) -> next day. The night
requests carry ``executed_agent`` (the writer view of S-online shows the execution before the night actions).
Village wins when the werewolf dies; werewolves win when #wolves >= #living humans; undecided after
the night of ``max_day`` -> NONE (reason max_day). Disconnect / notice timeout -> NONE (reason).
"""
from __future__ import annotations

from typing import Any

from common.protocol import Judge, Request, Role
from common.schema import WINNER_NONE, WINNER_VILLAGE, WINNER_WEREWOLF
from common.tiebreak import Tally
from server.base.domain import DomainLogic
from server.base.parse import match_name


class AiwolfLogic(DomainLogic):
    vote_request = "vote_day"

    def __init__(self, game):
        super().__init__(game)
        self.executed: dict[int, str] = {}        # day -> name
        self.attacked: dict[int, str] = {}        # day -> name
        self.divines: dict[int, Judge] = {}       # day -> seer's judge of that night
        self.winner: str | None = None
        self.reason: str | None = None

    # ---- role helpers ---------------------------------------------------------------------
    def seats_with_role(self, role: str, alive_only: bool = True) -> list[int]:
        g = self.game
        return [s for s in g.seats() if g.role(s) == role and (g.alive[s] or not alive_only)]

    def n_alive_wolves(self) -> int:
        return sum(1 for s in self.game.living_seats() if Role(self.game.role(s)).species == "WEREWOLF")

    def n_alive_humans(self) -> int:
        return sum(1 for s in self.game.living_seats() if Role(self.game.role(s)).species == "HUMAN")

    # ---- schedule -------------------------------------------------------------------------
    def has_vote(self, round_no: int) -> bool:
        return round_no >= 1

    # ---- info -----------------------------------------------------------------------------
    def init_info(self, seat: int) -> dict[str, Any]:
        return {}

    def _night_results(self, seat: int, day: int) -> dict[str, Any]:
        """Results of the night before ``day`` (execution of day-1, attack and divine of night day-1)."""
        prev = day - 1
        out: dict[str, Any] = {
            "executed_agent": self.executed.get(prev),
            "attacked_agent": self.attacked.get(prev),
            "vote_list": self.game.vote_lists.get(prev),
        }
        if self.game.role(seat) == Role.SEER and prev in self.divines:
            out["divine_result"] = self.divines[prev]
        return out

    def daily_init_info(self, seat: int, round_no: int) -> dict[str, Any]:
        return self._night_results(seat, round_no)

    def finish_info(self, seat: int) -> dict[str, Any]:
        out = self._night_results(seat, self.game.round + 1)
        out["role_map"] = self.game.full_role_map()
        return out

    # ---- vote / execution -----------------------------------------------------------------
    def parse_vote(self, seat: int, raw: str | None) -> str | None:
        candidates = self.game.living_names()
        if not self.rules.get("allow_self_vote", True):
            candidates = [n for n in candidates if n != self.game.name(seat)]
        return match_name(raw, candidates)

    async def after_vote(self, round_no: int, t: Tally) -> None:
        g = self.game
        if t.chosen:
            role = g.role(g.seat(t.chosen))
            g.kill(t.chosen)
            self.executed[round_no] = t.chosen
            g.writer.action(round_no, "execute", "", t.chosen, t.chosen, role=role, tie=t.tie)
        else:
            g.writer.action(round_no, "execute", "", "", "", role="", tie=False, no_target=True)
        self.check_win()

    # ---- night ----------------------------------------------------------------------------
    async def actions(self, round_no: int) -> None:
        g = self.game
        for seer in self.seats_with_role(Role.SEER):
            name = g.name(seer)
            raw = await g.ask(seer, g.packet(Request.DIVINE, seer, round_no, executed_agent=self.executed.get(round_no)))
            target = match_name(raw, [n for n in g.living_names() if n != name])
            if target:
                species = str(Role(g.role(g.seat(target))).species)
                self.divines[round_no] = Judge(round_no, name, target, species)
                # raw kept for every action: the batch-style writer (stepped) may state a result after the name
                g.writer.action(round_no, "divine", name, target, species, result=species, valid=True, raw=raw)
            else:
                g.writer.action(round_no, "divine", name, "", "", valid=False,
                                **({"timeout": True} if raw is None else {"raw": raw}))
        if round_no >= 1:
            for wolf in self.seats_with_role(Role.WEREWOLF):
                name = g.name(wolf)
                raw = await g.ask(wolf, g.packet(Request.ATTACK, wolf, round_no, executed_agent=self.executed.get(round_no)))
                target = match_name(raw, [n for n in g.living_names() if n != name])
                if target:
                    g.kill(target)
                    self.attacked[round_no] = target
                    g.writer.action(round_no, "attack", name, target, target, success=True, no_target=False, raw=raw)
                else:
                    g.writer.action(round_no, "attack", name, "", "", success=False, no_target=True,
                                    **({"timeout": True} if raw is None else {"raw": raw}))
        self.check_win()

    # ---- end of game ----------------------------------------------------------------------
    def check_win(self) -> None:
        if self.winner is not None:
            return
        wolves, humans = self.n_alive_wolves(), self.n_alive_humans()
        if wolves == 0:
            self.winner = WINNER_VILLAGE
        elif wolves >= humans:
            self.winner = WINNER_WEREWOLF

    def finished(self) -> bool:
        return self.winner is not None

    def conclude(self) -> None:
        if self.winner is None:
            self.winner, self.reason = WINNER_NONE, "max_day"

    def abort(self, reason: str) -> None:
        super().abort(reason)
        self.winner, self.reason = WINNER_NONE, reason

    def write_result(self) -> None:
        self.game.writer.result(self.game.round, self.winner or WINNER_NONE, **self.outcome())

    def outcome(self) -> dict[str, Any]:
        return {"winner": self.winner or WINNER_NONE, "villagers": self.n_alive_humans(),
                "werewolves": self.n_alive_wolves(), "reason": self.reason}

    def private_seed(self, seat: int) -> str:
        return self.game.role(seat)


__all__ = ["AiwolfLogic"]
