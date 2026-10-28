"""Synthetic rows for every method-independent violation code (DESIGN §8, common/violations.py)."""
from __future__ import annotations

import pytest

from common.schema import LogRow
from common.setup import GameContext
from common.violations import (
    CARD_NGRAM,
    CODES,
    find_truncations,
    find_violations,
    merge_violations,
    partial_tokens,
    summarize,
)

AIWOLF = GameContext.load("aiwolf_0001")            # Kenji, Mizuki, Benjamin, Shizue, Minako
PANEL = GameContext.load("candidate_selection_0001")  # instance candidate_selection_002


def talk(seq, text, agent=None, rnd=1, turn=1, ctx=AIWOLF, **extra):
    return LogRow(seq, rnd, turn, "talk", agent or ctx.names[0], "", text, extra)


def pass_(seq, token, agent=None, rnd=1, turn=1, ctx=AIWOLF, **extra):
    e = {"forced": False, "empty": False}
    e.update(extra)
    return LogRow(seq, rnd, turn, "pass", agent or ctx.names[0], "", token, e)


def codes(rows, ctx=AIWOLF):
    return [v["code"] for v in find_violations(rows, ctx)]


def test_clean_talk_has_no_violations():
    rows = [talk(0, "I think we should hear from the Seer first. @Mizuki, what do you say?"),
            pass_(1, "Over"), pass_(2, "Skip", forced=True)]
    assert find_violations(rows, AIWOLF) == []


def test_over_cap():
    text = " ".join(["word"] * (int(AIWOLF.rules["word_cap"]) + 1))
    v = find_violations([talk(0, text)], AIWOLF)
    assert [x["code"] for x in v] == ["over_cap"]
    assert v[0]["detail"]["words"] == 41 and v[0]["detail"]["cap"] == 40 and v[0]["seq"] == 0
    assert codes([talk(1, " ".join(["w"] * 40))]) == []


@pytest.mark.parametrize("text", ["Kenji: hello everyone", "Kenji：hello", "**Kenji**: hello", "Kenji - hello", "[Kenji]: hi"])
def test_name_label(text):
    v = find_violations([talk(0, text, agent="Kenji")], AIWOLF)
    assert "name_label" in [x["code"] for x in v]
    assert v[0]["detail"]["name"] == "Kenji"


def test_name_label_not_for_plain_name_mention():
    assert codes([talk(0, "Kenji here. Let's begin."), talk(1, "Mizuki, what do you think?")]) == []
    assert codes([talk(2, "Mizuki said it was fine.")]) == []  # no quotation mark -> not reported speech


def test_multi_utt_and_speak_for_others():
    v = find_violations([talk(0, "I vote Shizue.\nMizuki: I agree.\nKenji: Thanks.", agent="Kenji")], AIWOLF)
    c = {x["code"]: x for x in v}
    assert set(c) == {"multi_utt", "speak_for_others"}
    assert c["multi_utt"]["detail"]["names"] == ["Mizuki", "Kenji"]
    assert c["speak_for_others"]["detail"]["names"] == ["Mizuki"]
    # a second line in the speaker's own voice is multi_utt but not speak_for_others
    v2 = find_violations([talk(1, "First thought.\nKenji: second thought.", agent="Kenji")], AIWOLF)
    assert [x["code"] for x in v2] == ["multi_utt"]


def test_speak_for_others_reported_speech():
    v = find_violations([talk(0, 'Earlier Benjamin said "I am the Seer" and I believe him.', agent="Kenji")], AIWOLF)
    assert [x["code"] for x in v] == ["speak_for_others"]
    assert v[0]["detail"]["names"] == ["Benjamin"]


def test_pass_punct_on_pass_rows_and_talk_rows():
    rows = [pass_(0, "Over", raw="Over."), pass_(1, "Skip", raw="skip"), pass_(2, "Over", raw=" Over "),
            talk(3, '"Over"'), talk(4, "over."), talk(5, "Skip!"), talk(6, "Over is what I say.")]
    v = find_violations(rows, AIWOLF)
    assert [(x["seq"], x["code"]) for x in v] == [(0, "pass_punct"), (1, "pass_punct"), (3, "pass_punct"),
                                                  (4, "pass_punct"), (5, "pass_punct")]
    assert v[0]["detail"] == {"token": "Over", "raw": "Over."}
    assert v[3]["detail"]["token"] == "Over"


@pytest.mark.parametrize("text,kind", [
    ("## Day 1\nI am a villager.", "heading"),
    ("I **really** mean it.", "bold"),
    ("[laughs] That was funny.", "bracket"),
    ("(laughs) I do not think so.", "paren_stage"),
    ("(leans forward) Listen to me.", "paren_stage"),
    ("*nods slowly* Yes.", "asterisk_stage"),
    ("Turn 2\nI vote for Shizue.", "scaffold"),
    ("Round 1: hello", "scaffold"),
    ("Fine.\n---\nMore.", "hrule"),
])
def test_format_noise(text, kind):
    v = find_violations([talk(0, text)], AIWOLF)
    noise = [x for x in v if x["code"] == "format_noise"]
    assert len(noise) == 1 and kind in noise[0]["detail"]["kinds"]


def test_format_noise_ignores_ordinary_parentheses_and_mentions():
    assert codes([talk(0, "I agree (mostly) with @Mizuki and the plan (see day 1)."),
                  talk(1, "We go in turn, two at a time.")]) == []


