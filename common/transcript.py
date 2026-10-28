"""One transcript grammar for both methods (DESIGN §7.4, 2026-10-27).

The single writer generates the *writer view* (everything, Markdown); the multi agent rebuilds the
*seat view* (what that seat knows so far, same grammar) before every request and continues it with its
own line. ``render_writer_view`` / ``render_seat_view`` produce the same text from the common log rows,
so an agent's user message can be checked byte for byte against the log (tests, distillation data).

Grammar (one line each):
  # <setup_id>
  ## <Period> <n>
  ### Findings | ### Options            (seat view, discussion: told at the start of the round)
  ### Talk / #### Turn <t> of <n> / - **Name**: text | Skip | Over
  ### Vote / - Voter -> Target / - execution: Name | no one / - adopted: Label
  ### Action / - divine: Seer -> Target (human|werewolf) | - divine: Seer -> none
             / - attack: Wolf -> Target | none / - attacked: Target | no one   (seat view, public)
             / - investigate: Name -> title; title | none
  ## Result / - winner: village|werewolves / - adopted: Label
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .schema import LogRow
from .setup import GameContext

NONE = "none"
NO_ONE = "no one"


# ---- line formatters ----------------------------------------------------------------------------
def game_heading(setup_id: str) -> str:
    return f"# {setup_id}"


def period_heading(period: str, n: int) -> str:
    return f"## {period.capitalize()} {n}"


def turn_heading(t: int, n: int) -> str:
    return f"#### Turn {t} of {n}"


def talk_line(name: str, text: str) -> str:
    return f"- **{name}**: {text}"


def vote_line(voter: str, target: str) -> str:
    return f"- {voter} -> {target}"


def execution_line(name: str | None) -> str:
    return f"- execution: {name or NO_ONE}"


def adopted_line(label: str | None) -> str:
    return f"- adopted: {label or NO_ONE}"


def divine_line(seer: str, target: str | None, result: str | None) -> str:
    if not target:
        return f"- divine: {seer} -> {NONE}"
    return f"- divine: {seer} -> {target} ({str(result).lower()})" if result else f"- divine: {seer} -> {target}"


def attack_line(wolf: str, target: str | None) -> str:
    return f"- attack: {wolf} -> {target or NONE}"


def attacked_line(target: str | None) -> str:
    return f"- attacked: {target or NO_ONE}"


def investigate_line(name: str, titles: Iterable[str]) -> str:
    ts = [t for t in titles if t]
    return f"- investigate: {name} -> " + ("; ".join(ts) if ts else NONE)


def finding_line(title: str, text: str) -> str:
    return f"- {title}: {text}" if title else f"- {text}"


def option_line(o: dict[str, Any]) -> str:
    return f"- {o['label']}: {o['name']}. {o['summary']}"


def winner_line(winner: str) -> str:
    return f"- winner: {winner}"


# ---- the seat view, built incrementally (agent) or from log rows (tests / replay) ----------------
@dataclass
class _Period:
    turns: dict[int, list[str]] = field(default_factory=dict)   # turn -> talk/pass lines
    findings: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    votes: list[str] = field(default_factory=list)
    execution: str | None = None       # execution / adopted line
    actions: list[str] = field(default_factory=list)
    action_keys: list[str] = field(default_factory=list)   # parallel to actions (upsert_action)


@dataclass
class SeatTranscript:
    """What one seat knows, rendered in the common grammar. ``seat`` None = writer view (everything)."""
    ctx: GameContext
    seat: int | None
    periods: dict[int, _Period] = field(default_factory=dict)
    result: str | None = None
    _seen: set[tuple[int, int]] = field(default_factory=set)

    @property
    def name(self) -> str | None:
        return self.ctx.name_of_seat(self.seat) if self.seat is not None else None

    @property
    def period_name(self) -> str:
        return str(self.ctx.rules["period_name"])

    @property
    def turns_per_round(self) -> int:
        return int(self.ctx.rules["turns_per_round"])

    def period(self, n: int) -> _Period:
        return self.periods.setdefault(int(n), _Period())

    def ensure_turn(self, n: int, t: int) -> None:
        self.period(n).turns.setdefault(int(t), [])

    # -- talks (from packets: idx is unique within a round) --
    def add_talk(self, day: int, idx: int, turn: int, agent: str, text: str, skip: bool = False,
                 over: bool = False) -> None:
        key = (int(day), int(idx))
        if key in self._seen:
            return
        self._seen.add(key)
        shown = str(self.ctx.rules["pass_skip"]) if skip else str(self.ctx.rules["pass_over"]) if over else text
        self.period(day).turns.setdefault(int(turn), []).append(talk_line(agent, shown))

    # -- votes / results --
    def set_votes(self, n: int, votes: Iterable[tuple[str, str]]) -> None:
        self.period(n).votes = [vote_line(a, b) for a, b in votes]

    def set_own_vote(self, n: int, target: str) -> None:
        """Provisional: the seat's own vote until the full list arrives."""
        p = self.period(n)
        if not p.votes and self.name:
            p.votes = [vote_line(self.name, target)]

    def add_vote(self, n: int, voter: str, target: str) -> None:
        """Writer view: every vote as it is made (one line per voter, in the order made)."""
        p = self.period(n)
        prefix = f"- {voter} ->"
        if not any(v.startswith(prefix + " ") for v in p.votes):
            p.votes.append(vote_line(voter, target))

    def upsert_action(self, n: int, key: str, line: str) -> None:
        """Writer view: one action line per (seat, kind), replaced in place when its result arrives."""
        p = self.period(n)
        if key in p.action_keys:
            p.actions[p.action_keys.index(key)] = line
        else:
            p.action_keys.append(key)
            p.actions.append(line)

    def section_open(self, n: int, section: str) -> bool:
        """Whether the ``### Vote`` / ``### Action`` section of period ``n`` is already rendered (so a label
        continues it instead of opening it)."""
        p = self.periods.get(int(n))
        if p is None:
            return False
        return bool(p.votes or p.execution) if section == "vote" else bool(p.actions)

    def set_execution(self, n: int, name: str | None) -> None:
        self.period(n).execution = execution_line(name)

    def set_adopted(self, n: int, label: str | None) -> None:
        self.period(n).execution = adopted_line(label)

    def set_actions(self, n: int, lines: list[str]) -> None:
        self.period(n).actions = list(lines)

    def set_findings(self, n: int, cards: Iterable[dict[str, Any]]) -> None:
        self.period(n).findings = [finding_line(str(c.get("title") or ""), str(c["text"])) for c in cards]

    def set_options(self, n: int, options: Iterable[dict[str, Any]]) -> None:
        self.period(n).options = [option_line(o) for o in options]

    # -- render --
    def render(self) -> str:
        out = [game_heading(self.ctx.setup.setup_id)]
        for n in sorted(self.periods):
            p = self.periods[n]
            out.append(period_heading(self.period_name, n))
            if p.findings:
                out.append("### Findings")
                out.extend(p.findings)
            if p.options:
                out.append("### Options")
                out.extend(p.options)
            out.append("### Talk")
            for t in sorted(p.turns):
                out.append(turn_heading(t, self.turns_per_round))
                out.extend(p.turns[t])
            if p.votes or p.execution:
                out.append("### Vote")
                out.extend(p.votes)
                if p.execution:
                    out.append(p.execution)
            if p.actions:
                out.append("### Action")
                out.extend(p.actions)
        if self.result:
            out.append("## Result")
            out.append(self.result)
        return "\n".join(out)


