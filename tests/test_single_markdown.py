"""common/convert/single_markdown: valid transcripts for the three domains, every violation code, garbage."""
from __future__ import annotations

import random
import re

import pytest

from common.convert.single_markdown import convert
from common.setup import GameContext
from common.tiebreak import tally

# ---- fixtures ---------------------------------------------------------------------------------
# aiwolf_0001: seats Kenji(POSSESSED) Mizuki(VILLAGER) Benjamin(SEER) Shizue(WEREWOLF) Minako(VILLAGER)
#              speaking order Minako, Shizue, Mizuki, Benjamin, Kenji
# candidate_selection_0001: Midori Benjamin Toshio Kenji Servas; order Servas, Midori, Kenji, Benjamin, Toshio; A-D
# shared_living_0001: Misaki Ryuji Rin Mio Shizue; order Mio, Shizue, Ryuji, Rin, Misaki; A-C

AIWOLF_HEAD = """# aiwolf_0001
## Participants
| Seat | Name | Role |
|---|---|---|
| 1 | Kenji | Possessed |
| 2 | Mizuki | Villager |
| 3 | Benjamin | Seer |
| 4 | Shizue | Werewolf |
| 5 | Minako | Villager |
"""

VILLAGE_MD = AIWOLF_HEAD + """## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Good morning everyone. Let us share what we know.
- **Shizue**: Nothing yet from me, but I am listening.
- **Mizuki**: I am a villager, so I will just watch for lies.
- **Benjamin**: I will divine tonight and report tomorrow.
- **Kenji**: Sounds good, @Benjamin, please pick carefully.
#### Turn 2 of 4
- **Minako**: Skip
- **Shizue**: I agree with waiting for the Seer.
- **Mizuki**: Over
- **Benjamin**: Noted.
- **Kenji**: Same here.
#### Turn 3 of 4
- **Minako**: Over
- **Shizue**: Over
- **Benjamin**: Over
- **Kenji**: Over
#### Turn 4 of 4
### Action
- divine: Benjamin -> Shizue (werewolf)
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: Benjamin, what did you see?
- **Shizue**: I hope the Seer has good news.
- **Mizuki**: Let us hear it.
- **Benjamin**: I am the Seer. Shizue is the werewolf.
- **Kenji**: That is a strong claim, @Benjamin.
#### Turn 2 of 4
- **Minako**: I believe Benjamin. Vote Shizue.
- **Shizue**: He is lying! I am a villager.
- **Mizuki**: Over
- **Benjamin**: Over
- **Kenji**: Over
#### Turn 3 of 4
- **Minako**: Over
- **Shizue**: Over
#### Turn 4 of 4
### Vote
- Minako -> Shizue
- Shizue -> Benjamin
- Mizuki -> Shizue
- Benjamin -> Shizue
- Kenji -> Benjamin
- execution: Shizue
## Result
- winner: village
"""

WOLF_MD = AIWOLF_HEAD + """## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Hello all.
- **Shizue**: Hello.
- **Mizuki**: Hi.
- **Benjamin**: Greetings.
- **Kenji**: Hey.
#### Turn 2 of 4
- **Minako**: Over
- **Shizue**: Over
- **Mizuki**: Over
- **Benjamin**: Over
- **Kenji**: Over
### Action
- divine: Benjamin -> Minako (human)
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: I suspect Mizuki.
- **Shizue**: So do I.
- **Mizuki**: That is unfair.
- **Benjamin**: Minako is human, I checked.
- **Kenji**: Mizuki it is.
#### Turn 2 of 4
- **Minako**: Over
- **Shizue**: Over
- **Mizuki**: Over
- **Benjamin**: Over
- **Kenji**: Over
### Vote
- Minako -> Mizuki
- Shizue -> Mizuki
- Mizuki -> Shizue
- Benjamin -> Mizuki
- Kenji -> Mizuki
- execution: Mizuki
### Action
- divine: Benjamin -> Kenji (human)
- attack: Shizue -> Benjamin
## Day 2
### Talk
#### Turn 1 of 4
- **Minako**: Benjamin is gone. Shizue, was it you?
- **Shizue**: No, I think Minako is the wolf.
- **Kenji**: I agree with Shizue.
#### Turn 2 of 4
- **Minako**: Over
- **Shizue**: Over
- **Kenji**: Over
### Vote
- Minako -> Shizue
- Shizue -> Minako
- Kenji -> Minako
- execution: Minako
## Result
- winner: werewolves
"""

CS_FIXED_MD = """# candidate_selection_0001
## Participants
| Seat | Name |
|---|---|
| 1 | Midori |
| 2 | Benjamin |
| 3 | Toshio |
| 4 | Kenji |
| 5 | Servas |
## Round 1
### Talk
#### Turn 1 of 4
- **Servas**: Let us begin by sharing what worries each of us.
- **Midori**: My concern is where the money really comes from.
- **Kenji**: Shared facilities are my worry.
- **Benjamin**: Interruptions outside the science itself.
- **Toshio**: Whether our picks deliver in the end.
#### Turn 2 of 4
- **Servas**: Over
- **Midori**: Over
- **Kenji**: Over
- **Benjamin**: Skip
- **Toshio**: Over
#### Turn 3 of 4
- **Benjamin**: Over
#### Turn 4 of 4
## Round 2
### Talk
#### Turn 1 of 4
- **Servas**: I learned that technicians are scarce.
- **Midori**: Travel budgets are frozen, I found.
- **Kenji**: The animal facility is accredited again.
- **Benjamin**: The spectroscopy suite sat idle for weeks.
- **Toshio**: Catalogue projects keep being used for years.
#### Turn 2 of 4
- **Servas**: Over
- **Midori**: Over
- **Kenji**: Over
- **Benjamin**: Over
- **Toshio**: Over
## Round 3
### Talk
#### Turn 1 of 4
- **Servas**: Now that we see the candidates, I lean to A.
- **Midori**: A looks affordable to me too.
- **Kenji**: B depends on facilities that are strained.
- **Benjamin**: I prefer B for its science.
- **Toshio**: A has the better track record.
#### Turn 2 of 4
- **Servas**: Over
- **Midori**: Over
- **Kenji**: Over
- **Benjamin**: Over
- **Toshio**: Over
### Vote
- Servas -> A
- Midori -> A
- Kenji -> A
- Benjamin -> B
- Toshio -> A
- adopted: A
## Result
- adopted: A
"""

