"""Websocket loop: receive one JSON packet per message, reply with a plain string.

Uses ``websocket-client`` (``import websocket``) like aiwolf-nlp-common. The server may come up a
little after the agent, so connecting retries for ``connect_timeout`` seconds.
"""
from __future__ import annotations

import contextlib
import json
import sys
import time

import websocket

from common.protocol import Packet, Request

from .seat import SeatAgent


def connect(url: str, connect_timeout: float = 60.0, retry_interval: float = 0.5) -> websocket.WebSocket:
    deadline = time.monotonic() + connect_timeout
    last: Exception | None = None
    while True:
        try:
            return websocket.create_connection(url, timeout=None)
        except (OSError, websocket.WebSocketException) as e:
            last = e
            if time.monotonic() >= deadline:
                raise ConnectionError(f"could not connect to {url} within {connect_timeout}s: {e}") from last
            time.sleep(retry_interval)


def run_client(url: str, agent: SeatAgent, connect_timeout: float = 60.0, verbose: bool = False) -> int:
    """Return 0 when the game reached FINISH, 1 when the connection dropped before that."""
    ws = connect(url, connect_timeout)
    finished = False
    try:
        while True:
            try:
                raw = ws.recv()
            except websocket.WebSocketConnectionClosedException:
                break
            if not ws.connected or isinstance(raw, bytes):  # close frame: recv() returns its status bytes
                break
            if not raw:
                continue
            packet = Packet.from_dict(json.loads(raw))
            reply = agent.handle(packet)
            if verbose:
                print(f"[agent seat{agent.seat}] {packet.request} -> {reply!r}", file=sys.stderr)
            ws.send(reply)
            if packet.request == Request.FINISH:
                finished = True
                _drain(ws)
                break
    finally:
        with contextlib.suppress(Exception):
            ws.close()
        agent.close()
    return 0 if finished else 1


def _drain(ws: websocket.WebSocket, seconds: float = 3.0) -> None:
    """Give the server a moment to close first so our reply is read before the close frame."""
    with contextlib.suppress(Exception):  # timeout or closed: both fine
        ws.settimeout(seconds)
        ws.recv()
