"""Writer / reader for the common log: <game_id>.log (CSV) + <game_id>.jsonl. DESIGN §3."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterator

from .schema import CSV_FIELDS, LogRow

_WORD_RE = re.compile(r"\S+")
# bare name occurrences (word-bounded) of the game's participants (audit C5: the "@Name" form of the
# contest server is never produced here, so the metric counts plain names in both methods)
_MENTION_RE = re.compile(r"(?<![A-Za-z])([A-Z][a-z]+)(?![a-z])")


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def find_mentions(text: str, names: list[str], exclude: str | None = None) -> list[str]:
    """Participants named in ``text`` (bare, word-bounded names; the speaker itself excluded), in order."""
    found = []
    for m in _MENTION_RE.finditer(text):
        n = m.group(1)
        if n in names and n != exclude and n not in found:
            found.append(n)
    return found


class GameLogWriter:
    """Appends rows in time order. seq is assigned here; callers never pass it."""

    def __init__(self, game_dir: Path, game_id: str, names: list[str]):
        self.game_dir = Path(game_dir)
        self.game_dir.mkdir(parents=True, exist_ok=True)
        self.game_id = game_id
        self.names = list(names)
        self._csv_f = open(self.game_dir / f"{game_id}.log", "w", encoding="utf-8", newline="")
        self._csv = csv.writer(self._csv_f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        self._jsonl_f = open(self.game_dir / f"{game_id}.jsonl", "w", encoding="utf-8")
        self._seq = 0
        self.rows: list[LogRow] = []

    # ---- csv rows -------------------------------------------------------
    def _row(self, round_no: int, turn: int | None, typ: str, agent: str, target: str, text: str,
             extra: dict[str, Any] | None) -> LogRow:
        row = LogRow(self._seq, round_no, turn, typ, agent, target, text, dict(extra or {}))
        self._seq += 1
        self._csv.writerow(row.to_csv())
        self._csv_f.flush()
        self.rows.append(row)
        return row

    def status(self, round_no: int, agent: str, seat: int, role: str, alive: bool) -> LogRow:
        return self._row(round_no, None, "status", agent, "", "ALIVE" if alive else "DEAD",
                         {"seat": seat, "role": role, "alive": alive})

    def talk(self, round_no: int, turn: int, agent: str, text: str, raw: str | None = None,
             **extra: Any) -> LogRow:
        e = {"words": count_words(text), "mentions": find_mentions(text, self.names, exclude=agent),
             "raw_differs": (raw is not None and raw.strip() != text)}  # edge whitespace (continuation) is not a change
        e.update(extra)
        return self._row(round_no, turn, "talk", agent, "", text, e)

    def pass_(self, round_no: int, turn: int, agent: str, token: str, forced: bool = False,
              empty: bool = False, **extra: Any) -> LogRow:
        e = {"forced": forced, "empty": empty}
        e.update(extra)
        return self._row(round_no, turn, "pass", agent, "", token, e)

    def vote(self, round_no: int, agent: str, target: str | None, raw: str, valid: bool,
             request: str = "vote", **extra: Any) -> LogRow:
        e = {"request": request, "raw": raw, "valid": valid}
        e.update(extra)
        return self._row(round_no, None, "vote", agent, target or "", "", e)

    def action(self, round_no: int, action: str, agent: str, target: str, text: str,
               **extra: Any) -> LogRow:
        e = {"action": action}
        e.update(extra)
        return self._row(round_no, None, "action", agent, target, text, e)

    def result(self, round_no: int, text: str, **extra: Any) -> LogRow:
        return self._row(round_no, None, "result", "", "", text, dict(extra))

    # ---- jsonl ----------------------------------------------------------
    def record(self, kind: str, **payload: Any) -> None:
        self._jsonl_f.write(json.dumps({"kind": kind, **payload}, ensure_ascii=False) + "\n")
        self._jsonl_f.flush()

    def header(self, **payload: Any) -> None:
        self.record("header", game_id=self.game_id, **payload)

    def llm_call(self, **payload: Any) -> None:
        self.record("llm_call", **payload)

    def close(self) -> None:
        self._csv_f.close()
        self._jsonl_f.close()


def read_log(path: Path) -> list[LogRow]:
    with open(path, encoding="utf-8", newline="") as f:
        return [LogRow.from_csv(rec) for rec in csv.reader(f)]


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_rows(path: Path, rows: list[LogRow]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        for r in rows:
            w.writerow(r.to_csv())


__all__ = ["GameLogWriter", "read_log", "read_jsonl", "write_rows", "count_words", "find_mentions",
           "CSV_FIELDS"]
