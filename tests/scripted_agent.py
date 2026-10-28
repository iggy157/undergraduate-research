"""Deterministic, LLM-free agent for exercising the server (tests + scripts/compat_aiwolf_go.py).

Protocol: aiwolf-nlp-common compatible. One JSON packet per websocket message from the server; the
agent replies with a plain string. NAME -> "seat<N>", notices -> "Acknowledged.".

``run_seat(url, seat, **behaviour)`` plays one seat synchronously and returns the ``ScriptedAgent``
with everything it received, so tests can run five of them in threads and inspect them.

Default behaviour (all deterministic, keyed on seat and turn):
  TALK   seat 1: speaks every turn, "@Name" mention on turn 1, a 60-word utterance on turn 4
         seat 2: "skip." on turn 2 (lower case + punctuation -> normalised Skip)
         seat 3: "Over." on turn 3 (-> no turn 4)
         seat 4: "ForceSkip" on turn 2 (-> forced Skip)
         seat 5: "" on turn 3 (-> Over, empty:true)
  VOTE   aiwolf: alphabetically first living player (self allowed)
         discussion: seats 1-3 -> first label (written "Option A" / "a." / "A"), seats 4-5 -> second
  DIVINE / ATTACK: alphabetically first living other player
  INVESTIGATE: the first two titles from INITIALIZE's card_titles as "- title" lines
"""
from __future__ import annotations

import json
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import websocket  # websocket-client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.protocol import ACK, NOTICE_REQUESTS, T_FORCE_SKIP, Info, Packet, Request, Talk

# Special replies a behaviour function may return instead of a string:
NO_REPLY = None            # do not answer this packet at all (simulates an agent timeout)
DISCONNECT = object()      # close the websocket instead of answering (simulates a crash)

TalkFn = Callable[["ScriptedAgent", Info, int], str]
VoteFn = Callable[["ScriptedAgent", Info], str]
ActFn = Callable[["ScriptedAgent", Info, str], str]
InvFn = Callable[["ScriptedAgent", Info], str]


def living(info: Info) -> list[str]:
    return sorted(n for n, s in info.status_map.items() if s == "ALIVE")


def default_talk(agent: ScriptedAgent, info: Info, turn: int) -> str:
    others = [n for n in living(info) if n != agent.name]
    seat = agent.seat
    if seat == 2 and turn == 2:
        return "skip."
    if seat == 3 and turn == 3:
        return "Over."
    if seat == 4 and turn == 2:
        return T_FORCE_SKIP
    if seat == 5 and turn == 3:
        return ""
    if seat == 1 and turn == 4:
        return " ".join(f"word{i}" for i in range(60))
    mention = f"@{others[0]} " if others and turn == 1 else ""
    return f"{mention}{agent.name} speaking in round {info.day}, turn {turn}."


def default_vote(agent: ScriptedAgent, info: Info) -> str:
    if agent.options:  # discussion domains: labels revealed at round 3
        labels = [o["label"] for o in agent.options]
        if agent.seat <= 3:
            lab = labels[0]
            return {1: f"Option {lab}", 2: f"{lab.lower()}.", 3: lab}[agent.seat]
        return labels[1 % len(labels)]
    return living(info)[0]


def default_act(agent: ScriptedAgent, info: Info, request: str) -> str:
    return [n for n in living(info) if n != agent.name][0]


def default_investigate(agent: ScriptedAgent, info: Info) -> str:
    titles = info.card_titles or agent.card_titles
    return "\n".join(f"- {t}" for t in titles[:2])


