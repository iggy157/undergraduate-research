"""Common log schema (DESIGN §3): one CSV row type and the jsonl record kinds."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

CSV_FIELDS = ("seq", "round", "turn", "type", "agent", "target", "text", "extra")
ROW_TYPES = ("status", "talk", "pass", "vote", "action", "result")
JSONL_KINDS = ("header", "llm_call", "violations", "note")

WINNER_VILLAGE = "VILLAGE"
WINNER_WEREWOLF = "WEREWOLF"
WINNER_NONE = "NONE"


@dataclass
class LogRow:
    seq: int
    round: int
    turn: int | None
    type: str
    agent: str
    target: str
    text: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_csv(self) -> list[str]:
        return [str(self.seq), str(self.round), "" if self.turn is None else str(self.turn), self.type,
                self.agent, self.target, self.text,
                json.dumps(self.extra, ensure_ascii=False, separators=(",", ":")) if self.extra else ""]

    @staticmethod
    def from_csv(rec: list[str]) -> "LogRow":
        if len(rec) != len(CSV_FIELDS):
            raise ValueError(f"expected {len(CSV_FIELDS)} columns, got {len(rec)}: {rec!r}")
        seq, rnd, turn, typ, agent, target, text, extra = rec
        if typ not in ROW_TYPES:
            raise ValueError(f"unknown row type {typ!r}")
        return LogRow(int(seq), int(rnd), int(turn) if turn != "" else None, typ, agent, target, text,
                      json.loads(extra) if extra else {})


def normalize_winner(w: str | None) -> str:
    if w is None:
        return WINNER_NONE
    u = str(w).strip().upper()
    if u in ("VILLAGE", "VILLAGER", "VILLAGERS", "HUMAN"):
        return WINNER_VILLAGE
    if u in ("WEREWOLF", "WEREWOLVES", "WOLF", "WOLVES"):
        return WINNER_WEREWOLF
    return WINNER_NONE
