"""Source repo (manyshot-ablation) panel / living ``result.json`` -> common rows. Test-only (DESIGN §3.3).

``result.json`` (scripts/run_deliberation.py there)::

    {"game_id", "domain": "panel"|"living", "condition", "instance_id": "panel_006",
     "participants": [{"name", "objective", "profile", "cards"?: [text, text], "problem"?: str}],
     "turns": [{"cycle", "actor", "kind": "talk", "text"} |
               {"cycle", "actor", "kind": "pass", "text": "Over"} |
               {"cycle", "actor", "kind": "select", "request": "vote_final"|"eliminate_rK"|"leaning_rK",
                "selection": "B", "text": "(vote_final)", "raw"?: str, "raw_retry"?: str, "fallback"?: str}],
     "outcome_code": "B", "meta": {"model", "rounds", "cast_seed", "protocol"?}}

The turns carry no round / turn number. They are reconstructed from the generation loop of the
source (per round: up to ``turns_per_round`` sweeps over the seats in a fixed order; a seat that
said ``Over`` is skipped for the rest of the round):

* a ``select`` with request ``..._r<K>`` pins the round to K; ``vote_final`` pins it to ``meta.rounds``;
  after a block of selects the next talk starts round K+1;
* within talks, a new sweep starts when an actor repeats inside the current sweep, and a new round
  starts when an actor that has already passed in this round speaks again, or when the sweep count
  exceeds ``turns_per_round``.

Caveat (documented, not fixed): the source logs a ``Skip`` as a ``pass`` with text ``Over`` too, so a
seat that skipped and then spoke again looks like a round boundary. Skips were rare in the source
runs; the fixture test asserts the round counts of a known game.

Rows: ``status`` (all seats, role PARTICIPANT, at every round start and at the end; participant
``profile`` / ``objective`` / ``problem`` kept in extra), ``talk`` / ``pass``, ``vote`` (request,
raw, raw_retry, fallback kept in extra), ``result`` (text = ``outcome_code``, extra adopted / tally /
tie recomputed from the final votes). Seats follow the participant order unless a ``GameContext``
with the same names is given.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ..logwriter import count_words, find_mentions
from ..schema import LogRow
from ..setup import GameContext

_REQ_ROUND = re.compile(r"_r(\d+)$")
DOMAIN_OF = {"panel": "candidate_selection", "living": "shared_living"}


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assign_rounds(turns: list[dict[str, Any]], rounds_total: int, turns_per_round: int = 4,
                  ) -> list[tuple[int, int | None]]:
    """(round, sweep|None) for every turn, by the heuristic in the module docstring."""
    out: list[tuple[int, int | None]] = []
    rnd, sweep = 1, 1
    seen: set[str] = set()
    done: set[str] = set()
    after_select = False
    select_round: int | None = None
    for t in turns:
        kind = t.get("kind")
        actor = str(t.get("actor", ""))
        if kind == "select":
            m = _REQ_ROUND.search(str(t.get("request", "")))
            if m:
                select_round = int(m.group(1))
            elif str(t.get("request", "")).startswith("vote_final"):
                select_round = rounds_total
            else:
                select_round = rnd
            rnd = select_round
            after_select = True
            out.append((rnd, None))
            continue
        if after_select:
            rnd, sweep, seen, done, after_select = rnd + 1, 1, set(), set(), False
        elif (actor in done or (actor in seen and sweep >= turns_per_round)) and rnd < rounds_total:
            rnd, sweep, seen, done = rnd + 1, 1, set(), set()
        elif actor in seen or actor in done:
            # a repeat inside the last round (or a Skip logged as Over): new sweep, never a new round
            sweep += 1
            seen = set()
            done.discard(actor)
        seen.add(actor)
        if kind == "pass":
            done.add(actor)
        out.append((rnd, sweep))
    return out


def convert(result: dict[str, Any], ctx: GameContext | None = None, turns_per_round: int = 4,
            ) -> list[LogRow]:
    parts = list(result.get("participants", []))
    names = [str(p["name"]) for p in parts]
    if ctx is not None and sorted(ctx.names) == sorted(names):
        seat_of = {n: ctx.seat_of_name(n) for n in names}
    else:
        seat_of = {n: i + 1 for i, n in enumerate(names)}
    by_seat = sorted(names, key=lambda n: seat_of[n])
    info = {str(p["name"]): p for p in parts}
    rounds_total = int((result.get("meta") or {}).get("rounds", 3))
    turns = list(result.get("turns", []))
    placed = assign_rounds(turns, rounds_total, turns_per_round)

    rows: list[LogRow] = []

    def add(rnd: int, turn: int | None, typ: str, agent: str, target: str, text: str, extra: dict[str, Any]) -> None:
        rows.append(LogRow(len(rows), rnd, turn, typ, agent, target, text, extra))

    def status_block(rnd: int) -> None:
        for n in by_seat:
            p = info[n]
            extra: dict[str, Any] = {"seat": seat_of[n], "role": "PARTICIPANT", "alive": True}
            for k in ("profile", "objective", "problem", "cards"):
                if k in p:
                    extra[k] = p[k]
            add(rnd, None, "status", n, "", "ALIVE", extra)

    current_round = 0
    last_votes: dict[str, str] = {}
    last_vote_round = 0
    for t, (rnd, sweep) in zip(turns, placed):
        if rnd != current_round:
            current_round = rnd
            status_block(rnd)
        kind = t.get("kind")
        actor = str(t.get("actor", ""))
        if kind == "talk":
            text = str(t.get("text", ""))
            add(rnd, sweep, "talk", actor, "", text,
                {"words": count_words(text), "mentions": find_mentions(text, names, exclude=actor), "raw_differs": False})
        elif kind == "pass":
            add(rnd, sweep, "pass", actor, "", str(t.get("text", "Over")), {"forced": False, "empty": False})
        elif kind == "select":
            sel = str(t.get("selection", "") or "")
            extra = {"request": str(t.get("request", "select")), "raw": str(t.get("raw", sel)), "valid": bool(sel)}
            for k in ("raw_retry", "fallback"):
                if k in t:
                    extra[k] = t[k]
            add(rnd, None, "vote", actor, sel, "", extra)
            if rnd != last_vote_round:
                last_votes, last_vote_round = {}, rnd
            last_votes[actor] = sel
    final_round = max(current_round, rounds_total)
    if current_round != final_round:
        current_round = final_round
    status_block(final_round)
    adopted = str(result.get("outcome_code", "") or "")
    tally = dict(sorted(Counter(v for v in last_votes.values() if v).items()))
    top = [k for k, v in tally.items() if tally and v == max(tally.values())]
    add(final_round, None, "result", "", "", adopted, {"adopted": adopted, "tally": tally, "tie": len(top) > 1,
                                                         "source_game_id": result.get("game_id"),
                                                         "source_instance_id": result.get("instance_id"),
                                                         "domain": DOMAIN_OF.get(str(result.get("domain")),
                                                                                 result.get("domain"))})
    return rows


__all__ = ["DOMAIN_OF", "assign_rounds", "convert", "load"]