def test_early_reveal_option_name_before_round_3():
    name = PANEL.options()[1]["name"]
    rows = [talk(0, f"I lean towards the {name.lower()} idea.", rnd=1, ctx=PANEL),
            talk(1, f"The {name} is better.", rnd=2, ctx=PANEL),
            talk(2, f"The {name} is better.", rnd=3, ctx=PANEL)]
    v = find_violations(rows, PANEL)
    assert [(x["seq"], x["code"], x["detail"]["kind"]) for x in v] == [
        (0, "early_reveal", "option_name"), (1, "early_reveal", "option_name")]
    assert v[0]["detail"]["names"] == [name]
    # word boundary: a prefix of the name is not a hit
    first = name.split()[0]
    assert codes([talk(3, f"{first}ing is not a word.", rnd=1, ctx=PANEL)], PANEL) == []


def test_early_reveal_card_text_round_1_only():
    card = PANEL.card_pool()[3]
    words = card["text"].split()[: CARD_NGRAM + 2]
    quote = " ".join(words)
    rows = [talk(0, f"Someone told me that {quote.upper()}, really.", rnd=1, ctx=PANEL),
            talk(1, f"Someone told me that {quote}, really.", rnd=2, ctx=PANEL),
            talk(2, " ".join(words[: CARD_NGRAM - 1]), rnd=1, ctx=PANEL)]
    v = find_violations(rows, PANEL)
    assert len(v) == 1 and v[0]["seq"] == 0 and v[0]["detail"]["kind"] == "card_text"
    assert v[0]["detail"]["card_id"] == card["card_id"]


def test_early_reveal_not_in_aiwolf():
    rows = [talk(0, "Workflow Assistant Supplier Data Hub", rnd=0)]
    assert codes(rows) == []


def test_trailing_over():
    v = find_violations([talk(0, "I have nothing further. Over."), talk(1, "Abstain. over"),
                         talk(2, "See you tomorrow, skip!"), talk(3, "Over"), talk(4, "Over."),
                         talk(5, "The game is not over yet, is it?"), talk(6, "Overall fine.")], AIWOLF)
    got = [(x["seq"], x["code"], x["detail"].get("token")) for x in v]
    # only the exact token counts ("over" / "skip!" in lower case are ordinary words)
    assert got == [(0, "trailing_over", "Over"), (4, "pass_punct", "Over")]
    assert all(x["kind"] == "normalized" for x in v)


def test_partial_tokens_and_early_reveal_partial():
    assert partial_tokens("Mountain Training Centre") == ["Mountain", "Training"]
    assert partial_tokens("Campus Intensive") == ["Campus", "Intensive"]
    assert partial_tokens("Fixed Weekly Rota") == []           # all stopwords / < 5 letters
    assert partial_tokens("Per-Room Metering") == ["Metering"]
    # candidate_selection_0001 -> instance 002: Microbiome Atlas / Protein Folding Dynamics / ...
    opts = PANEL.options()
    o = opts[1]
    tok = partial_tokens(o["name"])[0]
    rows = [talk(0, f"I would rather look at {tok.lower()} data first.", rnd=1, ctx=PANEL),
            talk(1, f"I would rather look at {tok.lower()} data first.", rnd=3, ctx=PANEL),
            talk(2, f"{tok}s are interesting.", rnd=2, ctx=PANEL),          # plural: not a whole word
            talk(3, f"The {o['name']} is better.", rnd=2, ctx=PANEL)]       # full name: early_reveal only
    v = find_violations(rows, PANEL)
    assert [(x["seq"], x["code"]) for x in v] == [(0, "early_reveal_partial"), (3, "early_reveal")]
    assert v[0]["detail"] == {"token": tok, "label": o["label"], "name": o["name"]}


def test_merge_violations_keeps_structural_and_dedups():
    structural = [{"seq": None, "line": 3, "code": "format_noise", "detail": "code fence"},
                  {"seq": None, "line": None, "code": "llm_error", "detail": "boom"},
                  {"seq": 4, "line": 20, "code": "dead_actor", "detail": "x"},
                  {"seq": 1, "code": "over_cap", "detail": {"words": 99, "cap": 40}},   # stale common item
                  {"seq": None, "line": None, "code": "truncated", "detail": "finish_reason=length"}]
    common = [{"seq": 1, "code": "over_cap", "detail": {"words": 41, "cap": 40}},
              {"seq": 1, "code": "over_cap", "detail": {"words": 41, "cap": 40}},
              {"seq": 0, "code": "truncated", "detail": {"source": "llm_call"}}]
    out = merge_violations(structural, common)
    assert out == structural[:3] + [common[0], common[2]]


def test_find_truncations_and_summarize():
    recs = [{"kind": "header", "game_id": "x"},
            {"kind": "llm_call", "seq": 3, "seat_seq": 7, "seat": 2, "request": "TALK", "round": 1, "turn": 2,
             "finish_reason": "length", "truncated": True},
            {"kind": "llm_call", "seq": 4, "seat": 2, "request": "VOTE", "round": 1, "finish_reason": "stop",
             "truncated": False},
            {"kind": "llm_call", "seq": 5, "seat": "writer", "request": "FULL", "finish_reason": "length"}]
    t = find_truncations(recs)
    assert [(x["seq"], x["code"]) for x in t] == [(3, "truncated"), (5, "truncated")]
    assert t[0]["detail"] == {"source": "llm_call", "seat": 2, "seat_seq": 7, "request": "TALK", "round": 1, "turn": 2,
                              "finish_reason": "length"}
    assert t[0]["detail"]["seat"] == 2 and t[0]["detail"]["turn"] == 2
    s = summarize(t + find_violations([talk(0, "Kenji: hi", agent="Kenji"), pass_(1, "Over", raw="Over.")], AIWOLF))
    assert list(s) == list(CODES)
    assert s["truncated"] == 2 and s["name_label"] == 1 and s["pass_punct"] == 1 and s["over_cap"] == 0
