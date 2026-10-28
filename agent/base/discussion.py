"""Shared behaviour of the two discussion domains (candidate_selection / shared_living), DESIGN §7.4.

Round 2 start: the seat's own investigation line (titles as the server resolved them) in round 1 and a
"### Findings" section in round 2 (empty findings -> "- investigate: Name -> none", no section). Round 3
start: "### Options". Vote candidates are the option labels revealed at round 3; INVESTIGATE candidates
are the titles from INITIALIZE.

Writer mode (S-online): the writer view has one investigation line per seat and no Findings / Options
sections (the card texts and the options are in the system prompt's hidden information).
"""
from __future__ import annotations

import re

from common.protocol import Info, Request
from common.transcript import investigate_line

from .seat import SeatAgent

_SEP = re.compile(r"[;\n]")


class DiscussionAgent(SeatAgent):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.card_titles: list[str] = [t for t in self.rules["card_titles"] if t]
        self.option_labels: list[str] = list(self.ctx.option_labels())
        self.options_revealed = False

    def on_initialize(self, info: Info) -> None:
        if info.card_titles:
            self.card_titles = [str(t) for t in info.card_titles]

    def on_period_start(self, info: Info) -> None:
        rnd = int(info.day)
        if info.investigate_result is not None:  # the round after the investigation: findings are due
            cards = list(info.investigate_result)
            line = investigate_line(self.name, [str(c.get("title") or "") for c in cards])
            if self.writer_mode:
                if self.ctx.setup.info_mode != "fixed":  # fixed mode: cards are assigned, the writer writes no line
                    self.view.upsert_action(rnd - 1, f"investigate:{self.name}", line)
            else:
                self.view.set_actions(rnd - 1, [line])
                self.view.set_findings(rnd, cards)
        if info.options:
            self.option_labels = [str(o["label"]) for o in info.options]
            self.options_revealed = True
            if not self.writer_mode:
                self.view.set_options(rnd, info.options)

    def on_finish(self, info: Info) -> None:
        if not self.writer_mode:
            return
        last = int(self.rules["rounds_total"])
        if info.vote_list:
            self.view.set_votes(last, [(v.agent, v.target) for v in info.vote_list])
        if info.adopted is not None or info.vote_list:
            self.view.set_adopted(last, info.adopted or None)

    def vote_candidates(self, info: Info) -> list[str]:
        return list(self.option_labels)

    def action_candidates(self, request: Request, info: Info) -> list[str]:
        if request != Request.INVESTIGATE:
            raise ValueError(f"{self.ctx.domain} has no action {request}")
        return list(self.card_titles)

    def action_label(self, request: Request) -> str:
        return f"- investigate: {self.name} ->"

    def on_action_reply(self, request: Request, reply: str | None) -> None:
        titles = [t.strip().strip("-* ").strip() for t in _SEP.split(reply or "") if t.strip()]
        line = investigate_line(self.name, titles)
        if self.writer_mode:
            self.view.upsert_action(self.round, f"investigate:{self.name}", line)
        else:
            self.view.set_actions(self.round, [line])
