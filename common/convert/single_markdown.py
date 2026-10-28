"""Single-writer Markdown transcript -> common log rows (DESIGN §7.2 grammar, §8 structural violations).

``convert(markdown, ctx, game_id)`` parses the transcript strictly, replays the game with the same
rules the multi server applies (talk order, Over, votes, tie-break, executions, divine/attack,
investigate, win condition, max day) and returns the row sequence the server would have written for
the same events, plus the structural violations found, plus the recomputed outcome.

Tolerances (only those DESIGN §8 allows): name case (``name_case``), ``Over.`` etc. (``pass_punct``),
a code fence around the whole document (stripped, ``format_noise``), bold variations such as
``**Name:**`` or a missing bold (``format_noise``). Everything else that deviates from the grammar is
recorded and dropped. The converter never raises: unparseable input yields ``rows=[]`` and one
``parse_error`` violation.

Violation codes (DESIGN §8 single-only): name_case, unknown_name, dup_turn, talk_after_over,
over_repeat (normalized), pass_after_over (normalized), missing_turn, dead_actor, order, extra_round, bad_card, vote_count, tally_mismatch,
tie_choice_differs, divine_mismatch; shared: pass_punct, format_noise. Converter-specific additions
(all structural): parse_error, missing_round, extra_turn, dup_vote, dup_action, missing_action,
extra_action, wrong_actor, participant_mismatch, result_mismatch.

Ties: when the writer's execution / adoption is one of the tied top candidates (``Tally.top``) but
not the one ``common.tiebreak`` picks, the writer's value is kept for the replay (so the rest of the
transcript is not judged against a player the writer did not kill) and ``tie_choice_differs`` is
recorded; the execute / result row carries ``tie: true`` and ``rule_choice: <tiebreak value>``.
Only a value that is not a top candidate (a real miscount) is overridden (``tally_mismatch``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..logwriter import count_words, find_mentions
from ..normalize import normalize_talk
from ..violations import NORMALIZED
from ..schema import WINNER_NONE, WINNER_VILLAGE, WINNER_WEREWOLF, LogRow, normalize_winner
from ..setup import N_SEATS, GameContext
from ..tiebreak import Tally, tally

SPECIES_HUMAN = "HUMAN"
SPECIES_WEREWOLF = "WEREWOLF"


@dataclass
class ConvertResult:
    rows: list[LogRow]
    violations: list[dict[str, Any]]
    outcome: dict[str, Any]


# ---- in-memory row builder (same calls / extras as common.logwriter.GameLogWriter) ---------------
class _Rows:
    def __init__(self, names: list[str]):
        self.names = list(names)
        self.rows: list[LogRow] = []

    def _row(self, round_no: int, turn: int | None, typ: str, agent: str, target: str, text: str,
             extra: dict[str, Any] | None) -> LogRow:
        row = LogRow(len(self.rows), round_no, turn, typ, agent, target, text, dict(extra or {}))
        self.rows.append(row)
        return row

    def status(self, round_no: int, agent: str, seat: int, role: str, alive: bool) -> LogRow:
        return self._row(round_no, None, "status", agent, "", "ALIVE" if alive else "DEAD",
                         {"seat": seat, "role": role, "alive": alive})

    def talk(self, round_no: int, turn: int, agent: str, text: str, raw: str | None = None,
             **extra: Any) -> LogRow:
        e = {"words": count_words(text), "mentions": find_mentions(text, self.names, exclude=agent),
             "raw_differs": (raw is not None and raw != text)}
        e.update(extra)
        return self._row(round_no, turn, "talk", agent, "", text, e)

    def pass_(self, round_no: int, turn: int, agent: str, token: str, forced: bool = False,
              empty: bool = False, **extra: Any) -> LogRow:
        return self._row(round_no, turn, "pass", agent, "", token, {"forced": forced, "empty": empty, **extra})

    def vote(self, round_no: int, agent: str, target: str | None, raw: str, valid: bool,
             request: str = "vote", **extra: Any) -> LogRow:
        return self._row(round_no, None, "vote", agent, target or "", "",
                         {"request": request, "raw": raw, "valid": valid, **extra})

    def action(self, round_no: int, action: str, agent: str, target: str, text: str,
               **extra: Any) -> LogRow:
        return self._row(round_no, None, "action", agent, target, text, {"action": action, **extra})

    def result(self, round_no: int, text: str, **extra: Any) -> LogRow:
        return self._row(round_no, None, "result", "", "", text, dict(extra))


# ---- parsed document ---------------------------------------------------------------------------
@dataclass
class _TalkLine:
    name: str
    text: str
    line: int


@dataclass
class _VoteLine:
    voter: str
    target: str
    line: int


@dataclass
class _ActionLine:
    kind: str          # divine | attack | investigate
    actor: str
    target: str        # name, or raw title list for investigate
    result: str | None  # divine: human|werewolf as written
    line: int


@dataclass
class _Round:
    number: int
    line: int
    turns: dict[int, list[_TalkLine]] = field(default_factory=dict)
    votes: list[_VoteLine] = field(default_factory=list)
    execution: tuple[str, int] | None = None
    adopted: tuple[str, int] | None = None
    actions: list[_ActionLine] = field(default_factory=list)
    has_vote_section: bool = False
    has_action_section: bool = False


@dataclass
class _Doc:
    title: str | None = None
    participants: list[tuple[str, str, str | None, int]] = field(default_factory=list)  # seat, name, role, line
    rounds: list[_Round] = field(default_factory=list)
    result: dict[str, tuple[str, int]] = field(default_factory=dict)  # winner|adopted -> (value, line)


_FENCE_RE = re.compile(r"^```[A-Za-z0-9_+-]*\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_ROUND_RE = re.compile(r"^(?P<period>[A-Za-z]+)\s+(?P<n>\d+)\s*[.:]?$")
_TURN_RE = re.compile(r"^turn\s+(?P<t>\d+)(?:\s+of\s+(?P<of>\d+))?\s*[.:]?$", re.IGNORECASE)
_SECTIONS = ("participants", "talk", "vote", "action", "result")
_ARROW = r"(?:->|→|=>|-->|—>)"
_TALK_CANON_RE = re.compile(r"^- \*\*(?P<name>[^*]+?)\*\*:(?: (?P<text>.*))?$")
_TALK_LOOSE_RE = re.compile(r"^[-*+]\s*(?:\*\*|__|\*|_)?\s*(?P<name>[A-Za-z][A-Za-z0-9_' .-]*?)\s*(?:\*\*|__|\*|_)?"
                            r"\s*:\s*(?:\*\*|__|\*|_)?\s*(?P<text>.*?)\s*(?:\*\*|__)?\s*$")
_KEYED_RE = re.compile(r"^[-*+]\s*(?:\*\*|__)?\s*(?P<key>execution|executed|adopted|winner|divine|attack|"
                       r"investigate)\s*(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(?P<val>.*?)\s*(?:\*\*|__)?\s*$", re.IGNORECASE)
_VOTE_RE = re.compile(r"^[-*+]\s*(?:\*\*|__)?\s*(?P<voter>[^*>→]+?)\s*(?:\*\*|__)?\s*" + _ARROW +
                      r"\s*(?:\*\*|__)?\s*(?P<target>.+?)\s*(?:\*\*|__)?\s*$")
_DIVINE_RE = re.compile(r"^(?P<a>[^>→(]+?)\s*" + _ARROW + r"\s*(?P<b>[^(]+?)\s*(?:\((?P<res>[^)]*)\))?\s*[.]?$")
_ARROW_RE = re.compile(r"^(?P<a>[^>→]+?)\s*" + _ARROW + r"\s*(?P<b>.*?)\s*$")
# reply normalisation identical to server/base/parse.py (classify_talk / match_name / match_option)
_PASS_RE = re.compile(r"^(?P<tok>skip|over)[\s.。!！]*$", re.IGNORECASE)
_EDGE_PUNCT = " \t\r\n.,!?;:。、！？\"'`“”‘’"
_LABEL_PREFIX_RE = re.compile(r"^(?:option|candidate)\s+", re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*(?:[-*•·]+|\d+[.)]|\(\d+\))\s*")
VOTE_REQUEST = {"aiwolf": "vote_day"}  # discussion domains: vote_final (server/base/domain.py)


def _strip_edges(s: str) -> str:
    return s.strip().strip(_EDGE_PUNCT).strip()


class _Converter:
    def __init__(self, ctx: GameContext, game_id: str):
        self.ctx = ctx
        self.game_id = game_id
        self.names = ctx.names
        self.lower = {n.lower(): n for n in self.names}
        self.rules = ctx.rules
        self.period = str(self.rules["period_name"]).lower()
        self.turns_per_round = int(self.rules["turns_per_round"])
        self.first_round = int(self.rules["first_round"])
        self.rounds_total = int(self.rules["rounds_total"])
        self.pass_skip = str(self.rules["pass_skip"])
        self.pass_over = str(self.rules["pass_over"])
        self.vote_request = VOTE_REQUEST.get(ctx.domain, "vote_final")
        self.violations: list[dict[str, Any]] = []
        self.rows = _Rows(self.names)
        self.outcome: dict[str, Any] = {}

    # ---- bookkeeping ---------------------------------------------------------------------------
    def v(self, code: str, detail: str, line: int | None = None, seq: int | None = None,
          kind: str | None = None) -> None:
        item: dict[str, Any] = {"seq": seq, "line": line, "code": code, "detail": detail}
        if kind is not None:
            item["kind"] = kind
        self.violations.append(item)

    def resolve(self, raw: str, line: int | None) -> str | None:
        """Exact name, or case-insensitive match (records name_case), else None (records unknown_name)."""
        s = raw.strip().strip("*_").strip()
        if s in self.lower.values():
            return s
        n = self.lower.get(s.lower())
        if n is not None:
            self.v("name_case", f"{s!r} -> {n}", line)
            return n
        self.v("unknown_name", s, line)
        return None

    def species(self, name: str) -> str:
        return SPECIES_WEREWOLF if self.ctx.role_of_name(name) == "WEREWOLF" else SPECIES_HUMAN

    # ---- parsing -------------------------------------------------------------------------------
    def parse(self, markdown: str) -> _Doc:
        lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        # whole-document code fence
        nonblank = [i for i, l in enumerate(lines) if l.strip()]
        if len(nonblank) >= 2 and _FENCE_RE.match(lines[nonblank[0]].strip()) \
                and lines[nonblank[-1]].strip() == "```":
            lines[nonblank[0]] = ""
            lines[nonblank[-1]] = ""
            self.v("format_noise", "code fence around the document", nonblank[0] + 1)
        doc = _Doc()
        section: str | None = None
        cur: _Round | None = None
        cur_turn: int | None = None
        for no, raw in enumerate(lines, 1):
            s = raw.strip()
            if not s:
                continue
            hm = _HEADING_RE.match(s)
            if hm:
                level, text = len(hm.group(1)), hm.group(2).strip()
                low = text.lower().rstrip(".:")
                if low in _SECTIONS:
                    if low == "participants":
                        section = "participants"
                        if level != 2:
                            self.v("format_noise", f"heading level {level} for Participants", no)
                    elif low == "result":
                        section = "result"
                        cur, cur_turn = None, None
                        if level != 2:
                            self.v("format_noise", f"heading level {level} for Result", no)
                    else:
                        if cur is None:
                            self.v("format_noise", f"'{text}' section outside a round", no)
                            section = None
                        else:
                            section = low
                            cur_turn = None
                            if low == "vote":
                                cur.has_vote_section = True
                            elif low == "action":
                                cur.has_action_section = True
                            if level != 3:
                                self.v("format_noise", f"heading level {level} for {text}", no)
                    continue
                tm = _TURN_RE.match(text)
                if tm:
                    if cur is None:
                        self.v("format_noise", f"turn heading outside a round: {text!r}", no)
                        continue
                    if section != "talk":
                        self.v("format_noise", f"turn heading outside Talk: {text!r}", no)
                        section = "talk"
                    if level != 4 or tm.group("of") is None or int(tm.group("of")) != self.turns_per_round:
                        self.v("format_noise", f"turn heading {text!r}", no)
                    cur_turn = int(tm.group("t"))
                    cur.turns.setdefault(cur_turn, [])
                    continue
                rm = _ROUND_RE.match(text)
                if rm and rm.group("period").lower() in ("day", "round"):
                    if rm.group("period").lower() != self.period:
                        self.v("format_noise", f"period word {rm.group('period')!r} (expected {self.period})", no)
                    if level != 2:
                        self.v("format_noise", f"heading level {level} for {text!r}", no)
                    cur = _Round(int(rm.group("n")), no)
                    doc.rounds.append(cur)
                    section, cur_turn = None, None
                    continue
                if level == 1 and doc.title is None and cur is None:
                    doc.title = text
                    if text != self.ctx.setup.setup_id:
                        self.v("format_noise", f"title {text!r} != setup_id", no)
                    continue
                self.v("format_noise", f"unknown heading {s!r}", no)
                continue
            if section == "participants":
                if s.startswith("|"):
                    cells = [c.strip() for c in s.strip("|").split("|")]
                    if not cells or cells[0].lower() == "seat" or all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                        continue
                    if len(cells) < 2:
                        self.v("format_noise", f"participants row {s!r}", no)
                        continue
                    doc.participants.append((cells[0], cells[1], cells[2] if len(cells) > 2 else None, no))
                else:
                    self.v("format_noise", f"unexpected line in Participants: {s!r}", no)
                continue
            km = _KEYED_RE.match(s)
            if km:
                key, val = km.group("key").lower(), km.group("val")
                if key in ("execution", "executed"):
                    if cur is None:
                        self.v("format_noise", f"execution line outside a round: {s!r}", no)
                    else:
                        if section != "vote":
                            self.v("format_noise", f"execution line outside Vote: {s!r}", no)
                        if cur.execution is None:
                            cur.execution = (val, no)
                        else:
                            self.v("dup_vote", f"second execution line {s!r}", no)
                elif key == "adopted":
                    if section == "result" or cur is None:
                        if "adopted" in doc.result:
                            self.v("format_noise", f"second Result line {s!r}", no)
                        else:
                            doc.result["adopted"] = (val, no)
                    else:
                        if section != "vote":
                            self.v("format_noise", f"adopted line outside Vote: {s!r}", no)
                        if cur.adopted is None:
                            cur.adopted = (val, no)
                        else:
                            self.v("dup_vote", f"second adopted line {s!r}", no)
                elif key == "winner":
                    if section != "result":
                        self.v("format_noise", f"winner line outside Result: {s!r}", no)
                    if "winner" in doc.result:
                        self.v("format_noise", f"second Result line {s!r}", no)
                    else:
                        doc.result["winner"] = (val, no)
                else:  # divine | attack | investigate
                    if cur is None:
                        self.v("format_noise", f"action line outside a round: {s!r}", no)
                        continue
                    if section != "action":
                        self.v("format_noise", f"action line outside Action: {s!r}", no)
                    if key == "divine":
                        dm = _DIVINE_RE.match(val)
                        if not dm:
                            self.v("format_noise", f"unparseable divine line {s!r}", no)
                            continue
                        res = dm.group("res")
                        if res is None:
                            self.v("format_noise", f"divine line without result {s!r}", no)
                        cur.actions.append(_ActionLine("divine", dm.group("a"), dm.group("b"), res, no))
                    else:
                        am = _ARROW_RE.match(val)
                        if not am:
                            self.v("format_noise", f"unparseable {key} line {s!r}", no)
                            continue
                        cur.actions.append(_ActionLine(key, am.group("a"), am.group("b"), None, no))
                continue
            tc = _TALK_CANON_RE.match(s)
            if tc:
                if cur is None or section != "talk" or cur_turn is None:
                    self.v("format_noise", f"talk line outside a turn: {s!r}", no)
                    continue
                cur.turns[cur_turn].append(_TalkLine(tc.group("name"), (tc.group("text") or "").strip(), no))
                continue
            vm = _VOTE_RE.match(s)
            if vm and section == "vote" and cur is not None:
                cur.votes.append(_VoteLine(vm.group("voter"), vm.group("target"), no))
                continue
            tl = _TALK_LOOSE_RE.match(s)
            if tl and section == "talk" and cur is not None and cur_turn is not None:
                self.v("format_noise", f"non-canonical talk line {s!r}", no)
                cur.turns[cur_turn].append(_TalkLine(tl.group("name"), tl.group("text").strip(), no))
                continue
            if section == "talk" and cur is not None and cur_turn is not None and cur.turns.get(cur_turn) \
                    and not s.startswith(("#", "- ", "|", "* ")):
                # a plain line inside a turn continues the previous utterance (multi-line utterances are
                # allowed in both methods; the server keeps the agent's newlines as well)
                last = cur.turns[cur_turn][-1]
                cur.turns[cur_turn][-1] = _TalkLine(last.name, (last.text + "\n" + s).strip(), last.line)
                continue
            self.v("format_noise", f"unrecognised line {s!r}", no)
        return doc

    # ---- cross-checks ----------------------------------------------------------------------------
    def check_participants(self, doc: _Doc) -> None:
        seen: set[int] = set()
        for seat_s, name_raw, role_raw, no in doc.participants:
            name = self.resolve(name_raw, no)
            if name is None:
                continue
            try:
                seat = int(seat_s)
            except ValueError:
                self.v("participant_mismatch", f"seat {seat_s!r} for {name}", no)
                continue
            seen.add(seat)
            if not 1 <= seat <= N_SEATS or self.ctx.name_of_seat(seat) != name:
                self.v("participant_mismatch", f"seat {seat} is not {name}", no)
                continue
            if self.ctx.domain == "aiwolf":
                true_role = self.ctx.role_of_name(name)
                if role_raw is None or role_raw.strip().upper() != true_role:
                    self.v("participant_mismatch", f"{name}: role {role_raw!r} != {true_role.capitalize()}", no)
        if doc.participants and seen != set(range(1, N_SEATS + 1)):
            self.v("participant_mismatch", f"seats listed: {sorted(seen)}")

    # ---- talk ----------------------------------------------------------------------------------
    def replay_talk(self, pr: _Round | None, round_no: int, alive: set[str]) -> None:
        order = [n for n in self.ctx.speaking_order_names if n in alive]
        over: set[str] = set()
        turns = pr.turns if pr is not None else {}
        for t in sorted(turns):
            if not 1 <= t <= self.turns_per_round:
                self.v("extra_turn", f"turn {t} in {self.period} {round_no}", pr.line if pr else None)
        for t in range(1, self.turns_per_round + 1):
            expected = [n for n in order if n not in over]
            kept: dict[str, _TalkLine] = {}
            for tl in turns.get(t, []):
                name = self.resolve(tl.name, tl.line)
                if name is None:
                    continue
                if name not in alive:
                    self.v("dead_actor", f"{name} talks in {self.period} {round_no} turn {t}", tl.line)
                    continue
                if name in over:
                    pm = _PASS_RE.match(tl.text)
                    tok = pm.group("tok").lower() if pm else None
                    if tok == self.pass_over.lower():      # "Over" written again: filler, dropped
                        self.v("over_repeat", f"{name} turn {t}", tl.line, kind=NORMALIZED)
                    elif tok == self.pass_skip.lower():    # "Skip" after Over: filler, dropped
                        self.v("pass_after_over", f"{name} turn {t}", tl.line, kind=NORMALIZED)
                    else:
                        self.v("talk_after_over", f"{name} turn {t}: {tl.text[:40]!r}", tl.line)
                    continue
                if name in kept:
                    self.v("dup_turn", f"{name} turn {t}", tl.line)
                    continue
                kept[name] = _TalkLine(name, tl.text, tl.line)
            written = [tl.name for tl in sorted(kept.values(), key=lambda x: x.line)]
            restored = [n for n in expected if n in kept]
            if written != restored:
                self.v("order", f"turn {t}: {written} -> {restored}", turns[t][0].line if turns.get(t) else None)
            for n in expected:
                if n not in kept:
                    self.v("missing_turn", f"{n} has no line in {self.period} {round_no} turn {t}",
                           pr.line if pr else None)
            for n in restored:
                tl = kept[n]
                # the same normalisation as the server applies to an agent's reply (common.normalize)
                nm = normalize_talk(tl.text, n, self.pass_skip, self.pass_over)
                extra: dict[str, Any] = {"norm": nm.notes} if nm.notes else {}
                if nm.kind != "talk":
                    if nm.flags.get("empty"):
                        extra.update(empty=True, raw="")
                    elif tl.text != nm.text:
                        extra["raw"] = tl.text
                    self.rows.pass_(round_no, t, n, nm.text, **extra)
                    if nm.kind == "over":
                        over.add(n)
                else:
                    self.rows.talk(round_no, t, n, nm.text, raw=tl.text, **extra)
                    if nm.over_after:  # "... Over." glued to the utterance: ends the round like a spoken Over
                        self.rows.pass_(round_no, t, n, self.pass_over, trailing=True)
                        over.add(n)

    # ---- votes ---------------------------------------------------------------------------------
    def replay_votes(self, pr: _Round | None, round_no: int, alive: set[str],
                     target_of: Any) -> tuple[dict[str, str | None], Tally]:
        """target_of(raw, line) -> (canonical target | None, valid). Returns (votes, tally)."""
        votes: dict[str, tuple[str | None, str, bool]] = {}
        if pr is None or not pr.has_vote_section:
            self.v("vote_count", f"no Vote section in {self.period} {round_no}", pr.line if pr else None)
        for vl in (pr.votes if pr else []):
            voter = self.resolve(vl.voter, vl.line)
            if voter is None:
                continue
            if voter not in alive:
                self.v("dead_actor", f"{voter} votes in {self.period} {round_no}", vl.line)
                continue
            if voter in votes:
                self.v("dup_vote", f"{voter} votes twice in {self.period} {round_no}", vl.line)
                continue
            target, valid = target_of(vl.target.strip(), vl.line)
            votes[voter] = (target, vl.target.strip(), valid)
        missing = [n for n in self.names if n in alive and n not in votes]
        if missing and (pr is not None and pr.has_vote_section):
            self.v("vote_count", f"{len(votes)}/{len(alive)} votes in {self.period} {round_no}; missing {missing}",
                   pr.line)
        counted = {n: (t if valid else None) for n, (t, _, valid) in votes.items()}
        tl = tally(counted, self.ctx.setup.setup_id, round_no)
        for n, (target, raw, valid) in votes.items():  # the order written (the server asks in speaking order)
            self.rows.vote(round_no, n, target if valid else None, raw, valid, request=self.vote_request, tie=tl.tie)
        return counted, tl

    # ---- aiwolf ----------------------------------------------------------------------------------
    def replay_aiwolf(self, doc: _Doc) -> None:
        rounds = self.first_rounds(doc)
        alive = set(self.names)
        day = self.first_round
        winner: str | None = None
        reason = ""
        used: set[int] = set()
        seer = next(n for n in self.names if self.ctx.role_of_name(n) == "SEER")
        wolf = next(n for n in self.names if self.ctx.role_of_name(n) == "WEREWOLF")
        while True:
            pr = rounds.get(day)
            if pr is None:
                self.v("missing_round", f"{self.period} {day} not written")
                if not any(k > day for k in rounds):
                    winner, reason = WINNER_NONE, "incomplete"
                    day -= 1
                    break
            else:
                used.add(day)
            self.status_rows(day, alive)
            self.replay_talk(pr, day, alive)
            if day >= 1:
                _, tl = self.replay_votes(pr, day, alive, lambda raw, line: self.vote_target_aiwolf(raw, line, alive))
                executed = tl.chosen
                written = None
                if pr is not None and pr.execution is not None:
                    written = self.resolve(pr.execution[0], pr.execution[1])
                ex_line = pr.execution[1] if pr and pr.execution else None
                ex_extra: dict[str, Any] = {}
                if written is not None and written != executed and written in tl.top:
                    self.v("tie_choice_differs", f"{self.period} {day}: execution written {written!r}, "
                           f"tie-break rule {executed!r}", ex_line)
                    ex_extra["rule_choice"] = executed
                    executed = written
                elif written != executed:
                    self.v("tally_mismatch", f"{self.period} {day}: execution written {written!r}, "
                           f"recomputed {executed!r}", ex_line)
                if executed is not None:
                    self.rows.action(day, "execute", "", executed, executed,
                                     role=self.ctx.role_of_name(executed), tie=tl.tie, **ex_extra)
                    alive.discard(executed)
                else:
                    self.rows.action(day, "execute", "", "", "", role="", tie=False, no_target=True)
                winner = self.aiwolf_winner(alive)
                if winner:
                    break
            elif pr is not None and pr.has_vote_section:
                self.v("format_noise", f"Vote section in {self.period} {day}", pr.line)
            # night
            actions = pr.actions if pr is not None else []
            divines = [a for a in actions if a.kind == "divine"]
            attacks = [a for a in actions if a.kind == "attack"]
            for a in actions:
                if a.kind not in ("divine", "attack"):
                    self.v("extra_action", f"{a.kind} in aiwolf", a.line)
            if seer in alive:
                self.replay_divine(divines, day, seer, alive)
            else:
                for a in divines:
                    self.v("dead_actor", "divine by a dead Seer", a.line)
            if day >= 1:
                if wolf in alive:
                    self.replay_attack(attacks, day, wolf, alive)
                else:
                    for a in attacks:
                        self.v("dead_actor", "attack by a dead Werewolf", a.line)
            else:
                for a in attacks:
                    self.v("extra_action", f"attack in {self.period} {day}", a.line)
            winner = self.aiwolf_winner(alive)
            if winner:
                break
            if day >= self.rounds_total:
                winner, reason = WINNER_NONE, "max_day"
                break
            day += 1
        for k in sorted(rounds):
            if k not in used:
                self.v("extra_round", f"{self.period} {k} after the game ended", rounds[k].line)
        # result
        wr = doc.result.get("winner")
        if wr is None:
            self.v("result_mismatch", "no winner line", None)
        elif normalize_winner(wr[0]) != winner or (winner == WINNER_NONE):
            self.v("result_mismatch", f"written {wr[0]!r}, recomputed {winner}", wr[1])
        if "adopted" in doc.result:
            self.v("format_noise", "adopted line in an aiwolf Result", doc.result["adopted"][1])
        humans = sum(1 for n in alive if self.species(n) == SPECIES_HUMAN)
        wolves = len(alive) - humans
        self.status_rows(day + 1, alive)
        # same keys as server/aiwolf/logic.py outcome(): reason is present (None) even when decided
        self.outcome = {"winner": winner, "villagers": humans, "werewolves": wolves, "reason": reason or None}
        self.rows.result(day, winner, **self.outcome)

    def aiwolf_winner(self, alive: set[str]) -> str | None:
        wolves = sum(1 for n in alive if self.species(n) == SPECIES_WEREWOLF)
        humans = len(alive) - wolves
        if wolves == 0:
            return WINNER_VILLAGE
        if wolves >= humans:
            return WINNER_WEREWOLF
        return None

    def vote_target_aiwolf(self, raw: str, line: int, alive: set[str]) -> tuple[str | None, bool]:
        """server/base/parse.match_name over the living names: case-insensitive, edge punctuation and '@'."""
        s = _strip_edges(raw.strip().strip("*_"))
        if s.startswith("@"):
            s = s[1:].strip()
        name = self.lower.get(s.lower())
        if name is None:
            return None, False
        if name != s:
            self.v("name_case", f"{s!r} -> {name}", line)
        return (name, True) if name in alive else (None, False)

    def replay_divine(self, divines: list[_ActionLine], day: int, seer: str, alive: set[str]) -> None:
        if not divines:
            self.v("missing_action", f"no divine line in {self.period} {day}")
            return
        chosen: _ActionLine | None = None
        for a in divines:
            actor = self.resolve(a.actor, a.line)
            if actor is None:
                continue
            if actor != seer:
                self.v("wrong_actor", f"divine by {actor} (Seer is {seer})", a.line)
                continue
            if chosen is not None:
                self.v("dup_action", f"second divine line in {self.period} {day}", a.line)
                continue
            chosen = a
        if chosen is None:
            self.v("missing_action", f"no valid divine line in {self.period} {day}")
            return
        target, valid = self.vote_target_aiwolf(chosen.target, chosen.line, alive)
        if valid and target == seer:
            valid, target = False, None
        if valid:
            true = self.species(target)
            written = (chosen.result or "").strip().upper()
            if written in ("HUMAN", "HUMANS"):
                written = SPECIES_HUMAN
            elif written in ("WEREWOLF", "WEREWOLVES", "WOLF"):
                written = SPECIES_WEREWOLF
            if written != true:
                self.v("divine_mismatch", f"{target}: written {chosen.result!r}, true {true}", chosen.line)
            self.rows.action(day, "divine", seer, target, true, result=true, valid=True)
        else:
            self.rows.action(day, "divine", seer, "", "", result="", valid=False, raw=chosen.target.strip())

    def replay_attack(self, attacks: list[_ActionLine], day: int, wolf: str, alive: set[str]) -> None:
        if not attacks:
            self.v("missing_action", f"no attack line in {self.period} {day}")
            return
        chosen: _ActionLine | None = None
        for a in attacks:
            actor = self.resolve(a.actor, a.line)
            if actor is None:
                continue
            if actor != wolf:
                self.v("wrong_actor", f"attack by {actor} (Werewolf is {wolf})", a.line)
                continue
            if chosen is not None:
                self.v("dup_action", f"second attack line in {self.period} {day}", a.line)
                continue
            chosen = a
        if chosen is None:
            self.v("missing_action", f"no valid attack line in {self.period} {day}")
            return
        target, valid = self.vote_target_aiwolf(chosen.target, chosen.line, alive)
        if valid and target == wolf:
            valid, target = False, None
        if valid:
            self.rows.action(day, "attack", wolf, target, target, success=True, no_target=False)
            alive.discard(target)
        else:
            self.rows.action(day, "attack", wolf, "", "", success=False, no_target=True, raw=chosen.target.strip())

    # ---- candidate_selection / shared_living -----------------------------------------------------
    def replay_discussion(self, doc: _Doc) -> None:
        rounds = self.first_rounds(doc)
        alive = set(self.names)
        labels = self.ctx.option_labels()
        used: set[int] = set()
        adopted: str | None = None
        tl: Tally | None = None
        result_extra: dict[str, Any] = {}
        complete = True
        last = self.first_round
        for r in range(self.first_round, self.rounds_total + 1):
            last = r
            pr = rounds.get(r)
            if pr is None:
                self.v("missing_round", f"{self.period} {r} not written")
                if not any(k > r for k in rounds):
                    complete = False
                    last = r - 1
                    break
            else:
                used.add(r)
            self.status_rows(r, alive)
            self.replay_talk(pr, r, alive)
            actions = pr.actions if pr is not None else []
            if r == self.first_round:
                self.replay_investigate(actions, r)
            else:
                for a in actions:
                    self.v("extra_action", f"{a.kind} in {self.period} {r}", a.line)
            if r == self.rounds_total:
                _, tl = self.replay_votes(pr, r, alive, lambda raw, line: self.vote_target_label(raw, labels))
                adopted = tl.chosen
                written = pr.adopted[0].strip() if pr is not None and pr.adopted is not None else None
                wlabel = self.label_of(written, labels) if written is not None else None
                ad_line = pr.adopted[1] if pr and pr.adopted else None
                if wlabel is not None and wlabel != adopted and wlabel in tl.top:
                    self.v("tie_choice_differs", f"adopted written {written!r}, tie-break rule {adopted!r}", ad_line)
                    result_extra["rule_choice"] = adopted
                    adopted = wlabel
                elif wlabel != adopted:
                    self.v("tally_mismatch", f"adopted written {written!r}, recomputed {adopted!r}", ad_line)
            elif pr is not None and (pr.has_vote_section or pr.adopted is not None):
                self.v("format_noise", f"Vote section in {self.period} {r}", pr.line)
        for k in sorted(rounds):
            if k not in used:
                self.v("extra_round", f"{self.period} {k} beyond {self.rounds_total}", rounds[k].line)
        wr = doc.result.get("adopted")
        if wr is None:
            self.v("result_mismatch", "no adopted line in Result", None)
        elif self.label_of(wr[0].strip(), labels) != adopted or adopted is None:
            self.v("result_mismatch", f"Result written {wr[0]!r}, recomputed {adopted!r}", wr[1])
        if "winner" in doc.result:
            self.v("format_noise", "winner line in a discussion Result", doc.result["winner"][1])
        self.status_rows(last + 1, alive)
        # same shape as server/candidate_selection/logic.py: result row at the last round, reason only on abort
        self.outcome = {"adopted": adopted, "tally": tl.counts if tl is not None else {},
                        "tie": bool(tl and tl.tie)}
        if not complete:
            self.outcome["reason"] = "incomplete"
        self.rows.result(self.rounds_total, adopted or "", **self.outcome, **result_extra)

    def label_of(self, raw: str, labels: list[str]) -> str | None:
        """server/base/parse.match_option: 'A', 'A.', 'Option A', 'Candidate A' or the option's full name."""
        s = _strip_edges(raw.strip().strip("*_"))
        s = _strip_edges(_LABEL_PREFIX_RE.sub("", s))
        if not s:
            return None
        for o in self.ctx.options():
            if s.lower() == str(o["label"]).lower() or s.lower() == str(o.get("name", "")).lower():
                return str(o["label"])
        return None

    def vote_target_label(self, raw: str, labels: list[str]) -> tuple[str | None, bool]:
        label = self.label_of(raw, labels)
        return (label, True) if label is not None else (None, False)

    def replay_investigate(self, actions: list[_ActionLine], r: int) -> None:
        if self.ctx.setup.info_mode == "fixed":
            for a in actions:
                self.v("extra_action", f"{a.kind} line in fixed mode", a.line)
            for seat in self.ctx.setup.speaking_order:  # same order as the server
                cards = [c for c in self.ctx.fixed_cards_of_seat(seat) if c]
                self.rows.action(r, "investigate", self.ctx.name_of_seat(seat), "", _titles_text(cards),
                                 cards=[c["card_id"] for c in cards], parse="fixed")
            return
        by_name: dict[str, _ActionLine] = {}
        for a in actions:
            if a.kind != "investigate":
                self.v("extra_action", f"{a.kind} in {self.ctx.domain}", a.line)
                continue
            actor = self.resolve(a.actor, a.line)
            if actor is None:
                continue
            if actor in by_name:
                self.v("dup_action", f"second investigate line for {actor}", a.line)
                continue
            by_name[actor] = a
        for name in self.names:
            if name not in by_name:
                self.v("missing_action", f"no investigate line for {name}")
        for name, a in by_name.items():  # the order written (the server asks in speaking order)
            # same matching as server/base/parse.parse_investigate (';'-separated here)
            by_title = {str(c["title"]).strip().lower(): c for c in self.ctx.card_pool() if c.get("title")}
            cards: list[dict[str, Any]] = []
            for part in a.target.split(";"):
                t = _BULLET_RE.sub("", part.strip().strip("*_")).strip().strip("\"'`“”‘’").strip()
                if not t:
                    continue
                c = by_title.get(t.lower()) or by_title.get(t.rstrip(".").strip().lower())
                if c is None:
                    self.v("bad_card", f"{name}: {t!r}", a.line)
                    continue
                if all(c["card_id"] != f["card_id"] for f in cards):
                    cards.append(c)
                if len(cards) >= self.choose:
                    break
            parse = "ok" if len(cards) >= self.choose else ("partial" if cards else "fail")
            extra: dict[str, Any] = {"cards": [c["card_id"] for c in cards], "parse": parse}
            if parse != "ok":
                extra["raw"] = a.target.strip()
            self.rows.action(r, "investigate", name, "", _titles_text(cards), **extra)

    # ---- helpers ---------------------------------------------------------------------------------
    @property
    def choose(self) -> int:
        slot = self.ctx.roles.get("PARTICIPANT", {}).get("action") or {}
        return int(slot.get("choose", 2))

    def first_rounds(self, doc: _Doc) -> dict[int, _Round]:
        out: dict[int, _Round] = {}
        for pr in doc.rounds:
            if pr.number in out:
                self.v("extra_round", f"duplicate {self.period} {pr.number}", pr.line)
            elif pr.number < self.first_round or pr.number > self.rounds_total:
                self.v("extra_round", f"{self.period} {pr.number} outside {self.first_round}..{self.rounds_total}",
                       pr.line)
            else:
                out[pr.number] = pr
        return out

    def status_rows(self, round_no: int, alive: set[str]) -> None:
        for s in self.ctx.setup.seats:
            self.rows.status(round_no, s.persona, s.seat, s.role_slot, s.persona in alive)

    # ---- entry -----------------------------------------------------------------------------------
    def run(self, markdown: str) -> ConvertResult:
        doc = self.parse(markdown or "")
        if not doc.rounds:
            return ConvertResult([], [{"seq": None, "line": None, "code": "parse_error",
                                       "detail": f"no '## {self.period.capitalize()} <n>' heading found"}], {})
        if doc.title is None:
            self.v("format_noise", "no '# <setup_id>' title")
        if doc.participants:  # optional (DESIGN §7.4: participants are in the system prompt); checked when present
            self.check_participants(doc)
        if self.ctx.domain == "aiwolf":
            self.replay_aiwolf(doc)
        else:
            self.replay_discussion(doc)
        return ConvertResult(self.rows.rows, self.violations, self.outcome)


def _titles_text(cards: list[dict[str, Any]]) -> str:
    # fixed mode may run on data whose titles are still empty (DESIGN §9-9): fall back to the id
    return "; ".join(c["title"] or c["card_id"] for c in cards)


def convert(markdown: str, ctx: GameContext, game_id: str) -> ConvertResult:
    """Parse a single-writer transcript. Never raises; garbage -> rows=[] + one ``parse_error``."""
    conv = _Converter(ctx, game_id)
    try:
        return conv.run(markdown)
    except Exception as e:  # noqa: BLE001 - the converter must never crash on model output
        return ConvertResult([], [{"seq": None, "line": None, "code": "parse_error",
                                   "detail": f"{type(e).__name__}: {e}"}], {})


__all__ = ["ConvertResult", "convert"]
