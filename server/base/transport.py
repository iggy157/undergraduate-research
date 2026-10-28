"""Websocket transport: a lobby that collects the five seat connections and a per-seat ask() helper.

Wire format (aiwolf-nlp-common compatible): the server sends one JSON packet per text message and
the agent answers every packet with a plain string (name / utterance / "Acknowledged.").
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from common.protocol import Packet, Request
from common.setup import N_SEATS, SEAT_NAMES

log = logging.getLogger("server.transport")
CLOSE_TIMEOUT = 2.0  # seconds to wait for the peer to finish the closing handshake


class Disconnected(Exception):
    """The agent's websocket closed while the server was waiting for it."""

    def __init__(self, seat: int):
        super().__init__(f"seat{seat} disconnected")
        self.seat = seat


class SeatConnection:
    def __init__(self, ws: ServerConnection, seat: int):
        self.ws = ws
        self.seat = seat
        self.conn_name = f"seat{seat}"

    async def ask(self, packet: dict[str, Any], timeout: float) -> str | None:
        """Send one packet and wait for the reply. None = timeout. Raises Disconnected."""
        try:
            await self.ws.send(json.dumps(packet, ensure_ascii=False))
            reply = await asyncio.wait_for(self.ws.recv(), timeout)
        except TimeoutError:
            log.warning("seat%d: timeout waiting for %s", self.seat, packet.get("request"))
            return None
        except ConnectionClosed as e:
            raise Disconnected(self.seat) from e
        if isinstance(reply, bytes):
            reply = reply.decode("utf-8", errors="replace")
        return reply

    async def close(self) -> None:
        try:
            await self.ws.close()
        except Exception:  # pragma: no cover - best effort
            pass


class Lobby:
    """Accepts connections, sends NAME, keeps the ones that answer seat1..seat5 (no duplicates)."""

    def __init__(self, host: str, port: int, timeout: float, n_seats: int = N_SEATS):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.n_seats = n_seats
        self.conns: dict[int, SeatConnection] = {}
        self.ready = asyncio.Event()
        self.done = asyncio.Event()
        self._server: Server | None = None

    async def start(self) -> None:
        # ping_interval=None: an agent busy with a long LLM call must not be dropped for missing pings.
        # close_timeout: do not let a lingering (e.g. rejected) client hold the shutdown for 10 s.
        self._server = await serve(self._handler, self.host, self.port, ping_interval=None,
                                   close_timeout=CLOSE_TIMEOUT, max_size=16 * 1024 * 1024)
        self.port = self.bound_port

    @property
    def bound_port(self) -> int:
        assert self._server is not None
        for s in self._server.sockets:
            return int(s.getsockname()[1])
        return self.port

    async def _handler(self, ws: ServerConnection) -> None:
        try:
            await ws.send(json.dumps(Packet(Request.NAME).to_dict()))
            raw = await asyncio.wait_for(ws.recv(), self.timeout)
        except (TimeoutError, ConnectionClosed):
            return
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        name = raw.strip()
        if name not in SEAT_NAMES or self.ready.is_set():
            log.warning("rejecting connection with name %r", name)
            await ws.close(1008, "expected an unused seat name seat1..seat5")
            return
        seat = int(name[len("seat"):])
        if seat in self.conns:
            log.warning("rejecting duplicate seat name %r", name)
            await ws.close(1008, "duplicate seat name")
            return
        self.conns[seat] = SeatConnection(ws, seat)
        log.info("%s connected (%d/%d)", name, len(self.conns), self.n_seats)
        if len(self.conns) == self.n_seats:
            self.ready.set()
        await self.done.wait()  # keep the connection open until the game is over

    async def wait_ready(self, timeout: float | None = None) -> None:
        if timeout is None:
            await self.ready.wait()
        else:
            await asyncio.wait_for(self.ready.wait(), timeout)

    async def stop(self) -> None:
        self.done.set()
        for c in list(self.conns.values()):
            await c.close()
        if self._server is not None:
            self._server.close()
            try:
                await asyncio.wait_for(self._server.wait_closed(), CLOSE_TIMEOUT + 1)
            except TimeoutError:  # pragma: no cover - a client never closed its TCP side
                log.debug("server.wait_closed timed out; abandoning remaining connections")
            self._server = None


__all__ = ["Disconnected", "Lobby", "SeatConnection"]
