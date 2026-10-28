"""aiwolf seat: the seat view gets, at DAILY_INITIALIZE, what the schedule discloses (DESIGN §4.7 / §7.4).

Day 1 morning: night 0 had no vote and no attack, so only the Seer's own divination line is added.
Day >= 2: the previous day's votes, the execution ("- execution: Name" / "no one"), the attack as the
public "- attacked: Name" / "no one" (the Werewolf sees its own "- attack: Wolf -> Name" instead) and, for
the Seer, "- divine: Seer -> Target (human|werewolf)" / "-> none" when the divination failed. A dead
Seer gets nothing (nobody to tell; telling the others would reveal the death).

Writer mode (S-online): the shared writer view holds one line per night action, written provisionally
when the action is chosen and completed (the Seer's result) the next morning; no "- attacked" line.
"""
from __future__ import annotations

from agent.base.seat import SeatAgent
from common.protocol import Info, Request, Role
from common.transcript import attack_line, attacked_line, divine_line


class AiwolfAgent(SeatAgent):
    @property
    def role(self) -> str:
        return str(self.ctx.role_of_seat(self.seat))

    def on_period_start(self, info: Info) -> None:
        day = int(info.day)
        if day < 1:
            return
        prev = day - 1
        if prev >= 1:  # the night before had a vote and an attack
            if info.vote_list:
                self.view.set_votes(prev, [(v.agent, v.target) for v in info.vote_list])
            self.view.set_execution(prev, info.executed_agent or None)
        if self.writer_mode:
            if self.role == Role.SEER:
                dr = info.divine_result
                line = (divine_line(self.name, dr.target, dr.result) if dr is not None and dr.agent == self.name
                        else divine_line(self.name, None, None))
                self.view.upsert_action(prev, f"divine:{self.name}", line)
            if prev >= 1 and self.role == Role.WEREWOLF:
                self.view.upsert_action(prev, f"attack:{self.name}", attack_line(self.name, info.attacked_agent or None))
            return
        lines: list[str] = []
        if self.role == Role.SEER:
            dr = info.divine_result
            if dr is not None and dr.agent == self.name:
                lines.append(divine_line(self.name, dr.target, dr.result))
            else:
                lines.append(divine_line(self.name, None, None))
        if prev >= 1:
            if self.role == Role.WEREWOLF:
                lines.append(attack_line(self.name, info.attacked_agent or None))
            else:
                lines.append(attacked_line(info.attacked_agent or None))
        self.view.set_actions(prev, lines)

    def on_finish(self, info: Info) -> None:
        if not self.writer_mode:
            return
        day = int(info.day)
        if day >= 1 and info.vote_list:
            self.view.set_votes(day, [(v.agent, v.target) for v in info.vote_list])
            self.view.set_execution(day, info.executed_agent or None)

    def vote_candidates(self, info: Info) -> list[str]:
        return self.living(info)  # self included (allow_self_vote)

    def action_candidates(self, request: Request, info: Info) -> list[str]:
        if request not in (Request.DIVINE, Request.ATTACK):
            raise ValueError(f"aiwolf has no action {request}")
        return self.living_others(info)

    def action_label(self, request: Request) -> str:
        if request == Request.DIVINE:
            return divine_line(self.name, None, None).split(" -> ")[0] + " ->"
        return attack_line(self.name, None).split(" -> ")[0] + " ->"

    def on_action_reply(self, request: Request, target: str | None) -> None:
        # provisional own line until the morning discloses the result
        if request == Request.DIVINE:
            result = None
            if self.writer_mode and target:  # the writer knows every role: write the result like the batch writer
                result = str(Role(self.ctx.role_of_name(target)).species).lower()
            key, line = f"divine:{self.name}", divine_line(self.name, target, result)
        else:
            key, line = f"attack:{self.name}", attack_line(self.name, target)
        if self.writer_mode:
            self.view.upsert_action(self.round, key, line)
        else:
            self.view.set_actions(self.round, [line])