class ScriptedAgent:
    def __init__(self, url: str, seat: int, *, talk: TalkFn = default_talk, vote: VoteFn = default_vote,
                 act: ActFn = default_act, investigate: InvFn = default_investigate,
                 log_dir: str | Path | None = None, recv_timeout: float = 60.0,
                 name: str | None = None):
        self.url = url
        self.seat = seat
        self.conn_name = name or f"seat{seat}"
        self.talk_fn, self.vote_fn, self.act_fn, self.inv_fn = talk, vote, act, investigate
        self.log_dir = Path(log_dir) if log_dir else None
        self.recv_timeout = recv_timeout
        # --- what we learned ---
        self.name: str | None = None
        self.game_id: str | None = None
        self.role: str | None = None
        self.profile: str | None = None
        self.problem: str | None = None
        self.card_titles: list[str] = []
        self.options: list[dict[str, str]] | None = None
        self.options_seen_at: list[int] = []           # days whose DAILY_INITIALIZE carried options
        self.investigate_results: dict[int, list] = {}  # day -> investigate_result
        self.divine_results: dict[int, dict] = {}       # day -> divine_result
        self.executed_seen: dict[int, str | None] = {}
        self.attacked_seen: dict[int, str | None] = {}
        self.finish_info: dict[str, Any] | None = None
        self.packets: list[dict[str, Any]] = []
        self.received_talks: list[Talk] = []
        self.requests: list[tuple[str, int]] = []       # (request, day)
        self.talk_turns: dict[int, int] = {}            # day -> TALK requests received
        self.replies: list[tuple[str, str]] = []
        self.error: BaseException | None = None
        self._llm_seq = 0

    # ---- transport ------------------------------------------------------------------------
    def run(self) -> ScriptedAgent:
        try:
            ws = websocket.create_connection(self.url, timeout=self.recv_timeout)
        except Exception as e:  # pragma: no cover
            self.error = e
            return self
        try:
            while True:
                msg = ws.recv()
                if msg is None or msg == "":
                    break
                d = json.loads(msg)
                self.packets.append(d)
                reply = self.handle(d)
                if reply is DISCONNECT:
                    self.replies.append((d["request"], "<disconnect>"))
                    break
                if reply is NO_REPLY:
                    self.replies.append((d["request"], "<no reply>"))
                    continue
                self.replies.append((d["request"], reply))
                ws.send(reply)
                if d["request"] == "FINISH":
                    break
        except Exception as e:  # keep the exception for the test to inspect
            self.error = e
        finally:
            try:
                ws.close()
            except Exception:
                pass
        return self

    # ---- dispatch -------------------------------------------------------------------------
    def handle(self, d: dict[str, Any]) -> str:
        req = d["request"]
        if req == "NAME":
            return self.conn_name
        pkt = Packet.from_dict(d)
        info = pkt.info
        assert info is not None, req
        self.requests.append((req, info.day))
        if pkt.talk_history:
            self.received_talks.extend(pkt.talk_history)
        if req == Request.INITIALIZE:
            self.name = info.agent
            self.game_id = info.game_id
            self.profile = info.profile
            self.problem = info.problem
            self.card_titles = list(info.card_titles or [])
            self.role = info.role_map.get(info.agent)
            self.setting = pkt.setting
        if req == Request.DAILY_INITIALIZE:
            if info.options is not None:
                self.options = info.options
                self.options_seen_at.append(info.day)
            if info.investigate_result is not None:
                self.investigate_results[info.day] = info.investigate_result
            if info.divine_result is not None:
                self.divine_results[info.day] = info.divine_result.to_dict()
            self.executed_seen[info.day] = info.executed_agent
            self.attacked_seen[info.day] = info.attacked_agent
        if req == Request.FINISH:
            self.finish_info = d["info"]
        if req in NOTICE_REQUESTS:
            return ACK
        if req == Request.TALK:
            turn = self.talk_turns.get(info.day, 0) + 1
            self.talk_turns[info.day] = turn
            out = self.talk_fn(self, info, turn)
            if isinstance(out, str):
                self._llm_call("TALK", info.day, turn, out)
            return out
        if req == Request.VOTE:
            out = self.vote_fn(self, info)
            self._llm_call("VOTE", info.day, None, out)
            return out
        if req == Request.INVESTIGATE:
            out = self.inv_fn(self, info)
            self._llm_call("INVESTIGATE", info.day, None, out)
            return out
        if req in (Request.DIVINE, Request.ATTACK):
            out = self.act_fn(self, info, req)
            self._llm_call(req, info.day, None, out)
            return out
        return ""

    def _llm_call(self, request: str, day: int, turn: int | None, response: str) -> None:
        """Mimic agent/base: append an llm_call record to raw/agent.<seat>.jsonl (no LLM involved)."""
        if self.log_dir is None or self.game_id is None:
            return
        domain = self.game_id.rsplit("_", 1)[0].split("__")[0].rsplit("_", 1)[0]
        raw_dir = self.log_dir / domain / "multi-private" / self.game_id / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        import datetime as _dt
        rec = {"kind": "llm_call", "seq": self._llm_seq, "seat": self.seat, "request": request,
               "round": day, "turn": turn, "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds"),
               "messages": [], "response": response, "usage": None,
               "finish_reason": "stop", "error": None, "truncated": False, "latency_ms": 0}
        self._llm_seq += 1
        with open(raw_dir / f"agent.{self.seat}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_seat(url: str, seat: int, **kw: Any) -> ScriptedAgent:
    """Play one seat to the end (blocking)."""
    return ScriptedAgent(url, seat, **kw).run()


def run_seats_in_threads(url: str, per_seat: dict[int, dict[str, Any]] | None = None,
                         seats: range = range(1, 6), join_timeout: float = 60.0,
                         **common_kw: Any) -> list[ScriptedAgent]:
    agents = [ScriptedAgent(url, s, **{**common_kw, **(per_seat or {}).get(s, {})}) for s in seats]
    threads = [threading.Thread(target=a.run, name=f"agent-{a.seat}", daemon=True) for a in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join(join_timeout)
    return agents


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="scripted agent (one seat, or all five with --all)")
    ap.add_argument("--url", default="ws://127.0.0.1:10000")
    ap.add_argument("--seat", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--log-dir", default=None)
    a = ap.parse_args()
    if a.all:
        for ag in run_seats_in_threads(a.url, log_dir=a.log_dir):
            print(ag.seat, ag.name, ag.error or "ok")
    else:
        ag = run_seat(a.url, a.seat, log_dir=a.log_dir)
        print(ag.seat, ag.name, ag.error or "ok")
