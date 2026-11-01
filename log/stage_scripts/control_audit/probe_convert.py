"""Probe: how the single converter vs the multi server treat the same deviant utterances."""
import sys
sys.path.insert(0, "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
from common.setup import GameContext
from common.convert.single_markdown import convert
from common.violations import find_violations
from common.schema import LogRow
from common.logwriter import count_words, find_mentions
from server.base.parse import classify_talk
from single.base.fake import canned_transcript

ctx = GameContext.load("shared_living_0001"); ctx.setup.info_mode = "fixed"
md = canned_transcript(ctx)
names = ctx.speaking_order_names
n0, n1 = names[0], names[1]
# deviant utterances: multi-line, name label, parenthesised stage, trailing over, bold
md = md.replace(f"- **{n0}**: I have a short point to make and will keep it brief.",
                f"- **{n0}**: First line of a long speech.\nSecond line continues the same speech.\n- **{n1}**: {n1}: I label myself.", 1)
md = md.replace(f"- **{n1}**: I have a short point to make and will keep it brief.",
                f"- **{n1}**: (Dead)", 1)
md = md.replace(f"- **{names[2]}**: I have a short point to make and will keep it brief.",
                f"- **{names[2]}**: ## Round 1\nI think so. Over.", 1)
res = convert(md, ctx, "probe")
r1 = [r for r in res.rows if r.round == 1 and r.turn == 1]
for r in r1: print("ROW", r.seq, r.type, r.agent, repr(r.text), r.extra)
print("CONVERTER VIOLATIONS:")
for v in res.violations: print("  ", v)
print("COMMON (find_violations on converted rows):")
for v in find_violations(res.rows, ctx):
    if v["seq"] in [r.seq for r in r1]: print("  ", v)
# multi side: the same raw replies through the server path
print("MULTI side:")
for raw in ["First line of a long speech.\nSecond line continues the same speech.", f"{n1}: I label myself.", "(Dead)", "## Round 1\nI think so. Over.", "  Over. ", ""]:
    kind, text, flags = classify_talk(raw)
    row = LogRow(0, 1, 1, "talk" if kind == "talk" else "pass", n0, "", text,
                 {"words": count_words(text), "mentions": find_mentions(text, ctx.names), "raw_differs": raw != text} if kind == "talk" else {"forced": False, "empty": flags.get("empty", False), **({"raw": raw.strip()} if raw.strip() != text else {})})
    print("  ", kind, repr(text), row.extra, [ (v["code"], v["detail"]) for v in find_violations([row], ctx)])