# ---- views from log rows -------------------------------------------------------------------------
def view_from_rows(rows: Iterable[LogRow], ctx: GameContext, seat: int | None = None,
                   upto_seq: int | None = None, ensure_turn: tuple[int, int] | None = None) -> SeatTranscript:
    """Seat view (``seat``) or writer view (None) of a logged game, from the rows with seq < upto_seq.

    What the seat knows is derived from the rows' *disclosure time*: talks as they happen; votes,
    execution, attack and the Seer's own result at the start of the next period (i.e. once any row of
    the next period exists, or at the end of the game); findings when the next round starts, the
    options when the last round starts (its status rows exist). The writer view (``seat`` None: the online
    and stepped writers) sees every vote / execution / action line as soon as its row exists, the divination
    result included (the writer knows every role, as the batch writer does when it writes the night). ``ensure_turn=(period, turn)`` adds the heading of the turn
    about to be spoken in (what the agent does before its own TALK).
    """
    rows = [r for r in rows if upto_seq is None or r.seq < upto_seq]
    v = SeatTranscript(ctx, seat)
    me = v.name
    aiwolf = ctx.domain == "aiwolf"
    last_round = int(ctx.rules["rounds_total"])
    last_period = max((r.round for r in rows), default=None)
    finished = any(r.type == "result" for r in rows)

    def disclosed(n: int) -> bool:  # results of period n are public once period n+1 has started
        return finished or (last_period is not None and last_period > n)

    for r in rows:
        n = r.round
        if r.type == "status":  # written at the start of every period
            v.period(n)
            if seat is not None and not aiwolf and n == last_round and not v.period(n).options:
                v.set_options(n, ctx.options())
        elif r.type in ("talk", "pass"):
            skip = r.type == "pass" and r.text == str(ctx.rules["pass_skip"])
            over = r.type == "pass" and r.text == str(ctx.rules["pass_over"])
            v.add_talk(n, r.seq, r.turn or 0, r.agent, r.text, skip=skip, over=over)
        elif r.type == "vote":
            if seat is None or disclosed(n):
                p = v.period(n)
                if r.target:
                    p.votes.append(vote_line(r.agent, r.target))
            elif r.agent == me:
                v.set_own_vote(n, r.target or r.extra.get("raw", ""))
        elif r.type == "action":
            a = r.extra.get("action")
            p = v.period(n)
            if a == "execute":
                if seat is None or disclosed(n):  # told at the start of the next period
                    p.execution = execution_line(r.target or None)
            elif a == "divine":
                if seat is None:  # the writer knows every role: the result is written with the action (as in batch)
                    p.actions.append(divine_line(r.agent, r.target or None, r.text or None))
                elif r.agent == me:  # the Seer is told the result the next morning
                    p.actions.append(divine_line(r.agent, r.target or None, (r.text or None) if disclosed(n) else None))
            elif a == "attack":
                if seat is None or r.agent == me:
                    p.actions.append(attack_line(r.agent, r.target or None))
                elif disclosed(n):
                    p.actions.append(attacked_line(r.target or None))
            elif a == "investigate":
                if seat is None and ctx.setup.info_mode == "fixed":
                    continue  # the writer never writes investigation lines in fixed mode (cards are assigned)
                if seat is None or r.agent == me:
                    by_id = {c["card_id"]: c for c in ctx.card_pool()}
                    cards = [by_id[i] for i in (r.extra.get("cards") or []) if i in by_id]
                    p.actions.append(investigate_line(r.agent, [c["title"] for c in cards]))
                    if seat is not None and disclosed(n):  # findings are told at the start of the next round
                        v.set_findings(n + 1, cards)
        elif r.type == "result":
            if aiwolf:
                v.result = winner_line(r.text)
            else:
                v.period(n).execution = adopted_line(r.text or None)  # "- adopted: X" closes the last Vote section
                v.result = adopted_line(r.text or None)
    if finished:  # the final status snapshot (period after the last one) is not part of the transcript
        last = max(r.round for r in rows if r.type == "result")
        for n in [n for n in v.periods if n > last]:
            p = v.periods[n]
            if not (p.turns or p.votes or p.execution or p.actions or p.findings or p.options):
                del v.periods[n]
    if ensure_turn is not None:
        v.ensure_turn(*ensure_turn)
    return v


__all__ = ["NONE", "NO_ONE", "SeatTranscript", "adopted_line", "attack_line", "attacked_line", "divine_line",
           "execution_line", "finding_line", "game_heading", "investigate_line", "option_line",
           "period_heading", "talk_line", "turn_heading", "view_from_rows", "vote_line", "winner_line"]