SL_TITLES = ["Cleaning time log", "Supply costs", "Bathroom state", "Fairness survey", "Cleaner quotes",
             "Allergy note", "Schedule clashes", "Guest frequency", "Rota history", "Key handover"]

SL_DYNAMIC_MD = """# shared_living_0001
## Participants
| Seat | Name |
|---|---|
| 1 | Misaki |
| 2 | Ryuji |
| 3 | Rin |
| 4 | Mio |
| 5 | Shizue |
## Round 1
### Talk
#### Turn 1 of 4
- **Mio**: The bathroom is my main worry.
- **Shizue**: Who pays for supplies bothers me.
- **Ryuji**: I want to know the real hours.
- **Rin**: It does not feel even.
- **Misaki**: Guests make a mess too.
#### Turn 2 of 4
- **Mio**: Over
- **Shizue**: Over
- **Ryuji**: Over
- **Rin**: Over
- **Misaki**: Over
### Action
- investigate: Misaki -> Guest frequency; Key handover
- investigate: Ryuji -> cleaning time log; Schedule clashes
- investigate: Rin -> Fairness survey; Rota history
- investigate: Mio -> Bathroom state; Allergy note
- investigate: Shizue -> Supply costs; Cleaner quotes
## Round 2
### Talk
#### Turn 1 of 4
- **Mio**: The bathroom state log was grim.
- **Shizue**: Cleaners cost more than I thought.
- **Ryuji**: The time log shows long hours.
- **Rin**: The survey confirms the unfairness.
- **Misaki**: Guests come more often than we admit.
#### Turn 2 of 4
- **Mio**: Over
- **Shizue**: Over
- **Ryuji**: Over
- **Rin**: Over
- **Misaki**: Over
## Round 3
### Talk
#### Turn 1 of 4
- **Mio**: A rota keeps the bathroom predictable.
- **Shizue**: B is too expensive for us.
- **Ryuji**: A spreads the hours.
- **Rin**: A is the fairest.
- **Misaki**: C would let me pick my timing.
#### Turn 2 of 4
- **Mio**: Over
- **Shizue**: Over
- **Ryuji**: Over
- **Rin**: Over
- **Misaki**: Over
### Vote
- Mio -> A
- Shizue -> A
- Ryuji -> A
- Rin -> A
- Misaki -> C
- adopted: A
## Result
- adopted: A
"""


@pytest.fixture
def aiwolf() -> GameContext:
    return GameContext.load("aiwolf_0001")


@pytest.fixture
def cs_fixed() -> GameContext:
    ctx = GameContext.load("candidate_selection_0001")
    ctx.setup.info_mode = "fixed"
    return ctx


@pytest.fixture
def sl_dynamic() -> GameContext:
    ctx = GameContext.load("shared_living_0001")
    for c, t in zip(ctx.instance["card_pool"], SL_TITLES):  # titles are empty in data/ until DESIGN §9-9
        c["title"] = t
    ctx.check_dynamic_ready()
    return ctx


def codes(res) -> set[str]:
    return {v["code"] for v in res.violations}


def sig(rows) -> list[tuple]:
    return [(r.round, r.turn, r.type, r.agent, r.target, r.text) for r in rows]


def status_block(round_no: int, alive: dict[str, bool], ctx: GameContext) -> list[tuple]:
    return [(round_no, None, "status", s.persona, "", "ALIVE" if alive.get(s.persona, True) else "DEAD")
            for s in ctx.setup.seats]


# ---- valid transcripts -------------------------------------------------------------------------
def test_aiwolf_village_win_exact_rows(aiwolf):
    res = convert(VILLAGE_MD, aiwolf, "g")
    assert res.violations == []
    ms, sh, mz, bj, kj = "Minako", "Shizue", "Mizuki", "Benjamin", "Kenji"
    expected = status_block(0, {}, aiwolf) + [
        (0, 1, "talk", ms, "", "Good morning everyone. Let us share what we know."),
        (0, 1, "talk", sh, "", "Nothing yet from me, but I am listening."),
        (0, 1, "talk", mz, "", "I am a villager, so I will just watch for lies."),
        (0, 1, "talk", bj, "", "I will divine tonight and report tomorrow."),
        (0, 1, "talk", kj, "", "Sounds good, @Benjamin, please pick carefully."),
        (0, 2, "pass", ms, "", "Skip"),
        (0, 2, "talk", sh, "", "I agree with waiting for the Seer."),
        (0, 2, "pass", mz, "", "Over"),
        (0, 2, "talk", bj, "", "Noted."),
        (0, 2, "talk", kj, "", "Same here."),
        (0, 3, "pass", ms, "", "Over"),
        (0, 3, "pass", sh, "", "Over"),
        (0, 3, "pass", bj, "", "Over"),
        (0, 3, "pass", kj, "", "Over"),
        (0, None, "action", bj, sh, "WEREWOLF"),
    ] + status_block(1, {}, aiwolf) + [
        (1, 1, "talk", ms, "", "Benjamin, what did you see?"),
        (1, 1, "talk", sh, "", "I hope the Seer has good news."),
        (1, 1, "talk", mz, "", "Let us hear it."),
        (1, 1, "talk", bj, "", "I am the Seer. Shizue is the werewolf."),
        (1, 1, "talk", kj, "", "That is a strong claim, @Benjamin."),
        (1, 2, "talk", ms, "", "I believe Benjamin. Vote Shizue."),
        (1, 2, "talk", sh, "", "He is lying! I am a villager."),
        (1, 2, "pass", mz, "", "Over"),
        (1, 2, "pass", bj, "", "Over"),
        (1, 2, "pass", kj, "", "Over"),
        (1, 3, "pass", ms, "", "Over"),
        (1, 3, "pass", sh, "", "Over"),
        (1, None, "vote", ms, sh, ""),   # votes in the order written (speaking order), like the server
        (1, None, "vote", sh, bj, ""),
        (1, None, "vote", mz, sh, ""),
        (1, None, "vote", bj, sh, ""),
        (1, None, "vote", kj, bj, ""),
        (1, None, "action", "", sh, sh),
    ] + status_block(2, {sh: False}, aiwolf) + [(1, None, "result", "", "", "VILLAGE")]
    assert sig(res.rows) == expected
    assert [r.seq for r in res.rows] == list(range(len(expected)))
    # extras
    by = {(r.round, r.turn, r.type, r.agent): r for r in res.rows}
    assert by[(0, 1, "talk", kj)].extra == {"words": 6, "mentions": ["Benjamin"], "raw_differs": False}
    assert by[(0, 2, "pass", ms)].extra == {"forced": False, "empty": False}
    assert by[(1, None, "vote", kj)].extra == {"request": "vote_day", "raw": "Benjamin", "valid": True, "tie": False}
    assert by[(0, None, "action", bj)].extra == {"action": "divine", "result": "WEREWOLF", "valid": True}
    assert by[(1, None, "action", "")].extra == {"action": "execute", "role": "WEREWOLF", "tie": False}
    assert by[(0, None, "status", kj)].extra == {"seat": 1, "role": "POSSESSED", "alive": True}
    assert by[(2, None, "status", sh)].extra == {"seat": 4, "role": "WEREWOLF", "alive": False}
    assert res.rows[-1].extra == {"winner": "VILLAGE", "villagers": 4, "werewolves": 0, "reason": None}
    assert res.outcome == {"winner": "VILLAGE", "villagers": 4, "werewolves": 0, "reason": None}


