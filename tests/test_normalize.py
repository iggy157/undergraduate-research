"""common.normalize: the one normalisation shared by the server (multi) and the single converter."""
from __future__ import annotations

from common.convert.single_markdown import convert
from common.normalize import normalize_talk
from common.setup import GameContext
from common.violations import find_violations


def test_pass_variants_and_notes():
    for raw, kind, tok in (("Over.", "over", "Over"), ('"Skip"', "skip", "Skip"), ("over", "over", "Over"),
                           ("Skip", "skip", "Skip")):
        n = normalize_talk(raw, "Kenji")
        assert (n.kind, n.text) == (kind, tok)
        assert [x["code"] for x in n.notes] == ([] if raw == tok else ["pass_punct"])
    assert normalize_talk(None, "Kenji").flags == {"forced": True}
    assert normalize_talk("", "Kenji").kind == "over" and normalize_talk("", "Kenji").flags == {"empty": True}


def test_own_label_wrap_and_trailing_over():
    n = normalize_talk("**Kenji**: Hello\nsecond line", "Kenji")
    assert n.kind == "talk" and n.text == "Hello\nsecond line" and n.notes[0]["code"] == "name_label"
    n = normalize_talk('"Quoted whole."', "Kenji")
    assert n.text == "Quoted whole." and n.notes[0] == {"code": "format_noise", "kinds": ["wrap"], "raw": '"Quoted whole."'}
    n = normalize_talk("See you tomorrow. Over.", "Kenji")
    assert n.text == "See you tomorrow." and n.over_after and n.notes[0]["code"] == "trailing_over"
    # another participant's label stays (speak_for_others is judged later); ordinary words are untouched
    assert normalize_talk("Mizuki: I agree", "Kenji").text == "Mizuki: I agree"
    for s in ("Turn it over.", "Fine, over there it goes.", "The game is not over yet, is it?"):
        n = normalize_talk(s, "Kenji")
        assert n.text == s and not n.over_after and n.notes == []


def test_converter_joins_continuation_lines_and_handles_trailing_over():
    ctx = GameContext.load("aiwolf_0001")
    order = ctx.speaking_order_names
    seats = "\n".join(f"| {s.seat} | {s.persona} | {s.role_slot.capitalize()} |" for s in ctx.setup.seats)
    md = (f"# aiwolf_0001\n## Participants\n| Seat | Name | Role |\n|---|---|---|\n{seats}\n"
          "## Day 0\n### Talk\n#### Turn 1 of 4\n"
          f"- **{order[0]}**: First line of a long thought.\nSecond line of the same utterance.\n"
          f"- **{order[1]}**: I have nothing to add. Over.\n"
          + "".join(f"- **{n}**: Over\n" for n in order[2:])
          + "#### Turn 2 of 4\n"
          f"- **{order[0]}**: Over\n"
          "### Action\n- divine: Benjamin -> Shizue (werewolf)\n"
          "## Day 1\n### Talk\n#### Turn 1 of 4\n" + "".join(f"- **{n}**: Over\n" for n in order)
          + "### Vote\n" + "".join(f"- {n} -> Shizue\n" for n in order) + "- execution: Shizue\n"
          "## Result\n- winner: village\n")
    res = convert(md, ctx, "g")
    talks = [r for r in res.rows if r.type == "talk"]
    assert talks[0].text == "First line of a long thought.\nSecond line of the same utterance."
    assert talks[1].text == "I have nothing to add." and talks[1].extra["norm"][0]["code"] == "trailing_over"
    trailing = [r for r in res.rows if r.type == "pass" and r.agent == order[1] and r.round == 0]
    assert len(trailing) == 1 and trailing[0].extra.get("trailing") is True and trailing[0].turn == 1
    assert not [v for v in res.violations if v["code"] in ("missing_turn", "format_noise", "talk_after_over")]
    items = find_violations(res.rows, ctx)
    assert [(i["code"], i["kind"]) for i in items] == [("trailing_over", "normalized")]
