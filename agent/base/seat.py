"""One seat's state machine: packet -> reply string (IMPLEMENTATION_NOTES §3/§4, DESIGN §7.4 / §13).

``SeatAgent`` keeps the seat view of the transcript (common.transcript.SeatTranscript), rebuilds the user
message from it before every LLM call (messages are always ``[system, user]``), calls the injected
``LLMClient`` and appends ``llm_call`` records. Notices (INITIALIZE / DAILY_INITIALIZE / DAILY_FINISH /
FINISH) update the view and are answered with the static "Acknowledged." (no LLM call). Domain-specific
pieces are the hook methods overridden in agent/aiwolf and agent/base/discussion.

Conditions (common.conditions): ``reveal`` = multi-public (the system prompt shows all participants and the
hidden information); ``writer`` = single-online (one LLM writes every seat's line from the shared *writer view*;
the five seats of one game run in one process and share ``view`` + ``lock``); ``stepped`` = single-batch-stepped
(the single-batch system + user, the transcript so far as the assistant's own unfinished output, continued one
line per call; outcomes decided by the server); ``scenario`` = the ``## Plan`` block.
"""
from __future__ import annotations

import datetime as _dt
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any

from jinja2 import Environment

from common.conditions import condition_dir, multi_tag
from common.protocol import (
    ACK,
    ACTION_REQUESTS,
    NOTICE_REQUESTS,
    T_FORCE_SKIP,
    Info,
    Packet,
    Request,
    Status,
)
from common.setup import GameContext
from common.transcript import SeatTranscript

from .jsonl import RawJsonlWriter
from .llm import LLMClient, Message
from .prompts import (
    build_action_message,
    build_system_prompt,
    build_talk_message,
    build_vote_message,
    make_agent_env,
    rules_of,
)

LLM_CALL_FIELDS = ("seq", "seat", "request", "round", "turn", "ts", "messages", "response", "usage",
                   "finish_reason", "error", "truncated", "latency_ms")
MAX_TOKENS_KIND = {Request.TALK: "multi_talk", Request.VOTE: "multi_vote",
                   Request.DIVINE: "multi_action", Request.ATTACK: "multi_action",
                   Request.INVESTIGATE: "multi_action"}
_EDGE = re.compile(r"^[\s\"'`*_.,;:!?()\[\]-]+|[\s\"'`*_.,;:!?()\[\]-]+$")


def match_candidate(reply: str | None, candidates: list[str]) -> str | None:
    """The candidate the reply names (exact, then case-insensitive after trimming punctuation), else None.
    Used for the provisional own vote / action line of the view; the server's parse is the record."""
    if not reply:
        return None
    s = _EDGE.sub("", re.sub(r"\s*\([^)]*\)[\s.!]*$", "", reply.strip()).strip())  # "Shizue (werewolf)" -> Shizue
    if s in candidates:
        return s
    low = s.lower()
    for c in candidates:
        if c.lower() == low:
            return c
    return None


