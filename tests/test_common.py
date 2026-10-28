"""Tests for the common package (setup generation, tiebreak, logwriter round trip, shared rendering)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from common import DOMAINS
from common.logwriter import GameLogWriter, count_words, find_mentions, read_jsonl, read_log
from common.protocol import Info, Packet, Request, Setting, Talk
from common.render import identity_block, make_env, rules_context, shared_block
from common.schema import LogRow, normalize_winner
from common.setup import GameContext, game_setup, load_experiment, load_personas, load_setup, validate_setup
from common.tiebreak import choose, tally

EXP = load_experiment()


def test_personas_24_four_fields():
    ps = load_personas()
    assert len(ps) == 24
    p = next(iter(ps.values()))
    assert set(p.__dataclass_fields__) == {"name", "age", "gender", "personality"}


@pytest.mark.parametrize("domain", DOMAINS)
def test_game_setup_deterministic_and_valid(domain):
    a = game_setup(domain, 3, EXP["experiment_seed"])
    b = game_setup(domain, 3, EXP["experiment_seed"])
    assert a == b
    c = game_setup(domain, 4, EXP["experiment_seed"])
    assert c != a
    validate_setup(a)
    assert sorted(a.speaking_order) == [1, 2, 3, 4, 5]
    if domain == "aiwolf":
        assert sorted(s.role_slot for s in a.seats) == ["POSSESSED", "SEER", "VILLAGER", "VILLAGER", "WEREWOLF"]
        assert a.instance_id is None
    else:
        assert a.instance_id == f"{domain}_{(3 % 10) + 1:03d}"


@pytest.mark.parametrize("domain", DOMAINS)
def test_saved_setups_match_generator(domain):
    for k in (1, 17, 30):
        s = load_setup(f"{domain}_{k:04d}")
        assert s == game_setup(domain, k, EXP["experiment_seed"], s.info_mode)


def test_tiebreak_deterministic():
    assert choose(["B", "A"], "x_0001", 3) == choose(["A", "B"], "x_0001", 3)
    assert choose(["A"], "x", 1) == "A"
    t = tally({"p": "A", "q": "B", "r": None}, "x_0001", 3)
    assert t.tie and t.chosen in ("A", "B") and t.counts == {"A": 1, "B": 1}
    t2 = tally({"p": "A", "q": "A", "r": "B"}, "x_0001", 3)
    assert not t2.tie and t2.chosen == "A"
    assert tally({"p": None}, "x", 1).chosen is None


def test_logwriter_roundtrip(tmp_path: Path):
    names = ["Rin", "Kenji", "Mio", "Toshio", "Yuki"]
    w = GameLogWriter(tmp_path, "g1", names)
    w.header(setup_id="x_0001")
    w.status(0, "Rin", 1, "SEER", True)
    w.talk(0, 1, "Rin", 'Hi @Kenji, "quoted", and a, comma', raw='"Hi @Kenji, "quoted", and a, comma"')
    w.pass_(0, 2, "Kenji", "Skip", forced=True)
    w.vote(1, "Rin", None, raw="nobody", valid=False)
    w.action(1, "divine", "Rin", "Kenji", "HUMAN", result="HUMAN", valid=True)
    w.result(1, "VILLAGE", winner="VILLAGE")
    w.close()
    rows = read_log(tmp_path / "g1.log")
    assert [r.type for r in rows] == ["status", "talk", "pass", "vote", "action", "result"]
    assert [r.seq for r in rows] == list(range(6))
    t = rows[1]
    assert t.text == 'Hi @Kenji, "quoted", and a, comma'
    assert t.extra["mentions"] == ["Kenji"] and t.extra["words"] == 6 and t.extra["raw_differs"] is True
    assert rows[2].extra == {"forced": True, "empty": False}
    assert rows[3].extra["valid"] is False and rows[3].target == ""
    recs = list(read_jsonl(tmp_path / "g1.jsonl"))
    assert recs[0]["kind"] == "header" and recs[0]["game_id"] == "g1"


def test_logrow_csv_rejects_bad_type():
    with pytest.raises(ValueError):
        LogRow.from_csv(["0", "0", "", "chat", "", "", "", ""])


def test_words_and_mentions():
    assert count_words("a b  c") == 3
    assert find_mentions("@Rin and @Nobody and @Rin", ["Rin"]) == ["Rin"]


def test_normalize_winner():
    assert normalize_winner("village") == "VILLAGE"
    assert normalize_winner("WEREWOLF") == "WEREWOLF"
    assert normalize_winner("werewolves") == "WEREWOLF"
    assert normalize_winner(None) == "NONE"


def test_packet_roundtrip():
    info = Info(game_id="g", day=1, agent="Rin", status_map={"Rin": "ALIVE"}, role_map={"Rin": "SEER"},
                card_titles=["t1"], options=[{"label": "A", "name": "n", "summary": "s"}])
    p = Packet(Request.TALK, info, Setting(), [Talk(0, 1, 1, "Rin", "Skip", skip=True)], None)
    d = json.loads(json.dumps(p.to_dict()))
    q = Packet.from_dict(d)
    assert q.request == Request.TALK and q.info.card_titles == ["t1"] and q.talk_history[0].skip
    assert q.info.options[0]["label"] == "A"
    assert "divine_result" not in d["info"]  # None keys dropped


@pytest.mark.parametrize("domain", DOMAINS)
def test_shared_blocks_render(domain):
    ctx = GameContext.load(f"{domain}_0001")
    env = make_env()
    for b in ("setting", "structure", "schedule", "action"):
        txt = shared_block(env, ctx, b)
        assert txt and "{{" not in txt
    st = shared_block(env, ctx, "structure")
    assert f"{ctx.rules['word_cap']} words" in st
    assert ", ".join(ctx.speaking_order_names[:-1]) + " and " + ctx.speaking_order_names[-1] in st
    ident = identity_block(env, ctx, 1)
    assert ident.startswith(f"Name: {ctx.name_of_seat(1)}\n")
    assert ident.rstrip().splitlines()[-1].startswith(ctx.rules["private_seed_label"] + ": ")
    v = rules_context(ctx)
    assert v["n_options"] == (0 if domain == "aiwolf" else len(ctx.options()))


def test_fixed_mode_sentences_differ():
    ctx = GameContext.load("shared_living_0001")
    env = make_env()
    dyn = shared_block(env, ctx, "schedule")
    ctx.setup.info_mode = "fixed"
    fixed = shared_block(env, ctx, "schedule")
    assert dyn != fixed and "chosen for them" in fixed


def test_dynamic_ready_check_requires_titles():
    ctx = GameContext.load("shared_living_0001")
    ctx.check_dynamic_ready()  # real instances carry titles since the §9-9 rewrite
    for c in ctx.instance["card_pool"]:
        c["title"] = ""
    with pytest.raises(ValueError):
        ctx.check_dynamic_ready()
