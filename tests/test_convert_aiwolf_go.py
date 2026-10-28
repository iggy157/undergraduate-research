"""Go aiwolf-nlp-server log + json -> common rows (common/convert/aiwolf_go.py).

Fixture: manyshot-ablation log/factor/eval/en_scaf_base/{log,json}/1787800750_yharada_*.{log,json}
(5-player game, 3 days, invalid votes ("none") on day 1, execution + attack on day 2, WEREWOLF win).
"""
from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path

import pytest

from common.convert import aiwolf_go
from common.schema import LogRow
from common.violations import CODES, find_violations

FIX = Path(__file__).parent / "fixtures"
CSV_TEXT = (FIX / "aiwolf_go_1787800750.log").read_text(encoding="utf-8")
SERVER_JSON = json.loads((FIX / "aiwolf_go_1787800750.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ctx():
    return aiwolf_go.context_from_log(CSV_TEXT)


@pytest.fixture(scope="module")
def rows(ctx):
    return aiwolf_go.convert(CSV_TEXT, SERVER_JSON, ctx)


def test_context_from_log_mirrors_go_assignment(ctx):
    assert ctx.names == ["Midori", "Toshio", "Mio", "Mizuki", "Misaki"]
    assert ctx.role_of_name("Toshio") == "SEER" and ctx.role_of_name("Misaki") == "WEREWOLF"
    assert ctx.domain == "aiwolf" and ctx.rules["word_cap"] == 40


def test_counts_per_type(rows):
    c = Counter(r.type for r in rows)
    assert c == {"status": 20, "talk": 54, "pass": 2, "vote": 9, "action": 5, "result": 1}
    assert [r.seq for r in rows] == list(range(len(rows)))


def test_csv_roundtrip(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for r in rows:
        w.writerow(r.to_csv())
    back = [LogRow.from_csv(rec) for rec in csv.reader(io.StringIO(buf.getvalue()))]
    assert back == rows


def test_talk_turns_names_and_mentions(rows):
    talks = [r for r in rows if r.type == "talk"]
    assert {r.turn for r in talks} == {1, 2, 3, 4}
    first = talks[0]
    assert (first.round, first.turn, first.agent) == (0, 1, "Mizuki")
    assert first.text == "I'm Mizuki. Let's organize what we know first."
    assert first.extra["words"] == 8 and first.extra["mentions"] == [] and first.extra["raw_differs"] is False
    mio = talks[1]
    assert mio.agent == "Mio" and mio.extra["mentions"] == ["Mizuki"] and mio.extra["raw_differs"] is True
    assert "!  @Mizuki ," in mio.text  # Go processText re-spaces mentions; kept as seen by others


def test_pass_rows(rows):
    p = [r for r in rows if r.type == "pass"]
    assert [(r.round, r.turn, r.agent, r.text) for r in p] == [(0, 4, "Misaki", "Over"), (0, 4, "Toshio", "Over")]
    assert all(r.extra == {"forced": False, "empty": False} for r in p)


def test_votes_valid_and_invalid(rows):
    d1 = [r for r in rows if r.type == "vote" and r.round == 1]
    assert len(d1) == 5 and all(r.extra["valid"] is False and r.target == "" and r.extra["raw"] == "none" for r in d1)
    d2 = [r for r in rows if r.type == "vote" and r.round == 2]
    assert [(r.agent, r.target, r.extra["valid"]) for r in d2] == [
        ("Midori", "Mio", True), ("Mio", "", False), ("Mizuki", "Mio", True), ("Misaki", "Mio", True)]


def test_actions(rows):
    acts = [(r.round, r.extra["action"], r.agent, r.target, r.text) for r in rows if r.type == "action"]
    assert acts == [(0, "divine", "Toshio", "Mizuki", "HUMAN"),
                    (1, "divine", "Toshio", "Misaki", "WEREWOLF"),
                    (1, "attack", "Misaki", "Toshio", "Toshio"),
                    (2, "execute", "", "Mio", "Mio"),
                    (2, "attack", "Misaki", "Mizuki", "Mizuki")]
    ex = next(r for r in rows if r.type == "action" and r.extra["action"] == "execute")
    assert ex.extra == {"action": "execute", "role": "POSSESSED", "tie": False}
    at = [r for r in rows if r.type == "action" and r.extra["action"] == "attack"]
    assert all(r.extra["success"] and not r.extra["no_target"] for r in at)


def test_status_and_result(rows):
    st = [r for r in rows if r.type == "status"]
    assert Counter(r.round for r in st) == {0: 5, 1: 5, 2: 5, 3: 5}
    final = {r.agent: r.extra["alive"] for r in st if r.round == 3}
    assert final == {"Midori": True, "Toshio": False, "Mio": False, "Mizuki": False, "Misaki": True}
    assert st[0].extra == {"seat": 1, "role": "VILLAGER", "alive": True}
    res = rows[-1]
    assert res.type == "result" and res.round == 3 and res.text == "WEREWOLF"
    assert res.extra == {"winner": "WEREWOLF", "villagers": 1, "werewolves": 1}


def test_order_within_day_is_talk_vote_execute_night(rows):
    d2 = [r.type if r.type != "action" else r.extra["action"] for r in rows if r.round == 2]
    assert d2[:5] == ["status"] * 5
    body = [t for t in d2 if t not in ("status", "talk")]
    assert body == ["vote"] * 4 + ["execute", "attack"]


def test_without_json_only_valid_votes_and_no_raw(ctx):
    rows = aiwolf_go.convert(CSV_TEXT, None, ctx)
    c = Counter(r.type for r in rows)
    assert c["vote"] == 3 and c["talk"] == 54 and c["pass"] == 2
    assert all(r.extra["raw_differs"] is False for r in rows if r.type == "talk")


def test_violations_run_on_converted_rows(ctx, rows):
    v = find_violations(rows, ctx)
    assert all(v_["code"] in CODES for v_ in v)
    assert not any(v_["code"].startswith("early_reveal") for v_ in v)
    # the real-run pattern: utterances with the pass token glued to the end ("... I abstain. Over.")
    trailing = [v_ for v_ in v if v_["code"] == "trailing_over"]
    assert len(trailing) == 10 and all(rows[v_["seq"]].text.endswith(" Over.") for v_ in trailing)


def test_empty_reply_and_forceskip_from_json(ctx):
    """The Go json logger omits "response" for an empty reply (-> Over, empty:true); ForceSkip -> forced Skip."""
    lines = [
        "0,status,1,VILLAGER,ALIVE,x1,Midori", "0,status,2,SEER,ALIVE,x2,Toshio", "0,status,3,POSSESSED,ALIVE,x3,Mio",
        "0,status,4,VILLAGER,ALIVE,x4,Mizuki", "0,status,5,WEREWOLF,ALIVE,x5,Misaki",
        "0,talk,0,0,1,Over", "0,talk,1,0,2,Skip", "0,talk,2,0,3,Over", "0,talk,3,0,4,hello, world",
        "1,status,1,VILLAGER,ALIVE,x1,Midori", "1,status,2,SEER,ALIVE,x2,Toshio", "1,status,3,POSSESSED,ALIVE,x3,Mio",
        "1,status,4,VILLAGER,ALIVE,x4,Mizuki", "1,status,5,WEREWOLF,ALIVE,x5,Misaki", "1,result,4,1,VILLAGER"]
    csv_text = "\n".join(lines)

    def entry(agent, response=None):
        e = {"agent": agent, "request": json.dumps({"request": "TALK", "info": {"day": 0, "agent": agent}})}
        if response is not None:
            e["response"] = response
        return e
    sj = {"entries": [entry("Midori"), entry("Toshio", "ForceSkip"), entry("Mio", "Over"), entry("Mizuki", "hello, world")]}
    rows = aiwolf_go.convert(csv_text, sj, ctx)
    p = {r.agent: r for r in rows if r.type in ("pass", "talk")}
    assert p["Midori"].type == "pass" and p["Midori"].extra == {"forced": False, "empty": True, "raw": ""}
    assert p["Toshio"].type == "pass" and p["Toshio"].extra == {"forced": True, "empty": False, "raw": "ForceSkip"}
    assert p["Mio"].type == "pass" and p["Mio"].extra == {"forced": False, "empty": False}
    assert p["Mizuki"].type == "talk" and p["Mizuki"].text == "hello, world" and p["Mizuki"].extra["raw_differs"] is False
    assert rows[-1].type == "result" and rows[-1].text == "VILLAGE" and rows[-1].extra["villagers"] == 4
    assert find_violations(rows, ctx) == []  # forced / empty passes are not pass_punct
