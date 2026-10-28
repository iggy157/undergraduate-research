"""Unit tests for the reply parsers, game id, and the CLI entry point."""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from conftest import ROOT
from scripted_agent import run_seats_in_threads

from common.logwriter import read_log
from common.setup import GameContext
from server.base.game import make_game_id, sanitize_model_tag
from server.base.parse import classify_talk, match_name, match_option, parse_investigate


@pytest.mark.parametrize("raw,expected", [
    (None, ("skip", "Skip", {"forced": True})),
    ("", ("over", "Over", {"empty": True})),
    ("   \n", ("over", "Over", {"empty": True})),
    ("ForceSkip", ("skip", "Skip", {"forced": True})),
    ("Skip", ("skip", "Skip", {})),
    ("skip.", ("skip", "Skip", {})),
    ("OVER!", ("over", "Over", {})),
    ("Over.\n", ("over", "Over", {})),
    ("  Hello @Rin, over to you.  ", ("talk", "Hello @Rin, over to you.", {})),
    ("Skip this one, I think.", ("talk", "Skip this one, I think.", {})),
    ("Overall I agree.", ("talk", "Overall I agree.", {})),
])
def test_classify_talk(raw, expected):
    assert classify_talk(raw) == expected


def test_classify_never_truncates():
    text = "w " * 500
    assert classify_talk(text)[1] == text.strip()


def test_match_name():
    names = ["Rin", "Kenji", "Mio"]
    assert match_name("Rin", names) == "Rin"
    assert match_name(" kenji. ", names) == "Kenji"
    assert match_name("@Mio", names) == "Mio"
    assert match_name('"Rin"', names) == "Rin"
    assert match_name("Rin and Mio", names) is None
    assert match_name("Nobody", names) is None
    assert match_name(None, names) is None


def test_match_option():
    opts = [{"label": "A", "name": "Fixed Weekly Rota"}, {"label": "B", "name": "Paid Cleaning Service"}]
    for raw in ("A", "a", "A.", "Option A", "option a.", "Candidate A", " A "):
        assert match_option(raw, opts) == "A"
    assert match_option("paid cleaning service", opts) == "B"
    assert match_option("C", opts) is None
    assert match_option("", opts) is None
    assert match_option("Option", opts) is None


def test_parse_investigate():
    cards = [{"card_id": f"card_{i:02d}", "title": f"Title {i}"} for i in range(1, 5)]
    assert parse_investigate("- Title 2\n- Title 4", cards) == ([cards[1], cards[3]], "ok")
    assert parse_investigate("1. 'title 3'\n2. Title 3\n3. Title 1", cards) == ([cards[2], cards[0]], "ok")
    assert parse_investigate("Title 1; Title 2; Title 3", cards) == ([cards[0], cards[1]], "ok")
    assert parse_investigate("Title 1.", cards) == ([cards[0]], "partial")
    assert parse_investigate("Title 1\nTitle 1", cards) == ([cards[0]], "partial")
    assert parse_investigate("nothing here", cards) == ([], "fail")
    assert parse_investigate(None, cards) == ([], "fail")
    untitled = [{"card_id": "card_01", "title": ""}]
    assert parse_investigate("", untitled) == ([], "fail")


def test_game_id_and_model_tag():
    assert sanitize_model_tag("google/gemma-3-27b-it") == "gemma-3-27b-it"
    assert sanitize_model_tag("Qwen/Qwen2.5-7B_Instruct:v1") == "Qwen2.5-7B-Instruct-v1"
    import datetime
    gid = make_game_id("aiwolf_0001", "scripted", datetime.datetime(2026, 10, 27, 8, 5, 9))
    assert gid == "aiwolf_0001__multi-private__scripted__20261027T080509"


def _assert_closed(ws) -> None:
    """websocket-client returns '' (or raises) once the server has closed the connection."""
    try:
        got = ws.recv()
    except Exception:
        return
    assert got in ("", b""), got


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_cli_end_to_end(tmp_path: Path):
    port = _free_port()
    log_dir = tmp_path / "log"
    proc = subprocess.Popen(
        [sys.executable, "-m", "server", "--setup", "aiwolf_0003", "--port", str(port), "--log-dir",
         str(log_dir), "--timeout", "5", "--model-tag", "scripted", "--connect-timeout", "20"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    url = f"ws://127.0.0.1:{port}"
    agents: list = []

    def connect_when_up():
        deadline = 10.0
        import time
        while deadline > 0:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
                deadline -= 0.1
        agents.extend(run_seats_in_threads(url))

    t = threading.Thread(target=connect_when_up)
    t.start()
    out, err = proc.communicate(timeout=30)
    t.join(10)
    assert proc.returncode == 0, err
    line = out.strip().splitlines()[-1]
    game_id, outcome = line.split("\t")
    assert game_id.startswith("aiwolf_0003__multi-private__scripted__")
    assert json.loads(outcome)["winner"] in ("VILLAGE", "WEREWOLF")
    rows = read_log(log_dir / "aiwolf" / "multi-private" / game_id / f"{game_id}.log")
    assert rows[-1].type == "result"
    assert all(a.error is None for a in agents)


def test_dynamic_without_titles_is_refused(tmp_path: Path):
    """An instance without card titles: dynamic mode must refuse to start (check_dynamic_ready)."""
    import asyncio

    from server.base.runner import run_game
    ctx = GameContext.load("shared_living_0001")
    for c in ctx.instance["card_pool"]:
        c["title"] = ""  # the pre-§9-9 state
    with pytest.raises(ValueError, match="needs card titles"):
        asyncio.run(run_game(ctx, 0, tmp_path, timeout=1))


def test_duplicate_or_bad_seat_name_is_rejected(tmp_path: Path):
    """A connection whose NAME reply is not an unused seat1..seat5 is closed; the game still starts."""
    import asyncio

    import websocket

    from server.base.runner import run_game
    ctx = GameContext.load("aiwolf_0004")
    box: dict = {}
    ev = threading.Event()

    def on_listening(p):
        box["port"] = p
        ev.set()

    def server_main():
        try:
            box["game"] = asyncio.run(run_game(ctx, 0, tmp_path, timeout=5, on_listening=on_listening,
                                               connect_timeout=20))
        except BaseException as e:
            box["error"] = e
            ev.set()

    th = threading.Thread(target=server_main, daemon=True)
    th.start()
    assert ev.wait(10)
    url = f"ws://127.0.0.1:{box['port']}"
    for bad in ("seat9", "agent1", ""):
        ws = websocket.create_connection(url, timeout=5)
        assert json.loads(ws.recv())["request"] == "NAME"
        ws.send(bad)
        _assert_closed(ws)
        ws.close()
    # a proper seat1, then a duplicate seat1 which must be rejected, then the rest
    first = websocket.create_connection(url, timeout=30)
    assert json.loads(first.recv())["request"] == "NAME"
    first.send("seat1")
    dup = websocket.create_connection(url, timeout=5)
    dup.recv()
    dup.send("seat1")
    _assert_closed(dup)
    dup.close()
    first.close()  # seat1 goes away before the game starts: its slot is taken, a reconnect must be possible
    agents = run_seats_in_threads(url, seats=range(2, 6))
    th.join(15)
    # seat1 closed its socket before INITIALIZE, so the game is expected to abort on the first notice
    assert "game" in box
    game = box["game"]
    assert game.aborted and game.outcome["winner"] == "NONE"
    assert game.outcome["reason"].startswith("disconnect:")
    assert all(a.error is None for a in agents)
