"""Source repo result.json -> common rows (common/convert/legacy_resultjson.py).

Fixture: manyshot-ablation log/domains/panel/v4/l8_unordered/panel_unordered_064_20260912023154/result.json
(protocol v4, 3 rounds x 4 sweeps x 5 seats = 60 talks, no passes, one vote with raw_retry).
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path

import pytest

from common.convert import legacy_resultjson as lr
from common.schema import LogRow

FIX = Path(__file__).parent / "fixtures" / "legacy_panel_unordered_064_result.json"


@pytest.fixture(scope="module")
def result():
    return lr.load(FIX)


@pytest.fixture(scope="module")
def rows(result):
    return lr.convert(result)


def test_counts(rows):
    assert Counter(r.type for r in rows) == {"status": 20, "talk": 60, "vote": 5, "result": 1}
    assert [r.seq for r in rows] == list(range(len(rows)))


def test_rounds_and_sweeps(rows):
    talks = [r for r in rows if r.type == "talk"]
    assert Counter(r.round for r in talks) == {1: 20, 2: 20, 3: 20}
    assert Counter((r.round, r.turn) for r in talks) == {(r, t): 5 for r in (1, 2, 3) for t in (1, 2, 3, 4)}
    assert talks[0].agent == "Daisuke" and talks[0].extra["raw_differs"] is False
    assert talks[0].extra["words"] == len(talks[0].text.split())


def test_status_blocks_keep_profile(rows, result):
    st = [r for r in rows if r.type == "status"]
    assert Counter(r.round for r in st) == {1: 5, 2: 5, 3: 10}
    first = st[0]
    assert first.agent == result["participants"][0]["name"] and first.extra["seat"] == 1
    assert first.extra["role"] == "PARTICIPANT" and first.extra["alive"] is True
    assert first.extra["profile"] == result["participants"][0]["profile"]
    assert first.extra["problem"] == result["participants"][0]["problem"]
    assert len(first.extra["cards"]) == 2


def test_votes_keep_raw_retry_and_result_tally(rows):
    votes = [r for r in rows if r.type == "vote"]
    assert [(r.agent, r.target) for r in votes] == [("Daisuke", "D"), ("Minako", "D"), ("Kenji", "D"),
                                                    ("Takumi", "A"), ("Shunichi", "C")]
    assert all(r.round == 3 and r.extra["request"] == "vote_final" and r.extra["valid"] for r in votes)
    assert votes[0].extra["raw"] == "@D"
    assert votes[-1].extra["raw"] == "@Market Plaza" and votes[-1].extra["raw_retry"] == "C"
    res = rows[-1]
    assert res.type == "result" and res.text == "D"
    assert res.extra["adopted"] == "D" and res.extra["tally"] == {"A": 1, "C": 1, "D": 3} and res.extra["tie"] is False
    assert res.extra["domain"] == "candidate_selection" and res.extra["source_instance_id"] == "panel_005"


def test_csv_roundtrip(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for r in rows:
        w.writerow(r.to_csv())
    assert [LogRow.from_csv(rec) for rec in csv.reader(io.StringIO(buf.getvalue()))] == rows


def test_assign_rounds_with_passes_and_eliminations():
    names = ["A", "B", "C", "D", "E"]
    turns = []
    # round 1: sweep 1 all talk; sweep 2: B passes (Over); sweep 3: A,C,D,E; sweep 4: A,C
    for n in names:
        turns.append({"actor": n, "kind": "talk", "text": "x"})
    for n in names:
        turns.append({"actor": n, "kind": "pass" if n == "B" else "talk", "text": "Over" if n == "B" else "x"})
    for n in ["A", "C", "D", "E"]:
        turns.append({"actor": n, "kind": "talk", "text": "x"})
    for n in ["A", "C"]:
        turns.append({"actor": n, "kind": "talk", "text": "x"})
    # round 2 starts with B (a seat that passed in round 1) -> boundary
    for n in names:
        turns.append({"actor": n, "kind": "talk", "text": "x"})
    for n in names:
        turns.append({"actor": n, "kind": "select", "request": "eliminate_r2", "selection": "A", "text": "(eliminate_r2)"})
    for n in ["C", "D"]:
        turns.append({"actor": n, "kind": "talk", "text": "x"})
    placed = lr.assign_rounds(turns, 3)
    assert placed[:5] == [(1, 1)] * 5 and placed[5:10] == [(1, 2)] * 5
    assert placed[10:14] == [(1, 3)] * 4 and placed[14:16] == [(1, 4)] * 2
    assert placed[16:21] == [(2, 1)] * 5
    assert placed[21:26] == [(2, None)] * 5
    assert placed[26:] == [(3, 1)] * 2