def test_aiwolf_werewolf_win_with_attack(aiwolf):
    res = convert(WOLF_MD, aiwolf, "g")
    assert res.violations == []
    actions = [(r.round, r.extra["action"], r.agent, r.target, r.extra) for r in res.rows if r.type == "action"]
    assert actions == [
        (0, "divine", "Benjamin", "Minako", {"action": "divine", "result": "HUMAN", "valid": True}),
        (1, "execute", "", "Mizuki", {"action": "execute", "role": "VILLAGER", "tie": False}),
        (1, "divine", "Benjamin", "Kenji", {"action": "divine", "result": "HUMAN", "valid": True}),
        (1, "attack", "Shizue", "Benjamin", {"action": "attack", "success": True, "no_target": False}),
        (2, "execute", "", "Minako", {"action": "execute", "role": "VILLAGER", "tie": False}),
    ]
    # the order inside a day is Talk -> Vote -> execute -> divine -> attack
    kinds = [(r.type, r.extra.get("action")) for r in res.rows if r.round == 1 and r.type in ("vote", "action")]
    assert kinds == [("vote", None)] * 5 + [("action", "execute"), ("action", "divine"), ("action", "attack")]
    # day 2 status: Mizuki and Benjamin dead; the dead have no talk rows
    st2 = {r.agent: r.extra["alive"] for r in res.rows if r.type == "status" and r.round == 2}
    assert st2 == {"Kenji": True, "Mizuki": False, "Benjamin": False, "Shizue": True, "Minako": True}
    assert not [r for r in res.rows if r.round == 2 and r.type == "talk" and r.agent in ("Mizuki", "Benjamin")]
    assert res.rows[-1].type == "result" and res.rows[-1].round == 2
    assert res.rows[-1].extra == {"winner": "WEREWOLF", "villagers": 1, "werewolves": 1, "reason": None}
    assert res.outcome["winner"] == "WEREWOLF"
    final = [r for r in res.rows if r.type == "status" and r.round == 3]
    assert len(final) == 5 and final[-2].agent == "Shizue" and final[-2].extra["alive"]


def test_aiwolf_tie_uses_common_tiebreak(aiwolf):
    votes = {"Minako": "Shizue", "Shizue": "Benjamin", "Mizuki": "Shizue", "Benjamin": "Kenji", "Kenji": "Benjamin"}
    t = tally(votes, "aiwolf_0001", 1)
    assert t.tie and t.chosen == "Benjamin"
    md = VILLAGE_MD.replace("- Benjamin -> Shizue\n", "- Benjamin -> Kenji\n").replace("- execution: Shizue", "- execution: Benjamin")
    # after Benjamin (Seer) is executed the game continues; the writer stops -> incomplete, but no tally_mismatch
    res = convert(md, aiwolf, "g")
    ex = [r for r in res.rows if r.type == "action" and r.extra["action"] == "execute"]
    assert ex[0].target == "Benjamin" and ex[0].extra == {"action": "execute", "role": "SEER", "tie": True}
    assert "tally_mismatch" not in codes(res)


