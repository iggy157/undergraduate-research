"""The game loop shared by all domains (IMPLEMENTATION_NOTES §3, DESIGN §4.5 / §5).

Request sequence: NAME (lobby) -> INITIALIZE -> per round [DAILY_INITIALIZE -> TALK x <=4 turns
-> (VOTE) -> (DIVINE / ATTACK / INVESTIGATE) -> DAILY_FINISH] -> FINISH.
Every packet is answered by the agent; notices are answered with "Acknowledged.".
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from common.conditions import parse_condition
from common.logwriter import GameLogWriter, read_jsonl
from common.protocol import T_OVER, Info, Request, Setting, Talk, Vote
from common.render import make_env
from common.scenario import find_scenario_deviations
from common.setup import DATA, N_SEATS, GameContext
from common.tiebreak import Tally, tally
from common.violations import find_truncations, find_violations

from .domain import DomainLogic, make_logic
from .parse import classify_talk, normalize
from .transport import Disconnected, SeatConnection

log = logging.getLogger("server.game")

PIPELINE = "server"
DEFAULT_CONDITION = "multi-private"
REMAIN_SKIP = 99
_INFO_FIELDS = frozenset(Info.__dataclass_fields__)
# chronological order of the requests inside one round (merge of the agents' llm_call records)
_PHASE_ORDER = {"TALK": 0, "VOTE": 1, "DIVINE": 2, "INVESTIGATE": 2, "ATTACK": 3}


def sanitize_model_tag(model: str) -> str:
    """Last path element of a model name with ``[^A-Za-z0-9.-]`` replaced by ``-`` (§2)."""
    last = str(model).rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9.-]", "-", last) or "model"


def make_game_id(setup_id: str, model_tag: str, now: _dt.datetime | None = None, condition: str = DEFAULT_CONDITION) -> str:
    """``<setup>__<condition tag>__<model_tag>__<ts>`` (common.conditions)."""
    ts = (now or _dt.datetime.now()).strftime("%Y%m%dT%H%M%S")
    parse_condition(condition)
    return f"{setup_id}__{condition}__{model_tag}__{ts}"


def _now_iso() -> str:
    """tz-aware UTC ISO string (same form in the single method)."""
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def persona_profile(ctx: GameContext, seat: int) -> str:
    """The four persona lines sent as ``info.profile`` (no private seed: that is in the agent's identity)."""
    p = ctx.persona_of_name(ctx.name_of_seat(seat))
    return f"Name: {p.name}\nAge: {p.age}\nGender: {p.gender}\nPersonality: {p.personality}"


class GameAbort(Exception):
    """Raised inside the loop to stop the game (disconnect / notice timeout)."""


class Game:
    def __init__(self, ctx: GameContext, conns: dict[int, SeatConnection], log_dir: str | Path,
                 model_tag: str = "scripted", timeout: float = 600.0, game_id: str | None = None,
                 model: str | None = None,
                 header_extra: dict[str, Any] | None = None, condition: str = DEFAULT_CONDITION,
                 scenario: dict[str, Any] | None = None, scenario_info: dict[str, Any] | None = None):
        if set(conns) != set(range(1, N_SEATS + 1)):
            raise ValueError(f"need connections for seats 1..{N_SEATS}, got {sorted(conns)}")
        self.ctx = ctx
        self.conns = conns
        self.timeout = float(timeout)
        self.model_tag = model_tag
        self.header_extra = dict(header_extra or {})  # sampling / model_info from the runner (DESIGN §3.2)
        self.model = model if model else model_tag  # full model name as in config/models.yml
        self.names = ctx.names
        self.condition = str(condition or DEFAULT_CONDITION)
        self.axes = parse_condition(self.condition)
        self.scenario = scenario          # the plan the agents were given (deviations are recorded, DESIGN §13)
        self.scenario_info = dict(scenario_info or {})
        self.game_id = game_id or make_game_id(ctx.setup.setup_id, model_tag, condition=self.condition)
        self.game_dir = Path(log_dir) / ctx.domain / self.axes["dir"] / self.game_id
        (self.game_dir / "raw").mkdir(parents=True, exist_ok=True)
        self.writer = GameLogWriter(self.game_dir, self.game_id, self.names)
        self.env = make_env()
        self.alive: dict[int, bool] = {s: True for s in range(1, N_SEATS + 1)}
        self.talks: list[Talk] = []
        self._delivered: dict[int, int] = {s: 0 for s in range(1, N_SEATS + 1)}
        self._round_talk_idx = 0
        self.vote_lists: dict[int, list[Vote]] = {}
        self.turns_per_round = int(ctx.rules["turns_per_round"])
        self.logic: DomainLogic = make_logic(ctx.domain, self)
        self.round = self.logic.first_round
        self.started_at = _now_iso()
        self.finished_at: str | None = None
        self.aborted = False
        self.outcome: dict[str, Any] | None = None

    # ---- seat helpers --------------------------------------------------------------------
    def name(self, seat: int) -> str:
        return self.ctx.name_of_seat(seat)

    def seat(self, name: str) -> int:
        return self.ctx.seat_of_name(name)

    def role(self, seat: int) -> str:
        return self.ctx.role_of_seat(seat)

    def seats(self) -> list[int]:
        return list(range(1, N_SEATS + 1))

    def living_seats(self) -> list[int]:
        return [s for s in self.seats() if self.alive[s]]

    def living_names(self) -> list[str]:
        return [self.name(s) for s in self.living_seats()]

    def kill(self, name: str) -> None:
        self.alive[self.seat(name)] = False

    def status_map(self) -> dict[str, str]:
        return {self.name(s): ("ALIVE" if self.alive[s] else "DEAD") for s in self.seats()}

    def full_role_map(self) -> dict[str, str]:
        return {self.name(s): self.role(s) for s in self.seats()}

    # ---- packets -------------------------------------------------------------------------
    def diff(self, seat: int) -> list[Talk]:
        """Talks not yet delivered to ``seat`` (the Go server's per-agent talk_history diff)."""
        out = self.talks[self._delivered[seat]:]
        self._delivered[seat] = len(self.talks)
        return out

    def setting(self) -> Setting:
        s = Setting()
        s.agent_count = N_SEATS
        s.max_day = self.logic.last_round
        s.role_num_map = {slot: int(spec["count"]) for slot, spec in self.ctx.roles.items()}
        s.talk["max_count"] = {"per_agent": self.turns_per_round, "per_day": self.turns_per_round * N_SEATS}
        s.talk["max_skip"] = REMAIN_SKIP
        s.vote["allow_self_vote"] = bool(self.ctx.rules.get("allow_self_vote"))
        ms = int(self.timeout * 1000)
        s.timeout = {"action": ms, "response": ms}
        return s

    def packet(self, request: Request, seat: int, round_no: int, *, with_setting: bool = False,
               **info_extra: Any) -> dict[str, Any]:
        name = self.name(seat)
        fields: dict[str, Any] = {
            "game_id": self.game_id, "day": round_no, "agent": name,
            "status_map": self.status_map(), "role_map": {name: self.role(seat)},
        }
        raw_extra: dict[str, Any] = {}
        for k, v in info_extra.items():
            if k in _INFO_FIELDS:
                fields[k] = v
            else:
                raw_extra[k] = v
        info = Info(**fields).to_dict()
        info.update({k: v for k, v in raw_extra.items() if v is not None})
        return {
            "request": str(request),
            "info": info,
            "setting": self.setting().to_dict() if with_setting else None,
            "talk_history": [t.to_dict() for t in self.diff(seat)],
            "whisper_history": [],
        }

    async def ask(self, seat: int, pkt: dict[str, Any]) -> str | None:
        """Send and wait. None on timeout; GameAbort on disconnect."""
        try:
            return await self.conns[seat].ask(pkt, self.timeout)
        except Disconnected:
            raise GameAbort(f"disconnect:{self.name(seat)}") from None

    async def ask_many(self, packets: dict[int, dict[str, Any]]) -> dict[int, str | None]:
        seats = list(packets)
        replies = await asyncio.gather(*(self.ask(s, packets[s]) for s in seats))
        return dict(zip(seats, replies))

    async def notify(self, request: Request, round_no: int, best_effort: bool = False) -> None:
        """Send a notice to every seat (dead ones too) and wait for the acknowledgements."""
        packets: dict[int, dict[str, Any]] = {}
        for seat in self.seats():
            if request == Request.INITIALIZE:
                extra = {"profile": persona_profile(self.ctx, seat), **self.logic.init_info(seat)}
                packets[seat] = self.packet(request, seat, round_no, with_setting=True, **extra)
            elif request == Request.DAILY_INITIALIZE:
                packets[seat] = self.packet(request, seat, round_no, **self.logic.daily_init_info(seat, round_no))
            elif request == Request.FINISH:
                packets[seat] = self.packet(request, seat, round_no, **self.logic.finish_info(seat))
            else:
                packets[seat] = self.packet(request, seat, round_no)

        async def one(seat: int) -> None:
            reply = await self.ask(seat, packets[seat])
            if reply is None:
                raise GameAbort(f"timeout:{self.name(seat)}")

        if best_effort:
            await asyncio.gather(*(one(s) for s in self.seats()), return_exceptions=True)
        else:
            await asyncio.gather(*(one(s) for s in self.seats()))

    # ---- phases --------------------------------------------------------------------------
    def write_status(self, round_no: int) -> None:
        for seat in self.seats():
            self.writer.status(round_no, self.name(seat), seat, self.role(seat), self.alive[seat])

    async def talk_phase(self, round_no: int) -> None:
        self._round_talk_idx = 0
        over: set[int] = set()
        turns = self.turns_per_round
        for turn in range(1, turns + 1):
            for seat in self.ctx.setup.speaking_order:
                if not self.alive[seat] or seat in over:
                    continue
                name = self.name(seat)
                pkt = self.packet(Request.TALK, seat, round_no, remain_count=turns - turn + 1,
                                  remain_skip=REMAIN_SKIP)
                raw = await self.ask(seat, pkt)
                n = normalize(raw, name)
                kind, text, flags = n.kind, n.text, n.flags
                self.talks.append(Talk(self._round_talk_idx, round_no, turn, name, text,
                                       skip=(kind == "skip"), over=(kind == "over")))
                self._round_talk_idx += 1
                if kind == "talk":
                    extra: dict[str, Any] = {"norm": n.notes} if n.notes else {}
                    self.writer.talk(round_no, turn, name, text, raw=raw, **extra)
                    if n.over_after:  # "... Over." glued to the utterance: ends the round like a spoken Over
                        self.talks.append(Talk(self._round_talk_idx, round_no, turn, name, T_OVER, over=True))
                        self._round_talk_idx += 1
                        self.writer.pass_(round_no, turn, name, T_OVER, trailing=True)
                        over.add(seat)
                else:
                    extra = {"norm": n.notes} if n.notes else {}
                    if raw is None:
                        extra["timeout"] = True
                    elif raw.strip() != text:  # e.g. "skip." / "ForceSkip": keep what was said
                        extra["raw"] = raw.strip()
                    self.writer.pass_(round_no, turn, name, text, forced=flags.get("forced", False),
                                      empty=flags.get("empty", False), **extra)
                    if kind == "over":
                        over.add(seat)

    async def vote_phase(self, round_no: int) -> Tally:
        voters = [s for s in self.ctx.setup.speaking_order if self.alive[s]]
        # asked one seat after another in speaking order (= the order of the rows and the order the batch
        # writer uses) so that a writer view built live equals the one rebuilt from the log; seats never see
        # each other's vote anyway
        replies: dict[int, str | None] = {}
        for s in voters:
            replies[s] = await self.ask(s, self.packet(Request.VOTE, s, round_no))
        parsed = {s: self.logic.parse_vote(s, replies[s]) for s in voters}
        t = tally({self.name(s): parsed[s] for s in voters}, self.ctx.setup.setup_id, round_no)
        for s in voters:
            raw = replies[s]
            extra = {"tie": t.tie}
            if raw is None:
                extra["timeout"] = True
            self.writer.vote(round_no, self.name(s), parsed[s], raw if raw is not None else "",
                             parsed[s] is not None, request=self.logic.vote_request, **extra)
        self.vote_lists[round_no] = [Vote(round_no, self.name(s), parsed[s]) for s in voters if parsed[s]]
        return t

    # ---- main loop -----------------------------------------------------------------------
    async def run(self) -> dict[str, Any]:
        log.info("game %s starting (%s)", self.game_id, self.ctx.setup.setup_id)
        try:
            await self.notify(Request.INITIALIZE, self.logic.first_round)
            for round_no in self.logic.rounds():
                self.round = round_no
                self.write_status(round_no)
                await self.notify(Request.DAILY_INITIALIZE, round_no)
                await self.talk_phase(round_no)
                if self.logic.has_vote(round_no):
                    t = await self.vote_phase(round_no)
                    await self.logic.after_vote(round_no, t)
                if not self.logic.finished():
                    await self.logic.actions(round_no)
                await self.notify(Request.DAILY_FINISH, round_no)
                if self.logic.finished():
                    break
            if not self.logic.finished():
                self.logic.conclude()
        except GameAbort as e:
            log.error("game %s aborted: %s", self.game_id, e)
            self.aborted = True
            self.logic.abort(str(e))
        self.write_status(self.round + 1)
        self.logic.write_result()
        self.outcome = self.logic.outcome()
        await self.notify(Request.FINISH, self.round, best_effort=True)
        self.finished_at = _now_iso()
        self.finalize()
        log.info("game %s finished: %s", self.game_id, self.outcome)
        return self.outcome

    # ---- jsonl header + merge of the agents' llm_call records ----------------------------
    def header(self) -> dict[str, Any]:
        setup = self.ctx.setup
        participants = []
        for seat in self.seats():
            p = self.ctx.persona_of_name(self.name(seat))
            participants.append({
                "seat": seat, "name": p.name, "role_slot": self.role(seat),
                "persona": {"name": p.name, "age": p.age, "gender": p.gender, "personality": p.personality},
                "private_seed": self.logic.private_seed(seat),
            })
        rules_hash = hashlib.sha1((DATA / self.ctx.domain / "rules.yml").read_bytes()).hexdigest()
        h: dict[str, Any] = {
            "setup_id": setup.setup_id, "domain": self.ctx.domain, "method": self.axes["method"],
            "pipeline": PIPELINE, "condition": self.condition,
            "model": self.model, "model_tag": self.model_tag, "info_mode": setup.info_mode,
            "setup_path": self.ctx.setup_path_str(), "setup_sha1": self.ctx.setup_sha1(),
            "started_at": self.started_at, "finished_at": self.finished_at,
            "participants": participants, "speaking_order": list(setup.speaking_order),
            "option_perm": list(setup.option_perm) if setup.option_perm else None,
        }
        h.update(self.logic.header_fields())
        h["axes"] = {k: v for k, v in self.axes.items() if k in ("method", "generation", "information", "plan")}
        h["scenario"] = self.scenario_info or None
        h["outcome"] = self.outcome
        h["rules_hash"] = rules_hash
        h.update(self.header_extra)
        return h

    def finalize(self) -> None:
        """header, merged llm_call records, then the ``violations`` record (DESIGN §3.2 / §8)."""
        self.writer.header(**self.header())
        merged = self.merge_agent_jsonl()
        items = find_violations(self.writer.rows, self.ctx) + find_truncations(merged)
        if self.scenario is not None:
            items += find_scenario_deviations(self.writer.rows, self.ctx, self.scenario)
        self.writer.record("violations", items=items)
        self.writer.close()

    def _merge_key(self, rec: dict[str, Any]) -> tuple:
        """Chronological key: (round, phase TALK<VOTE<DIVINE/INVESTIGATE<ATTACK, turn, speaking
        position for TALK else seat), then the agent's wall-clock ``ts`` and its own counter."""
        rnd = rec.get("round")
        rnd = int(rnd) if isinstance(rnd, (int, float)) else 1 << 30
        phase = _PHASE_ORDER.get(str(rec.get("request")), 9)
        turn = rec.get("turn")
        turn = int(turn) if isinstance(turn, (int, float)) else 0
        seat = rec.get("seat")
        seat = int(seat) if isinstance(seat, (int, float)) else 0
        order = list(self.ctx.setup.speaking_order)
        pos = order.index(seat) if (phase == 0 and seat in order) else seat
        seq = rec.get("seq")
        seq = int(seq) if isinstance(seq, (int, float)) else 1 << 30
        return (rnd, phase, turn, pos, str(rec.get("ts") or ""), seq)

    def merge_agent_jsonl(self) -> list[dict[str, Any]]:
        """Append raw/agent.*.jsonl records to <game_id>.jsonl in game order.

        The agents' own per-seat counter is kept as ``seat_seq``; ``seq`` is reassigned 0..n-1 over the
        merged, chronologically sorted records. Returns the records as written."""
        records: list[dict[str, Any]] = []
        for p in sorted((self.game_dir / "raw").glob("agent.*.jsonl")):
            try:
                records.extend(read_jsonl(p))
            except (OSError, ValueError) as e:
                log.warning("cannot read %s: %s", p, e)
        records.sort(key=self._merge_key)
        out: list[dict[str, Any]] = []
        for i, rec in enumerate(records):
            rec = dict(rec)
            kind = rec.pop("kind", "llm_call")
            seat_seq = rec.pop("seq", None)
            rec = {"seq": i, "seat_seq": seat_seq, **rec}
            self.writer.record(kind, **rec)
            out.append({"kind": kind, **rec})
        return out


__all__ = ["DEFAULT_CONDITION", "PIPELINE", "Game", "GameAbort", "make_game_id", "persona_profile", "sanitize_model_tag"]
