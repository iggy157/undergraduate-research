"""Pilot 5 inspection: per condition -> games, outcome, talks/passes, words, Skip/Over, violations, deviations,
record checks (prompt_token_ids, token counts), the seat / writer view byte-equality on the real logs, and the
batch-vs-stepped first divergence per setup."""
import collections
import glob
import json
import sys

sys.path.insert(0, "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
from common.logwriter import read_log
from common.setup import GameContext
from common.transcript import view_from_rows

LOG = sys.argv[1] if len(sys.argv) > 1 else "log/_pilot5"
games = []
for f in sorted(glob.glob(f"{LOG}/*/*/*/*.jsonl")):
    if "/raw/" in f:
        continue
    recs = [json.loads(l) for l in open(f)]
    if not recs or recs[0].get("kind") != "header":
        continue  # still running
    h = recs[0]
    calls = [r for r in recs if r.get("kind") == "llm_call"]
    viol = next((r for r in recs if r.get("kind") == "violations"), {"items": []})["items"]
    rows = list(read_log(f.replace(".jsonl", ".log")))
    games.append((h, calls, viol, rows, f))

by_cond = collections.defaultdict(list)
for g in games:
    by_cond[g[0]["condition"]].append(g)

print(f"{'condition':28} {'n':>2} {'talks':>5} {'words':>6} {'maxw':>4} {'skip':>4} {'over':>4} {'viol':>4} {'norm':>4} {'dev':>4} {'ptok':>4} {'trunc':>5}")
for cond in sorted(by_cond):
    gs = by_cond[cond]
    talks = sum(1 for g in gs for r in g[3] if r.type == "talk")
    words = [r.extra["words"] for g in gs for r in g[3] if r.type == "talk"]
    skips = sum(1 for g in gs for r in g[3] if r.type == "pass" and r.text == "Skip")
    overs = sum(1 for g in gs for r in g[3] if r.type == "pass" and r.text == "Over")
    nv = sum(1 for g in gs for v in g[2] if v.get("kind", "violation") == "violation")
    nn = sum(1 for g in gs for v in g[2] if v.get("kind") == "normalized")
    nd = sum(1 for g in gs for v in g[2] if v.get("kind") == "deviation")
    ptok = sum(1 for g in gs for c in g[1] if c.get("prompt_token_ids"))
    ncalls = sum(len(g[1]) for g in gs)
    trunc = sum(1 for g in gs for c in g[1] if c.get("truncated"))
    print(f"{cond:28} {len(gs):>2} {talks:>5} {sum(words)/max(1,len(words)):>6.1f} {max(words, default=0):>4} {skips:>4} {overs:>4} {nv:>4} {nn:>4} {nd:>4} {ptok:>3}/{ncalls:<3} {trunc:>5}")

print("\nper game:")
for cond in sorted(by_cond):
    for h, calls, viol, rows, f in by_cond[cond]:
        vc = collections.Counter(v["code"] for v in viol if v.get("kind", "violation") != "normalized")
        outcome = h.get("outcome") or {}
        res = outcome.get("winner") or outcome.get("adopted")
        print(f"  {h['game_id'][:60]:60} result={res!s:9} rounds={max((r.round for r in rows), default=None)} viol={dict(vc)}")

# record checks: usage.prompt_tokens == len(prompt_token_ids)
bad = 0; n = 0
for h, calls, viol, rows, f in games:
    for c in calls:
        ids = c.get("prompt_token_ids")
        pt = (c.get("usage") or {}).get("prompt_tokens")
        if ids and pt is not None:
            n += 1
            if len(ids) != pt:
                bad += 1
print(f"\nprompt_token_ids == usage.prompt_tokens: {n - bad}/{n}")

# view byte-equality on the server-pipeline games
for h, calls, viol, rows, f in games:
    if h.get("pipeline") != "server":
        continue
    ctx = GameContext.load(h["setup_id"]); ctx.setup.info_mode = h["info_mode"]
    axes = h["axes"]
    seat_view = axes["method"] == "multi"
    ok = tot = 0
    for c in calls:
        if c["request"] != "TALK":
            continue
        seat = c["seat"]; name = ctx.name_of_seat(seat)
        row = next((r for r in rows if r.type in ("talk", "pass") and r.round == c["round"] and r.turn == c["turn"] and r.agent == name), None)
        if row is None:
            continue
        exp = view_from_rows(rows, ctx, seat if seat_view else None, upto_seq=row.seq, ensure_turn=(row.round, row.turn)).render() + f"\n- **{name}**:"
        got = c["messages"][-1]["content"]
        tot += 1
        ok += (got == exp)
    print(f"  view check {h['condition']:26} {h['setup_id']:26} TALK users equal the log-derived view: {ok}/{tot}")

# batch vs stepped divergence
batch = {g[0]["setup_id"]: g for g in games if g[0]["condition"] == "single-batch"}
for h, calls, viol, rows, f in games:
    if h["condition"] != "single-batch-stepped" or h["setup_id"] not in batch:
        continue
    ctx = GameContext.load(h["setup_id"])
    stepped = view_from_rows(rows, ctx, None).render().splitlines()
    bh, bcalls, _, brows, bf = batch[h["setup_id"]]
    btxt = open(bf.replace(bf.split("/")[-1], "raw/transcript.md")).read().splitlines()
    k = next((i for i, (a, b) in enumerate(zip(stepped, btxt)) if a != b), min(len(stepped), len(btxt)))
    print(f"  batch vs stepped {h['setup_id']:26}: identical for {k} lines (stepped {len(stepped)}, batch {len(btxt)})")