def test_candidate_selection_fixed_exact_rows(cs_fixed):
    res = convert(CS_FIXED_MD, cs_fixed, "g")
    assert res.violations == []
    sv, md, kj, bj, ts = "Servas", "Midori", "Kenji", "Benjamin", "Toshio"
    by_id = {c["card_id"]: c for c in cs_fixed.card_pool()}

    def t(*ids):
        return "; ".join(by_id[i]["title"] or i for i in ids)

    expected = status_block(1, {}, cs_fixed) + [
        (1, 1, "talk", sv, "", "Let us begin by sharing what worries each of us."),
        (1, 1, "talk", md, "", "My concern is where the money really comes from."),
        (1, 1, "talk", kj, "", "Shared facilities are my worry."),
        (1, 1, "talk", bj, "", "Interruptions outside the science itself."),
        (1, 1, "talk", ts, "", "Whether our picks deliver in the end."),
        (1, 2, "pass", sv, "", "Over"), (1, 2, "pass", md, "", "Over"), (1, 2, "pass", kj, "", "Over"),
        (1, 2, "pass", bj, "", "Skip"), (1, 2, "pass", ts, "", "Over"),
        (1, 3, "pass", bj, "", "Over"),
        (1, None, "action", sv, "", t("card_09", "card_10")),   # fixed cards in speaking order, like the server;
        (1, None, "action", md, "", t("card_01", "card_02")),   # titles (since the §9-9 rewrite) as text
        (1, None, "action", kj, "", t("card_07", "card_08")),
        (1, None, "action", bj, "", t("card_03", "card_04")),
        (1, None, "action", ts, "", t("card_05", "card_06")),
    ] + status_block(2, {}, cs_fixed) + [
        (2, 1, "talk", sv, "", "I learned that technicians are scarce."),
        (2, 1, "talk", md, "", "Travel budgets are frozen, I found."),
        (2, 1, "talk", kj, "", "The animal facility is accredited again."),
        (2, 1, "talk", bj, "", "The spectroscopy suite sat idle for weeks."),
        (2, 1, "talk", ts, "", "Catalogue projects keep being used for years."),
    ] + [(2, 2, "pass", n, "", "Over") for n in (sv, md, kj, bj, ts)] + status_block(3, {}, cs_fixed) + [
        (3, 1, "talk", sv, "", "Now that we see the candidates, I lean to A."),
        (3, 1, "talk", md, "", "A looks affordable to me too."),
        (3, 1, "talk", kj, "", "B depends on facilities that are strained."),
        (3, 1, "talk", bj, "", "I prefer B for its science."),
        (3, 1, "talk", ts, "", "A has the better track record."),
    ] + [(3, 2, "pass", n, "", "Over") for n in (sv, md, kj, bj, ts)] + [
        (3, None, "vote", sv, "A", ""), (3, None, "vote", md, "A", ""), (3, None, "vote", kj, "A", ""),
        (3, None, "vote", bj, "B", ""), (3, None, "vote", ts, "A", ""),
    ] + status_block(4, {}, cs_fixed) + [(3, None, "result", "", "", "A")]
    assert sig(res.rows) == expected
    assert [r.seq for r in res.rows] == list(range(len(expected)))
    inv = [r for r in res.rows if r.type == "action"]
    assert [r.extra for r in inv] == [{"action": "investigate", "cards": cs_fixed.instance["fixed_assignment"][str(s)],
                                       "parse": "fixed"} for s in cs_fixed.setup.speaking_order]
    assert res.rows[-1].extra == {"adopted": "A", "tally": {"A": 4, "B": 1}, "tie": False}
    assert res.outcome == {"adopted": "A", "tally": {"A": 4, "B": 1}, "tie": False}
    votes = [r for r in res.rows if r.type == "vote"]
    assert all(r.extra == {"request": "vote_final", "raw": r.target, "valid": True, "tie": False} for r in votes)
    assert all(r.extra == {"seat": s, "role": "PARTICIPANT", "alive": True}
               for s, r in enumerate([r for r in res.rows if r.type == "status"][:5], 1))


def test_shared_living_dynamic_exact_rows(sl_dynamic):
    res = convert(SL_DYNAMIC_MD, sl_dynamic, "g")
    assert res.violations == []
    inv = [(r.agent, r.target, r.text, r.extra) for r in res.rows if r.type == "action"]
    assert inv == [
        ("Misaki", "", "Guest frequency; Key handover",
         {"action": "investigate", "cards": ["card_08", "card_10"], "parse": "ok"}),
        ("Ryuji", "", "Cleaning time log; Schedule clashes",   # case-insensitive title match
         {"action": "investigate", "cards": ["card_01", "card_07"], "parse": "ok"}),
        ("Rin", "", "Fairness survey; Rota history",
         {"action": "investigate", "cards": ["card_04", "card_09"], "parse": "ok"}),
        ("Mio", "", "Bathroom state; Allergy note",
         {"action": "investigate", "cards": ["card_03", "card_06"], "parse": "ok"}),
        ("Shizue", "", "Supply costs; Cleaner quotes",
         {"action": "investigate", "cards": ["card_02", "card_05"], "parse": "ok"}),
    ]
    types = [r.type for r in res.rows]
    assert types[:5] == ["status"] * 5 and types[5:10] == ["talk"] * 5 and types[10:15] == ["pass"] * 5
    assert types[15:20] == ["action"] * 5 and types[20:25] == ["status"] * 5
    votes = [(r.agent, r.target, r.extra) for r in res.rows if r.type == "vote"]
    assert votes == [("Mio", "A", {"request": "vote_final", "raw": "A", "valid": True, "tie": False}),
                     ("Shizue", "A", {"request": "vote_final", "raw": "A", "valid": True, "tie": False}),
                     ("Ryuji", "A", {"request": "vote_final", "raw": "A", "valid": True, "tie": False}),
                     ("Rin", "A", {"request": "vote_final", "raw": "A", "valid": True, "tie": False}),
                     ("Misaki", "C", {"request": "vote_final", "raw": "C", "valid": True, "tie": False})]
    assert res.outcome == {"adopted": "A", "tally": {"A": 4, "C": 1}, "tie": False}
    assert res.rows[-1].round == 3 and res.rows[-6].round == 4 and res.rows[-6].type == "status"


