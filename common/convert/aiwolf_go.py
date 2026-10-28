"""Go aiwolf-nlp-server native logs -> common rows (DESIGN §3.3; used by the compatibility test only).

Go game log (``game_logger``), one CSV line per event, commas in talk text are **not** escaped, so
every line is split with a type-specific ``maxsplit``::

    day,status,idx,role,ALIVE|DEAD,originalName[,gameName]
    day,talk,idx,turn,agentIdx,text          (turn is 0-based; text may contain commas)
    day,whisper,idx,turn,agentIdx,text       (ignored: 5-player village has one wolf)
    day,vote,voterIdx,targetIdx              (only *valid* votes appear)
    day,execute,idx,role
    day,divine,seerIdx,targetIdx,HUMAN|WEREWOLF
    day,guard,...                            (ignored)
    day,attackVote,wolfIdx,targetIdx
    day,attack,targetIdx|-1,true|false
    day,result,villagers,werewolves,winSide  (or the older 3-column ``day,result,TEAM``)

Go JSON log (``json_logger``): ``{"agents": [{idx, team, name, role}], "entries": [{agent (game
name), request (JSON string), response, error, ...}], "game_id", "win_side"}``. It is optional; when
given it is used to recover (a) the raw TALK response (``raw_differs``, ``forced`` / ``empty``
pass flags) and (b) invalid votes / divines / attacks (requests with no matching CSV line) which
become ``valid:false`` rows exactly like the Python server writes them.

Mapping: Go agent ``idx`` == seat; names come from ``ctx.name_of_seat(idx)`` (the setup), so pass a
context whose seats correspond to the Go assignment (:func:`context_from_log` builds one from the
status lines, since the Go server shuffles roles and personas). Roles in ``status`` rows are taken
from the log. Within a day the Go order is fixed (status -> talk -> vote -> execute -> divine ->
attackVote/attack), and rows are emitted in that order with the invalid votes merged in at the
vote step.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from ..logwriter import count_words, find_mentions
from ..protocol import T_FORCE_SKIP, T_OVER, T_SKIP
from ..schema import LogRow, normalize_winner
from ..setup import GameContext, Seat, Setup, load_personas, load_roles, load_rules

_SPLITS = {"status": 7, "talk": 6, "whisper": 6, "vote": 4, "execute": 4, "divine": 5, "guard": 5,
           "attackVote": 4, "attack": 4, "result": 5}


@dataclass
class _Day:
    status: list[list[str]] = field(default_factory=list)
    talks: list[list[str]] = field(default_factory=list)
    votes: list[list[str]] = field(default_factory=list)
    execute: list[str] | None = None
    divines: list[list[str]] = field(default_factory=list)
    attack_votes: list[list[str]] = field(default_factory=list)
    attacks: list[list[str]] = field(default_factory=list)
    result: list[str] | None = None


def parse_csv(csv_text: str) -> dict[int, _Day]:
    """Group the Go CSV lines by day, splitting each by its type-specific column count."""
    days: dict[int, _Day] = defaultdict(_Day)
    for raw in csv_text.splitlines():
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        head = line.split(",", 2)
        if len(head) < 2:
            continue
        day, typ = int(head[0]), head[1]
        n = _SPLITS.get(typ)
        if n is None:
            continue
        cols = line.split(",", n - 1)
        d = days[day]
        if typ == "status":
            d.status.append(cols)
        elif typ == "talk":
            d.talks.append(cols)
        elif typ == "vote":
            d.votes.append(cols)
        elif typ == "execute":
            d.execute = cols
        elif typ == "divine":
            d.divines.append(cols)
        elif typ == "attackVote":
            d.attack_votes.append(cols)
        elif typ == "attack":
            d.attacks.append(cols)
        elif typ == "result":
            d.result = cols
    return dict(sorted(days.items()))


def log_names(csv_text: str) -> dict[int, tuple[str, str]]:
    """idx -> (game name, role) from the first status block (game name = last column)."""
    out: dict[int, tuple[str, str]] = {}
    for d in parse_csv(csv_text).values():
        for cols in d.status:
            idx = int(cols[2])
            if idx not in out:
                out[idx] = (cols[-1], cols[3])
        if out:
            break
    return out


def context_from_log(csv_text: str, setup_id: str = "aiwolf_0000", speaking_order: list[int] | None = None,
                     ) -> GameContext:
    """A GameContext whose seats mirror the Go assignment (idx -> persona name, role) in the status lines."""
    names = log_names(csv_text)
    if sorted(names) != [1, 2, 3, 4, 5]:
        raise ValueError(f"expected agent idx 1..5 in status lines, got {sorted(names)}")
    personas = load_personas()
    seats = []
    for idx in range(1, 6):
        name, role = names[idx]
        if name not in personas:
            raise ValueError(f"game name {name!r} is not one of the 24 personas")
        seats.append(Seat(idx, name, role))
    k = int(setup_id.rsplit("_", 1)[1])
    setup = Setup(setup_id=setup_id, domain="aiwolf", k=k, seats=seats,
                  speaking_order=speaking_order or [1, 2, 3, 4, 5])
    return GameContext(setup, personas, load_roles("aiwolf"), load_rules("aiwolf"), None)


# ---- json log --------------------------------------------------------------------------------
def _entries(server_json: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten entries: {agent, request, day, response, error}."""
    out = []
    for e in (server_json or {}).get("entries", []):
        req = e.get("request")
        if isinstance(req, str):
            try:
                req = json.loads(req)
            except json.JSONDecodeError:
                continue
        if not isinstance(req, dict):
            continue
        out.append({"agent": e.get("agent"), "request": req.get("request"),
                    "day": int((req.get("info") or {}).get("day", -1)),
                    "response": e.get("response"), "error": e.get("error")})
    return out


