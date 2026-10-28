"""Transcripts for utterance-level annotation (Bo et al. Responsiveness / Rebuttal and the Becker-type defect items).

usage: .venv/bin/python scripts/render_annotation.py --log-dir log/_pilot6 --out-dir <dir> [--replicates]

One file per game: the judge view (period headings, utterances, votes, result) with every utterance prefixed by its
log ``seq`` in brackets, so that an annotator can refer to it. ``<out-dir>/../games.json`` maps file names to games
and conditions (the annotators do not get it). ``--replicates`` keeps every replicate; the default keeps the first
game per setup and condition.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.logwriter import read_log  # noqa: E402
from common.setup import GameContext  # noqa: E402


def render(rows, ctx: GameContext) -> str:
    period = str(ctx.rules["period_name"]).capitalize()
    aiwolf = ctx.domain == "aiwolf"
    out = []
    cur = None
    votes: list[str] = []

    def flush():
        if votes:
            out.append("### Vote")
            out.extend(votes)
            votes.clear()

    for r in rows:
        if r.type in ("talk", "vote", "result", "action") and r.round != cur:
            flush()
            cur = r.round
            out.append(f"## {period} {cur}")
        if r.type == "talk":
            out.append(f"- [{r.seq}] **{r.agent}**: {r.text}")
        elif r.type == "vote" and r.target:
            votes.append(f"- {r.agent} -> {r.target}")
        elif r.type == "action" and r.extra.get("action") == "execute":
            votes.append(f"- execution: {r.target or 'no one'}")
        elif r.type == "result":
            flush()
            out.append("## Result")
            out.append(f"- winner: {r.text}" if aiwolf else f"- adopted: {r.text}")
    flush()
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default="log/_pilot6")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--replicates", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seen = set()
    games = {}
    k = 0
    for gd in sorted(Path(a.log_dir).glob("*/*/*")):
        if not gd.is_dir() or not (gd / f"{gd.name}.log").exists():
            continue
        sid, cond = gd.name.split("__")[:2]
        if not a.replicates and (sid, cond) in seen:
            continue
        seen.add((sid, cond))
        ctx = GameContext.load(sid)
        rows = list(read_log(gd / f"{gd.name}.log"))
        k += 1
        name = f"game_{k:03d}.md"
        (out / name).write_text(f"# {name[:-3]} ({ctx.domain})\n\n" + render(rows, ctx), encoding="utf-8")
        games[name] = {"game_id": gd.name, "setup_id": sid, "condition": cond, "domain": ctx.domain,
                       "n_talk": sum(1 for r in rows if r.type == "talk")}
    (out.parent / "games.json").write_text(json.dumps(games, indent=1) + "\n", encoding="utf-8")
    print(f"{len(games)} games -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