def test_discussion_tie_recomputed_with_tiebreak(sl_dynamic):
    md = SL_DYNAMIC_MD.replace("- Rin -> A\n", "- Rin -> C\n").replace("- Shizue -> A\n", "- Shizue -> C\n")
    t = tally({"Mio": "A", "Shizue": "C", "Ryuji": "A", "Rin": "C", "Misaki": "C"}, "shared_living_0001", 3)
    assert t.tie is False and t.chosen == "C"
    md = md.replace("- adopted: A", "- adopted: C")
    res = convert(md, sl_dynamic, "g")
    assert res.violations == []
    assert res.outcome["adopted"] == "C" and res.outcome["tally"] == {"A": 2, "C": 3}
    md2 = md.replace("- Misaki -> C\n", "- Misaki -> B\n")
    t2 = tally({"Mio": "A", "Shizue": "C", "Ryuji": "A", "Rin": "C", "Misaki": "B"}, "shared_living_0001", 3)
    assert t2.tie and t2.top == ["A", "C"]
    res2 = convert(md2, sl_dynamic, "g")  # the writer adopted C, a tied top candidate
    assert res2.outcome["adopted"] == "C" and res2.rows[-1].extra["tie"] is True and res2.rows[-1].text == "C"
    assert all(r.extra["tie"] is True for r in res2.rows if r.type == "vote")
    assert "tally_mismatch" not in codes(res2)
    if t2.chosen == "C":
        assert res2.violations == [] and "rule_choice" not in res2.rows[-1].extra
    else:
        assert codes(res2) == {"tie_choice_differs"} and res2.rows[-1].extra["rule_choice"] == t2.chosen
    # the other tied label written instead: symmetric
    other = next(x for x in t2.top if x != t2.chosen)
    md2b = md2.replace("- adopted: C", f"- adopted: {other}").replace("\n- adopted: C", f"\n- adopted: {other}")
    md2b = md2b.replace("## Result\n- adopted: C", f"## Result\n- adopted: {other}")
    res2b = convert(md2b, sl_dynamic, "g")
    assert res2b.outcome["adopted"] == other
    assert ("tie_choice_differs" in codes(res2b)) == (other != t2.chosen)
    # a label that is not a top candidate is a real miscount: overridden with the rule's choice
    md2c = md2.replace("- adopted: C", "- adopted: B")
    res2c = convert(md2c, sl_dynamic, "g")
    assert "tally_mismatch" in codes(res2c) and "tie_choice_differs" not in codes(res2c)
    assert res2c.outcome["adopted"] == t2.chosen and "rule_choice" not in res2c.rows[-1].extra
    # label forms accepted exactly as the multi server's match_option does
    name_a, name_c = sl_dynamic.options()[0]["name"], sl_dynamic.options()[2]["name"]
    md3 = md.replace("- Mio -> A\n", "- Mio -> Option a.\n").replace("- Ryuji -> A\n", f"- Ryuji -> {name_a}\n") \
            .replace("- Rin -> C\n", f"- Rin -> C: {name_c}\n")
    res3 = convert(md3, sl_dynamic, "g")
    v = {r.agent: (r.target, r.extra["valid"]) for r in res3.rows if r.type == "vote"}
    assert v["Mio"] == ("A", True) and v["Ryuji"] == ("A", True) and v["Rin"] == ("", False)


# ---- tolerated deviations -------------------------------------------------------------------
def test_name_case_restored(aiwolf):
    res = convert(VILLAGE_MD.replace("- **Minako**: Good morning", "- **minako**: Good morning"), aiwolf, "g")
    assert codes(res) == {"name_case"}
    assert res.rows[5].agent == "Minako" and res.rows[5].type == "talk"


def test_pass_punct_normalised(aiwolf):
    md = VILLAGE_MD.replace("- **Minako**: Skip\n", "- **Minako**: skip.\n").replace("- **Mizuki**: Over\n- **Benjamin**: Noted.", "- **Mizuki**: Over!\n- **Benjamin**: Noted.")
    res = convert(md, aiwolf, "g")
    # the same normalisation as the server: a note on the row (common.violations turns it into a
    # kind=normalized item), no structural violation
    assert res.violations == []
    passes = [(r.agent, r.text, r.extra) for r in res.rows if r.type == "pass" and r.round == 0 and r.turn == 2]
    assert passes == [("Minako", "Skip", {"forced": False, "empty": False, "raw": "skip.",
                                          "norm": [{"code": "pass_punct", "token": "Skip", "raw": "skip."}]}),
                      ("Mizuki", "Over", {"forced": False, "empty": False, "raw": "Over!",
                                          "norm": [{"code": "pass_punct", "token": "Over", "raw": "Over!"}]})]
    from common.violations import find_violations
    noted = [(x["seq"], x["code"], x["kind"]) for x in find_violations(res.rows, aiwolf) if x["code"] == "pass_punct"]
    assert len(noted) == 2 and all(k == "normalized" for _, _, k in noted)
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)
    # an empty utterance is an Over with empty:true (as the server records an empty reply)
    res = convert(VILLAGE_MD.replace("- **Mizuki**: Over\n- **Benjamin**: Noted.", "- **Mizuki**:\n- **Benjamin**: Noted."), aiwolf, "g")
    assert res.violations == []
    p = next(r for r in res.rows if r.type == "pass" and r.agent == "Mizuki" and r.round == 0)
    assert p.text == "Over" and p.extra == {"forced": False, "empty": True, "raw": ""}


def test_code_fence_and_bold_variants_are_format_noise(aiwolf):
    fenced = "```markdown\n" + VILLAGE_MD + "```\n"
    res = convert(fenced, aiwolf, "g")
    assert codes(res) == {"format_noise"} and len(res.violations) == 1
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)
    md = VILLAGE_MD.replace("- **Minako**: Good morning", "- **Minako:** Good morning") \
                   .replace("- **Shizue**: Nothing yet", "- Shizue: Nothing yet")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"format_noise"} and len(res.violations) == 2
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)


# ---- structural violations ------------------------------------------------------------------
def test_unknown_name_dropped(aiwolf):
    md = VILLAGE_MD.replace("- **Kenji**: Sounds good", "- **Bob**: who am I\n- **Kenji**: Sounds good")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"unknown_name"}
    assert not [r for r in res.rows if r.agent == "Bob"]
    assert len([r for r in res.rows if r.round == 0 and r.turn == 1]) == 5