class _Converter:
    def __init__(self, csv_text: str, server_json: dict[str, Any] | None, ctx: GameContext):
        self.days = parse_csv(csv_text)
        self.ctx = ctx
        self.names = list(ctx.names)
        self.name_of_idx = {i: ctx.name_of_seat(i) for i in range(1, 6)}
        # game name used in the json log -> idx (from the status lines; falls back to ctx names)
        self.idx_of_gamename = {gn: idx for idx, (gn, _) in log_names(csv_text).items()}
        for idx, n in self.name_of_idx.items():
            self.idx_of_gamename.setdefault(n, idx)
        self.entries = _entries(server_json)
        self.rows: list[LogRow] = []
        self.seq = 0
        # per-agent TALK entries in order, consumed as talk lines are converted
        self.talk_entries: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for e in self.entries:
            if e["request"] == "TALK" and e["agent"] in self.idx_of_gamename:
                self.talk_entries[self.idx_of_gamename[e["agent"]]].append(e)
        self.has_json = bool(self.entries)

    def _row(self, rnd: int, turn: int | None, typ: str, agent: str, target: str, text: str,
             extra: dict[str, Any]) -> LogRow:
        r = LogRow(self.seq, rnd, turn, typ, agent, target, text, extra)
        self.seq += 1
        self.rows.append(r)
        return r

    def _name(self, idx_s: str) -> str:
        idx = int(idx_s)
        return self.name_of_idx.get(idx, "") if idx > 0 else ""

    def _requests(self, day: int, request: str) -> list[dict[str, Any]]:
        return [e for e in self.entries if e["request"] == request and e["day"] == day]

    # ---- per type ----
    def status(self, day: int, cols: list[str]) -> None:
        idx = int(cols[2])
        alive = cols[4].strip().upper() == "ALIVE"
        self._row(day, None, "status", self._name(cols[2]), "", "ALIVE" if alive else "DEAD",
                  {"seat": idx, "role": cols[3], "alive": alive})

    def talk(self, day: int, cols: list[str]) -> None:
        turn = int(cols[3]) + 1
        idx = int(cols[4])
        text = cols[5] if len(cols) > 5 else ""
        agent = self._name(cols[4])
        raw: str | None = None
        err = None
        q = self.talk_entries.get(idx)
        if q:
            e = q.pop(0)
            err = e.get("error")
            # the Go json logger omits "response" when the reply was the empty string
            raw = e.get("response") if e.get("response") is not None else ("" if not err else None)
        if text in (T_SKIP, T_OVER):
            forced = bool(err) or raw == T_FORCE_SKIP
            empty = text == T_OVER and raw is not None and raw.strip() == "" and not err
            extra: dict[str, Any] = {"forced": forced, "empty": empty}
            if raw is not None and raw != text:
                extra["raw"] = raw
            self._row(day, turn, "pass", agent, "", text, extra)
            return
        self._row(day, turn, "talk", agent, "", text,
                  {"words": count_words(text), "mentions": find_mentions(text, self.names, exclude=agent),
                   "raw_differs": raw is not None and raw != text})

    def votes(self, day: int, d: _Day) -> list[str]:
        """Valid votes from CSV + invalid ones from JSON (voters with a VOTE request but no vote line)."""
        valid = {int(c[2]): int(c[3]) for c in d.votes}
        order: list[int] = []
        raw_of: dict[int, str] = {}
        for e in self._requests(day, "VOTE"):
            idx = self.idx_of_gamename.get(e["agent"])
            if idx is None or idx in order:
                continue
            order.append(idx)
            raw_of[idx] = e.get("response") or ""
        for idx in valid:
            if idx not in order:
                order.append(idx)
        targets: list[str] = []
        for idx in order:
            agent = self.name_of_idx.get(idx, "")
            if idx in valid:
                t = self.name_of_idx.get(valid[idx], "")
                targets.append(t)
                self._row(day, None, "vote", agent, t, "", {"request": "vote", "raw": raw_of.get(idx, t),
                                                           "valid": True})
            else:
                self._row(day, None, "vote", agent, "", "", {"request": "vote", "raw": raw_of.get(idx, ""),
                                                            "valid": False})
        return targets

    def execute(self, day: int, cols: list[str], targets: list[str]) -> None:
        name = self._name(cols[2])
        counts: dict[str, int] = {}
        for t in targets:
            counts[t] = counts.get(t, 0) + 1
        top = [k for k, v in counts.items() if counts and v == max(counts.values())]
        self._row(day, None, "action", "", name, name, {"action": "execute", "role": cols[3], "tie": len(top) > 1})

    def divines(self, day: int, d: _Day) -> None:
        done = {int(c[2]) for c in d.divines}
        for cols in d.divines:
            seer, target, species = self._name(cols[2]), self._name(cols[3]), cols[4].strip().upper()
            self._row(day, None, "action", seer, target, species, {"action": "divine", "result": species, "valid": True})
        for e in self._requests(day, "DIVINE"):
            idx = self.idx_of_gamename.get(e["agent"])
            if idx is None or idx in done:
                continue
            done.add(idx)
            self._row(day, None, "action", self.name_of_idx[idx], "", "",
                      {"action": "divine", "result": None, "valid": False, "raw": e.get("response") or ""})

    def attack(self, day: int, d: _Day) -> None:
        if not d.attacks and not d.attack_votes:
            # a wolf was asked but nothing happened (no attack line): record the failed request
            for e in self._requests(day, "ATTACK"):
                idx = self.idx_of_gamename.get(e["agent"])
                if idx is not None:
                    self._row(day, None, "action", self.name_of_idx[idx], "", "",
                              {"action": "attack", "success": False, "no_target": True,
                               "raw": e.get("response") or ""})
            return
        wolf = self._name(d.attack_votes[0][2]) if d.attack_votes else ""
        voted = self._name(d.attack_votes[0][3]) if d.attack_votes else ""
        for cols in d.attacks:
            tidx = int(cols[2])
            success = cols[3].strip().lower() == "true"
            target = self._name(cols[2]) if tidx > 0 else ""
            extra: dict[str, Any] = {"action": "attack", "success": success and tidx > 0, "no_target": tidx <= 0}
            if voted and voted != target:
                extra["voted"] = voted
            self._row(day, None, "action", wolf, target, target, extra)

    def result(self, day: int, cols: list[str]) -> None:
        if len(cols) >= 5:
            villagers, werewolves, side = int(cols[2]), int(cols[3]), cols[4]
        else:
            villagers = werewolves = None
            side = cols[2].removesuffix("_WIN") if len(cols) > 2 else None
        winner = normalize_winner(side)
        extra: dict[str, Any] = {"winner": winner}
        if villagers is not None:
            extra["villagers"] = villagers
            extra["werewolves"] = werewolves
        self._row(day, None, "result", "", "", winner, extra)

    def run(self) -> list[LogRow]:
        for day, d in self.days.items():
            for cols in d.status:
                self.status(day, cols)
            for cols in d.talks:
                self.talk(day, cols)
            targets = self.votes(day, d) if (d.votes or self._requests(day, "VOTE")) else []
            if d.execute:
                self.execute(day, d.execute, targets)
            self.divines(day, d)
            self.attack(day, d)
            if d.result:
                self.result(day, d.result)
        return self.rows


def convert(csv_text: str, server_json: dict[str, Any] | None, ctx: GameContext) -> list[LogRow]:
    """Convert a Go server game log (+ optional JSON log) into common rows (seq assigned 0..n-1)."""
    return _Converter(csv_text, server_json, ctx).run()


__all__ = ["context_from_log", "convert", "log_names", "parse_csv"]