class SeatAgent:
    """Base agent. Subclasses override the hooks only."""

    def __init__(self, ctx: GameContext, seat: int, llm: LLMClient, log_dir: Path | str,
                 max_tokens: dict[str, int] | None = None, env: Environment | None = None,
                 stop_talk: list[str] | None = None, *, reveal: bool = False, writer: bool = False,
                 stepped: bool = False, scenario: dict[str, Any] | None = None,
                 shared_view: SeatTranscript | None = None, lock: threading.RLock | None = None):
        self.ctx = ctx
        self.seat = int(seat)
        self.name = ctx.name_of_seat(self.seat)
        self.llm = llm
        self.log_dir = Path(log_dir)
        self.env = env or make_agent_env()
        self.rules = rules_of(ctx)
        self.max_tokens = dict(max_tokens or {"multi_talk": 1024, "multi_vote": 64, "multi_action": 64})
        self.stop_talk: list[str] = list(stop_talk) if stop_talk is not None else ["\n- **", "\n####", "\n###", "\n##"]
        self.stepped = bool(stepped)
        self.reveal = bool(reveal or writer or stepped)
        self.writer_mode = bool(writer or stepped)   # both write every seat's line from the shared writer view
        self.scenario = scenario
        plan = (scenario or {}).get("granularity") if scenario is not None else None
        self.condition = multi_tag(reveal=reveal, writer=writer, stepped=stepped, plan=plan)
        self.batch_user: str | None = None
        if self.stepped:  # the single-batch prompt, continued as the assistant's own output
            from single.base.prompt import build_messages
            sys_msg, user_msg = build_messages(ctx, scenario=scenario)
            self.system_prompt = sys_msg["content"]
            self.batch_user = user_msg["content"]
        else:
            self.system_prompt = build_system_prompt(ctx, self.seat, self.env, reveal=self.reveal, writer=self.writer_mode,
                                                     scenario=scenario)
        if self.writer_mode:
            self.view = shared_view if shared_view is not None else SeatTranscript(ctx, None)
            if self.view.seat is not None:
                raise ValueError("writer mode needs the writer view (seat None)")
        else:
            self.view = SeatTranscript(ctx, self.seat)
        self.lock = lock if lock is not None else threading.RLock()
        self.game_id: str | None = None
        self.round: int = int(self.rules["first_round"])
        self.turn: int = 0  # TALK requests received this round
        self.seq: int = 0
        self.records: list[dict[str, Any]] = []
        self._writer: RawJsonlWriter | None = None
        self.last_info: Info | None = None
        self.last_user: str | None = None  # the user message of the last LLM call (tests / dumps)

    # ---- hooks ------------------------------------------------------------------------------
    def on_initialize(self, info: Info) -> None:
        """Capture per-game data from INITIALIZE (e.g. card titles)."""

    def on_period_start(self, info: Info) -> None:
        """Update the view with what DAILY_INITIALIZE discloses (previous results, findings, options)."""

    def on_finish(self, info: Info) -> None:
        """FINISH: the last period's results (the deciding vote / execution) for the writer view."""

    def vote_candidates(self, info: Info) -> list[str]:
        raise NotImplementedError

    def action_candidates(self, request: Request, info: Info) -> list[str]:
        raise NotImplementedError

    def action_label(self, request: Request) -> str:
        """The action line without its target (``- divine: Name ->``)."""
        raise NotImplementedError

    def on_action_reply(self, request: Request, target: str | None) -> None:
        """Record the seat's own (provisional) action line in the view. ``target`` is the matched candidate."""

    # ---- helpers ----------------------------------------------------------------------------
    @property
    def connection_name(self) -> str:
        return f"seat{self.seat}"

    @property
    def messages(self) -> list[Message]:
        """The messages of the next call: system + the current view (for inspection only)."""
        return [{"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.view.render()}]

    def living(self, info: Info) -> list[str]:
        """Living players in seat order (status_map order is the server's; we sort by seat)."""
        alive = {n for n, s in info.status_map.items() if s == Status.ALIVE}
        return [n for n in self.ctx.names if n in alive]

    def living_others(self, info: Info) -> list[str]:
        return [n for n in self.living(info) if n != self.name]

    def absorb_talks(self, packet: Packet) -> None:
        for t in packet.talk_history or []:
            self.view.add_talk(t.day, t.idx, t.turn, t.agent, t.text, skip=t.skip, over=t.over)

    def raw_jsonl_path(self) -> Path:
        if self.game_id is None:
            raise RuntimeError("game_id unknown before INITIALIZE")
        return self.log_dir / self.ctx.domain / condition_dir(self.condition) / self.game_id / "raw" / f"agent.{self.seat}.jsonl"

    def _writer_or_open(self) -> RawJsonlWriter:
        if self._writer is None:
            self._writer = RawJsonlWriter(self.raw_jsonl_path())
        return self._writer

    def close(self) -> None:
        if self._writer is not None:
            self._writer.close()

    # ---- dispatch ---------------------------------------------------------------------------
    def handle_dict(self, d: dict[str, Any]) -> str:
        return self.handle(Packet.from_dict(d))

    def handle(self, packet: Packet) -> str:
        req = packet.request
        if req == Request.NAME:
            return self.connection_name
        info = packet.info
        if info is None:
            return ""
        self.last_info = info
        if req in NOTICE_REQUESTS:
            return self._notice(req, packet, info)
        if req == Request.TALK:
            return self._talk(packet, info)
        if req == Request.VOTE:
            return self._vote(packet, info)
        if req in ACTION_REQUESTS:
            return self._action(req, packet, info)
        return ""  # WHISPER / GUARD are not used in this study

    # ---- notices ----------------------------------------------------------------------------
    def _notice(self, req: Request, packet: Packet, info: Info) -> str:
        if req == Request.INITIALIZE:
            if info.agent != self.name:
                raise ValueError(f"seat {self.seat}: setup persona {self.name!r} but server says "
                                 f"info.agent={info.agent!r}")
            self.game_id = info.game_id
            self.on_initialize(info)
            self._writer_or_open()
        with self.lock:
            self.absorb_talks(packet)
            if req == Request.DAILY_INITIALIZE:
                self.round = int(info.day)
                self.turn = 0
                self.view.period(self.round)
                self.on_period_start(info)
            elif req == Request.DAILY_FINISH:
                self.round = int(info.day)
            elif req == Request.FINISH:
                self.on_finish(info)
        return ACK

    # ---- requests ---------------------------------------------------------------------------
    def _talk(self, packet: Packet, info: Info) -> str:
        self.round = int(info.day)
        with self.lock:
            self.absorb_talks(packet)
            self.turn += 1
            self.view.ensure_turn(self.round, self.turn)
            tail = build_talk_message(self.view.render(), self.name)
        if self.stepped:
            wire, _reply = self._complete(Request.TALK, self.batch_user, self.turn, on_error=T_FORCE_SKIP, assistant=tail)
        else:
            wire, _reply = self._complete(Request.TALK, tail, self.turn, on_error=T_FORCE_SKIP)
        return wire

    def _vote(self, packet: Packet, info: Info) -> str:
        self.round = int(info.day)
        candidates = self.vote_candidates(info)
        with self.lock:
            self.absorb_talks(packet)
            section_open = self.view.section_open(self.round, "vote")
            if self.stepped:
                tail = self.view.render() + "\n" + ("" if section_open else "### Vote\n") + f"- {self.name} ->"
            else:
                user = build_vote_message(self.ctx, self.view.render(), self.name, candidates, self.env,
                                          section_open=section_open)
        if self.stepped:
            wire, reply = self._complete(Request.VOTE, self.batch_user, None, on_error="", assistant=tail)
        else:
            wire, reply = self._complete(Request.VOTE, user, None, on_error="")
        target = match_candidate(reply, candidates)
        if target:
            with self.lock:
                if self.writer_mode:
                    self.view.add_vote(self.round, self.name, target)
                else:
                    self.view.set_own_vote(self.round, target)
        return wire

    def _action(self, req: Request, packet: Packet, info: Info) -> str:
        self.round = int(info.day)
        candidates = self.action_candidates(req, info)
        with self.lock:
            self.absorb_talks(packet)
            if self.writer_mode and info.executed_agent is not None and self.round >= 1:
                self.view.set_execution(self.round, info.executed_agent or None)  # told with the night request
            section_open = self.view.section_open(self.round, "action")
            if self.stepped:
                tail = self.view.render() + "\n" + ("" if section_open else "### Action\n") + self.action_label(req)
            else:
                user = build_action_message(self.ctx, self.view.render(), self.action_label(req), str(req), candidates,
                                            self.env, section_open=section_open)
        if self.stepped:
            wire, reply = self._complete(req, self.batch_user, None, on_error="", assistant=tail)
        else:
            wire, reply = self._complete(req, user, None, on_error="")
        with self.lock:
            self.on_action_reply(req, self._match_action(req, reply, candidates))
        return wire

    def _match_action(self, req: Request, reply: str, candidates: list[str]) -> str | None:
        """Single-target actions match one candidate; INVESTIGATE (several titles) is handled by the hook."""
        if req == Request.INVESTIGATE:
            return reply
        return match_candidate(reply, candidates)

    # ---- LLM call + record ------------------------------------------------------------------
    def _complete(self, req: Request, user: str, turn: int | None, on_error: str,
                  assistant: str | None = None) -> tuple[str, str]:
        """Returns ``(wire, stripped)``: the raw LLM text sent to the server unmodified (it normalises and
        keeps ``raw``) and the stripped form. On an LLM error both are ``on_error``.
        ``assistant`` (stepped): the transcript so far + label, continued as the writer's own output of the
        batch prompt (``LLMClient.complete_continuation``: token ids of the chat prompt + the prefix, sent to
        ``/v1/completions``). A talk stops at the next transcript element, a vote / action line at its end of line."""
        messages = [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user}]
        if assistant is not None:
            messages.append({"role": "assistant", "content": assistant})
        self.last_user = assistant if assistant is not None else user
        max_tokens = int(self.max_tokens[MAX_TOKENS_KIND[req]])
        ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds")
        t0 = time.perf_counter()
        raw: str | None = None
        meta: dict[str, Any] = {}
        error: str | None = None
        stop = self.stop_talk if req == Request.TALK else (["\n"] if assistant is not None else None)
        try:
            if assistant is not None:
                raw, meta = self.llm.complete_continuation(messages[:2], assistant, max_tokens, stop=stop)
            else:
                try:
                    raw, meta = self.llm.complete(messages, max_tokens, stop=stop)
                except TypeError:  # a client without the ``stop`` keyword (scripted / legacy)
                    raw, meta = self.llm.complete(messages, max_tokens)
            wire = raw if raw is not None else ""
            reply = wire.strip()
        except Exception as e:  # noqa: BLE001 - any failure degrades to a pass / empty action
            error = f"{type(e).__name__}: {e}"
            wire = reply = on_error
            print(f"[agent seat{self.seat}] {req} llm error: {error}", file=sys.stderr)
        latency_ms = round((time.perf_counter() - t0) * 1000)
        finish_reason = meta.get("finish_reason")
        self.seq += 1
        rec = {
            "kind": "llm_call",
            "seq": self.seq, "seat": self.seat, "request": str(req), "round": self.round, "turn": turn,
            "ts": ts, "messages": [dict(m) for m in messages], "response": raw,
            "usage": meta.get("usage"), "finish_reason": finish_reason, "error": error,
            "truncated": finish_reason == "length", "latency_ms": latency_ms,
        }
        if stop:
            rec["stop"] = list(stop)
        if assistant is not None:
            rec["continuation"] = meta.get("continuation", "completions")
            for k in ("prompt_ids", "prefix_ids"):
                if meta.get(k) is not None:
                    rec[k] = meta[k]
        for k in ("model", "tokens", "logprobs_error", "prompt_token_ids", "prompt_token_ids_error"):
            if meta.get(k) is not None:
                rec[k] = meta[k]
        self.records.append(rec)
        if self.game_id is not None:
            self._writer_or_open().write(rec)
        return wire, reply