def test_dup_turn_keeps_first(aiwolf):
    md = VILLAGE_MD.replace("- **Shizue**: Nothing yet from me, but I am listening.\n",
                            "- **Shizue**: Nothing yet from me, but I am listening.\n- **Shizue**: And again.\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"dup_turn"}
    rows = [r for r in res.rows if r.round == 0 and r.turn == 1 and r.agent == "Shizue"]
    assert len(rows) == 1 and rows[0].text.startswith("Nothing yet")


def test_talk_after_over_and_over_repeat(aiwolf):
    md = VILLAGE_MD.replace("#### Turn 3 of 4\n- **Minako**: Over\n",
                            "#### Turn 3 of 4\n- **Minako**: Over\n- **Mizuki**: One more thing.\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"talk_after_over"}
    assert not [r for r in res.rows if r.round == 0 and r.turn == 3 and r.agent == "Mizuki"]
    md = VILLAGE_MD.replace("#### Turn 3 of 4\n- **Minako**: Over\n",
                            "#### Turn 3 of 4\n- **Minako**: Over\n- **Mizuki**: Over\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"over_repeat"}
    assert all(v["kind"] == "normalized" for v in res.violations if v["code"] == "over_repeat")
    assert not [r for r in res.rows if r.round == 0 and r.turn == 3 and r.agent == "Mizuki"]
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)
    # "Skip" written after Over is filler too (the writer fills the remaining turns), not a violation
    md = VILLAGE_MD.replace("#### Turn 3 of 4\n- **Minako**: Over\n",
                            "#### Turn 3 of 4\n- **Minako**: Over\n- **Mizuki**: Skip\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"pass_after_over"}
    assert all(v["kind"] == "normalized" for v in res.violations if v["code"] == "pass_after_over")
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)


def test_missing_turn_recorded(aiwolf):
    res = convert(VILLAGE_MD.replace("- **Kenji**: Sounds good, @Benjamin, please pick carefully.\n", ""), aiwolf, "g")
    assert codes(res) == {"missing_turn"}
    assert res.violations[0]["detail"].startswith("Kenji has no line in day 0 turn 1")
    assert len([r for r in res.rows if r.round == 0 and r.turn == 1]) == 4


def test_dead_actor_dropped(aiwolf):
    md = WOLF_MD.replace("- **Kenji**: I agree with Shizue.\n", "- **Kenji**: I agree with Shizue.\n- **Mizuki**: I am back.\n") \
                .replace("- Kenji -> Minako\n", "- Kenji -> Minako\n- Benjamin -> Shizue\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"dead_actor"} and len(res.violations) == 2
    assert not [r for r in res.rows if r.round == 2 and r.type != "status" and r.agent in ("Mizuki", "Benjamin")]
    assert res.outcome["winner"] == "WEREWOLF"


def test_order_restored(aiwolf):
    md = VILLAGE_MD.replace("- **Minako**: Good morning everyone. Let us share what we know.\n- **Shizue**: Nothing yet from me, but I am listening.\n",
                            "- **Shizue**: Nothing yet from me, but I am listening.\n- **Minako**: Good morning everyone. Let us share what we know.\n")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"order"}
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)


def test_extra_round_dropped(aiwolf):
    md = VILLAGE_MD.replace("## Result", "## Day 2\n### Talk\n#### Turn 1 of 4\n- **Minako**: Still here.\n## Result")
    res = convert(md, aiwolf, "g")
    assert codes(res) == {"extra_round"}
    assert sig(res.rows) == sig(convert(VILLAGE_MD, aiwolf, "g").rows)
    res = convert(VILLAGE_MD.replace("## Day 1\n", "## Day 4\n### Talk\n## Day 1\n"), aiwolf, "g")
    assert "extra_round" in codes(res)


def test_extra_turn_recorded(aiwolf):
    md = VILLAGE_MD.replace("#### Turn 4 of 4\n### Action", "#### Turn 4 of 4\n#### Turn 5 of 4\n- **Minako**: again\n### Action")
    res = convert(md, aiwolf, "g")
    assert "extra_turn" in codes(res)
    assert not [r for r in res.rows if r.turn == 5]


def test_bad_card_partial_and_fail(sl_dynamic):
    md = SL_DYNAMIC_MD.replace("- investigate: Rin -> Fairness survey; Rota history",
                               "- investigate: Rin -> Fairness survey; No such card") \
                      .replace("- investigate: Mio -> Bathroom state; Allergy note",
                               "- investigate: Mio -> Nope; Nada")
    res = convert(md, sl_dynamic, "g")
    assert codes(res) == {"bad_card"} and len(res.violations) == 3
    inv = {r.agent: r for r in res.rows if r.type == "action"}
    assert inv["Rin"].extra == {"action": "investigate", "cards": ["card_04"], "parse": "partial",
                                "raw": "Fairness survey; No such card"}
    assert inv["Rin"].text == "Fairness survey"
    assert inv["Mio"].extra == {"action": "investigate", "cards": [], "parse": "fail", "raw": "Nope; Nada"}
    assert inv["Mio"].text == ""


def test_vote_count_and_invalid_votes(aiwolf):
    res = convert(VILLAGE_MD.replace("- Kenji -> Benjamin\n", ""), aiwolf, "g")
    assert codes(res) == {"vote_count"}
    assert len([r for r in res.rows if r.type == "vote"]) == 4
    assert res.outcome["winner"] == "VILLAGE"
    # a vote for an unknown or dead player is kept as an invalid row (valid false, empty target)
    res = convert(VILLAGE_MD.replace("- Kenji -> Benjamin\n", "- Kenji -> Nobody\n"), aiwolf, "g")
    assert res.violations == []
    v = next(r for r in res.rows if r.type == "vote" and r.agent == "Kenji")
    assert v.target == "" and v.extra == {"request": "vote_day", "raw": "Nobody", "valid": False, "tie": False}
    # '@Name', trailing punctuation and case are tolerated as in the server's match_name
    res = convert(VILLAGE_MD.replace("- Kenji -> Benjamin\n", "- Kenji -> @benjamin.\n"), aiwolf, "g")
    assert codes(res) == {"name_case"}
    assert next(r for r in res.rows if r.type == "vote" and r.agent == "Kenji").target == "Benjamin"
    # no Vote section at all on a voting day
    res = convert(VILLAGE_MD.replace("### Vote", "### Talk").replace("- execution: Shizue\n", ""), aiwolf, "g")
    assert "vote_count" in codes(res)


def test_tally_mismatch_overridden(aiwolf, cs_fixed):
    res = convert(VILLAGE_MD.replace("- execution: Shizue", "- execution: Benjamin"), aiwolf, "g")
    assert codes(res) == {"tally_mismatch"}
    ex = next(r for r in res.rows if r.type == "action" and r.extra["action"] == "execute")
    assert ex.target == "Shizue" and res.outcome["winner"] == "VILLAGE"
    res = convert(CS_FIXED_MD.replace("- adopted: A\n## Result", "- adopted: B\n## Result"), cs_fixed, "g")
    assert codes(res) == {"tally_mismatch"}
    assert res.outcome["adopted"] == "A" and res.rows[-1].text == "A"


def test_aiwolf_tie_keeps_writer_choice(aiwolf):
    """2-2-1 on day 1: a written execution that is a tied top candidate is kept (tie_choice_differs when it is
    not the tie-break rule's pick); a non-candidate is a miscount (tally_mismatch, overridden)."""
    base = VILLAGE_MD.replace("- Benjamin -> Shizue\n", "- Benjamin -> Kenji\n")
    t = tally({"Minako": "Shizue", "Shizue": "Benjamin", "Mizuki": "Shizue", "Benjamin": "Kenji", "Kenji": "Benjamin"},
              "aiwolf_0001", 1)
    assert t.tie and t.top == ["Benjamin", "Shizue"]
    other = next(x for x in t.top if x != t.chosen)
    for written in t.top:
        res = convert(base.replace("- execution: Shizue", f"- execution: {written}"), aiwolf, "g")
        ex = next(r for r in res.rows if r.type == "action" and r.extra["action"] == "execute" and r.round == 1)
        assert ex.target == written and ex.extra["tie"] is True
        assert "tally_mismatch" not in codes(res)
        if written == t.chosen:
            assert "tie_choice_differs" not in codes(res) and "rule_choice" not in ex.extra
        else:
            assert "tie_choice_differs" in codes(res) and ex.extra["rule_choice"] == t.chosen
            # the replay follows the writer: the executed player is dead afterwards, no dead_actor cascade
            assert "dead_actor" not in codes(res)
            st = {r.agent: r.text for r in res.rows if r.type == "status" and r.round == 2}
            assert st[written] == "DEAD" and st[t.chosen] == "ALIVE"
    res = convert(base.replace("- execution: Shizue", "- execution: Kenji"), aiwolf, "g")
    assert "tally_mismatch" in codes(res) and "tie_choice_differs" not in codes(res)
    ex = next(r for r in res.rows if r.type == "action" and r.extra["action"] == "execute" and r.round == 1)
    assert ex.target == t.chosen and "rule_choice" not in ex.extra
    assert other  # used above through t.top


def test_divine_mismatch_overridden(aiwolf):
    res = convert(VILLAGE_MD.replace("(werewolf)", "(human)"), aiwolf, "g")
    assert codes(res) == {"divine_mismatch"}
    d = next(r for r in res.rows if r.type == "action" and r.extra["action"] == "divine")
    assert d.extra == {"action": "divine", "result": "WEREWOLF", "valid": True} and d.text == "WEREWOLF"


def test_result_mismatch(aiwolf, cs_fixed):
    res = convert(VILLAGE_MD.replace("- winner: village", "- winner: werewolves"), aiwolf, "g")
    assert codes(res) == {"result_mismatch"} and res.outcome["winner"] == "VILLAGE"
    res = convert(VILLAGE_MD.replace("## Result\n- winner: village\n", ""), aiwolf, "g")
    assert codes(res) == {"result_mismatch"}
    res = convert(CS_FIXED_MD.replace("## Result\n- adopted: A", "## Result\n- adopted: D"), cs_fixed, "g")
    assert codes(res) == {"result_mismatch"} and res.rows[-1].text == "A"


def test_participant_table_cross_checked(aiwolf):
    md = VILLAGE_MD.replace("| 4 | Shizue | Werewolf |", "| 4 | Shizue | Villager |")
    assert codes(convert(md, aiwolf, "g")) == {"participant_mismatch"}
    md = VILLAGE_MD.replace("| 4 | Shizue | Werewolf |", "| 4 | Alice | Werewolf |")
    assert codes(convert(md, aiwolf, "g")) == {"unknown_name", "participant_mismatch"}


def test_actions_wrong_actor_dup_missing_extra(aiwolf, cs_fixed, sl_dynamic):
    res = convert(VILLAGE_MD.replace("- divine: Benjamin -> Shizue (werewolf)", "- divine: Kenji -> Shizue (werewolf)"), aiwolf, "g")
    assert codes(res) == {"wrong_actor", "missing_action"}
    assert not [r for r in res.rows if r.type == "action" and r.extra["action"] == "divine"]
    res = convert(VILLAGE_MD.replace("- divine: Benjamin -> Shizue (werewolf)",
                                     "- divine: Benjamin -> Shizue (werewolf)\n- divine: Benjamin -> Kenji (human)"), aiwolf, "g")
    assert codes(res) == {"dup_action"}
    res = convert(VILLAGE_MD.replace("- divine: Benjamin -> Shizue (werewolf)",
                                     "- divine: Benjamin -> Shizue (werewolf)\n- attack: Shizue -> Kenji"), aiwolf, "g")
    assert codes(res) == {"extra_action"}       # no attack on day 0
    assert not [r for r in res.rows if r.type == "action" and r.extra["action"] == "attack"]
    res = convert(WOLF_MD.replace("- attack: Shizue -> Benjamin\n", ""), aiwolf, "g")
    assert "missing_action" in codes(res)
    # fixed mode: an Action section is extra, rows still come from the fixed assignment
    md = CS_FIXED_MD.replace("#### Turn 4 of 4\n## Round 2", "#### Turn 4 of 4\n### Action\n- investigate: Midori -> x; y\n## Round 2")
    res = convert(md, cs_fixed, "g")
    assert codes(res) == {"extra_action"}
    assert len([r for r in res.rows if r.type == "action"]) == 5
    # dynamic: a missing investigate line gives no row
    res = convert(SL_DYNAMIC_MD.replace("- investigate: Rin -> Fairness survey; Rota history\n", ""), sl_dynamic, "g")
    assert codes(res) == {"missing_action"}
    assert len([r for r in res.rows if r.type == "action"]) == 4


def test_invalid_divine_and_attack_targets(aiwolf):
    md = WOLF_MD.replace("- divine: Benjamin -> Kenji (human)", "- divine: Benjamin -> Mizuki (human)") \
                .replace("- attack: Shizue -> Benjamin", "- attack: Shizue -> Shizue")
    res = convert(md, aiwolf, "g")
    acts = {(r.round, r.extra["action"]): r for r in res.rows if r.type == "action"}
    assert acts[(1, "divine")].extra == {"action": "divine", "result": "", "valid": False, "raw": "Mizuki"}
    assert acts[(1, "divine")].target == "" and acts[(1, "divine")].text == ""
    assert acts[(1, "attack")].extra == {"action": "attack", "success": False, "no_target": True, "raw": "Shizue"}
    assert acts[(1, "attack")].target == ""
    # nobody died that night: Benjamin is alive on day 2, so the writer's day 2 (written as if he were dead)
    # lacks his lines, his vote and the night actions, and the game is not decided by the day-2 execution
    assert {r.agent: r.extra["alive"] for r in res.rows if r.type == "status" and r.round == 2}["Benjamin"] is True
    assert codes(res) == {"missing_turn", "vote_count", "missing_action", "missing_round", "result_mismatch"}
    assert res.outcome["winner"] == "NONE" and res.outcome["reason"] == "incomplete"


def test_no_valid_votes_gives_no_target_execute(aiwolf):
    md = VILLAGE_MD
    for n in ("Minako", "Shizue", "Mizuki", "Benjamin", "Kenji"):
        md = re.sub(rf"- {n} -> \w+\n", f"- {n} -> nobody\n", md)
    res = convert(md.replace("- execution: Shizue\n", ""), aiwolf, "g")
    ex = next(r for r in res.rows if r.type == "action" and r.extra["action"] == "execute")
    assert ex.target == "" and ex.text == "" and ex.extra == {"action": "execute", "role": "", "tie": False, "no_target": True}
    assert "tally_mismatch" not in codes(res)


def test_max_day_gives_winner_none(aiwolf):
    day = """## Day {d}
### Talk
#### Turn 1 of 4
- **Minako**: Over
- **Shizue**: Over
- **Benjamin**: Over
### Vote
- Minako -> Nobody
- Shizue -> Nobody
- Benjamin -> Nobody
### Action
- divine: Benjamin -> Minako (human)
- attack: Shizue -> Shizue
"""
    md = WOLF_MD.replace("- execution: Mizuki\n### Action\n- divine: Benjamin -> Kenji (human)\n- attack: Shizue -> Benjamin\n",
                         "- execution: Mizuki\n### Action\n- divine: Benjamin -> Kenji (human)\n- attack: Shizue -> Kenji\n")
    md = md[:md.index("## Day 2")] + day.format(d=2) + day.format(d=3) + "## Result\n- winner: village\n"
    res = convert(md, aiwolf, "g")
    assert res.outcome == {"winner": "NONE", "villagers": 2, "werewolves": 1, "reason": "max_day"}
    assert res.rows[-1].extra == res.outcome and res.rows[-1].round == 3
    assert "result_mismatch" in codes(res)
    assert all(not r.extra["valid"] for r in res.rows if r.type == "vote" and r.round >= 2)
    assert "tally_mismatch" not in codes(res)  # no execution written, none recomputed
    assert [r.round for r in res.rows if r.type == "status"][-1] == 4


def test_truncated_transcript_is_incomplete(aiwolf, cs_fixed):
    res = convert(VILLAGE_MD[:VILLAGE_MD.index("## Day 1")], aiwolf, "g")
    assert "missing_round" in codes(res) and "result_mismatch" in codes(res)
    assert res.outcome["winner"] == "NONE" and res.outcome["reason"] == "incomplete"
    assert res.rows[-1].type == "result" and res.rows[-1].round == 0
    res = convert(CS_FIXED_MD[:CS_FIXED_MD.index("## Round 2")], cs_fixed, "g")
    assert "missing_round" in codes(res)
    assert res.outcome == {"adopted": None, "tally": {}, "tie": False, "reason": "incomplete"}
    assert res.rows[-1].extra == res.outcome and res.rows[-1].round == 3 and res.rows[-1].text == ""
    assert [r.round for r in res.rows if r.type == "status"][-1] == 2


def test_dup_vote_keeps_first(aiwolf):
    res = convert(VILLAGE_MD.replace("- Kenji -> Benjamin\n", "- Kenji -> Benjamin\n- Kenji -> Shizue\n"), aiwolf, "g")
    assert codes(res) == {"dup_vote"}
    assert [r.target for r in res.rows if r.type == "vote" and r.agent == "Kenji"] == ["Benjamin"]


# ---- garbage -------------------------------------------------------------------------------------
@pytest.mark.parametrize("junk", ["", "hello world", "# aiwolf_0001\n## Participants\n| 1 | Kenji |\n",
                                  "```\n```", "\x00\x01\xff", "## Round one\n- **Kenji**: hi", "- **Kenji**: hi\n" * 50,
                                  "## Day\n### Talk\n#### Turn 1 of 4\n- **Kenji**: hi"])
def test_garbage_never_crashes(aiwolf, junk):
    res = convert(junk, aiwolf, "g")
    assert res.rows == [] and res.outcome == {}
    assert [v["code"] for v in res.violations] == ["parse_error"]


def test_fuzzed_fragments_never_raise(aiwolf, sl_dynamic):
    frags = ["# aiwolf_0001", "## Participants", "| Seat | Name | Role |", "|---|---|---|", "| 1 | Kenji | Possessed |",
             "| 9 | Zed | Seer |", "## Day 0", "## Day 1", "## Day 2", "## Day 7", "## Round 1", "## Round 3",
             "### Talk", "### Vote", "### Action", "## Result", "#### Turn 1 of 4", "#### Turn 4 of 4", "#### Turn 9",
             "- **Kenji**: hi there", "- **Minako**: Over", "- **Shizue**: Skip.", "- **Bob**: who", "- Kenji -> Shizue",
             "- Mizuki -> B", "- Shizue -> Nobody", "- execution: Shizue", "- execution: ", "- adopted: A",
             "- winner: village", "- winner: ", "- divine: Benjamin -> Shizue (werewolf)", "- divine: Benjamin -> ",
             "- attack: Shizue -> Kenji", "- attack: Kenji -> Shizue", "- investigate: Misaki -> Supply costs; x",
             "- investigate: ->", "random prose line", "```", "- **Kenji**:", "- :", "->", "|||", "#", "####"]
    rng = random.Random(0)
    bad = re.compile(r"^no '## (Day|Round) <n>' heading found$")
    for i in range(300):
        doc = "\n".join(rng.choice(frags) for _ in range(rng.randint(1, 40)))
        for ctx in (aiwolf, sl_dynamic):
            res = convert(doc, ctx, "g")
            for v in res.violations:
                if v["code"] == "parse_error":
                    assert bad.match(v["detail"]), (i, v, doc)
            assert [r.seq for r in res.rows] == list(range(len(res.rows)))
