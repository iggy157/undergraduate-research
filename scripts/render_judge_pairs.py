"""Condition-blind transcript pairs for the pairwise judgement (human raters and the LLM judge).

usage: .venv/bin/python scripts/render_judge_pairs.py --log-dir log/_pilot6 --out-dir <dir> [--seed 1]

For every setup and every comparison in COMPARISONS, the writer view of the two games is rendered in the common
grammar as ``Transcript A`` and ``Transcript B``. Two files are written per pair: ``<pair>_o1.md`` (A = first
condition of the comparison) and ``<pair>_o2.md`` (swapped), so that an order effect can be measured.
``<out-dir>/../pairs.json`` (outside the directory the raters read) maps pair ids to setups and conditions.
``assignments.json`` groups the pairs into rater sets by a Latin square (every set has one pair of every
comparison, all from different setups).
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
from common.transcript import view_from_rows  # noqa: E402

COMPARISONS = [  # (id, first condition, second condition): the five main comparisons (paper_draft §5)
    ("C1", "single-batch", "multi-private"),
    ("C2", "single-batch", "single-online"),
    ("C3", "single-online", "multi-public"),
    ("C4", "multi-public", "multi-private"),
    ("C5", "single-batch", "single-batch-process"),
]


def render(gd: Path, ctx: GameContext, letter: str) -> str:
    rows = list(read_log(gd / f"{gd.name}.log"))
    text = view_from_rows(rows, ctx, None).render()
    return text.replace(f"# {ctx.setup.setup_id}", f"# Transcript {letter}", 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default="log/_pilot6")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    games: dict[str, dict[str, Path]] = {}
    for gd in sorted(Path(a.log_dir).glob("*/*/*")):
        if not gd.is_dir():
            continue
        parts = gd.name.split("__")
        if len(parts) >= 4:
            games.setdefault(parts[0], {}).setdefault(parts[1], gd)  # first replicate by timestamp
    setups = sorted(games)
    pairs = {}
    for i, sid in enumerate(setups):
        ctx = GameContext.load(sid)
        for j, (cid, c1, c2) in enumerate(COMPARISONS):
            if c1 not in games[sid] or c2 not in games[sid]:
                continue
            pid = f"{sid}__{cid}"
            t1, t2 = render(games[sid][c1], ctx, "A"), render(games[sid][c2], ctx, "B")
            (out / f"{pid}_o1.md").write_text(t1 + "\n\n---\n\n" + t2 + "\n", encoding="utf-8")
            t1b, t2b = render(games[sid][c2], ctx, "A"), render(games[sid][c1], ctx, "B")
            (out / f"{pid}_o2.md").write_text(t1b + "\n\n---\n\n" + t2b + "\n", encoding="utf-8")
            pairs[pid] = {"setup_id": sid, "comparison": cid, "o1": {"A": c1, "B": c2}, "o2": {"A": c2, "B": c1},
                          "games": {c1: games[sid][c1].name, c2: games[sid][c2].name}, "set": (i + j) % len(setups)}
    (out.parent / "pairs.json").write_text(json.dumps(pairs, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sets: dict[int, list[str]] = {}
    for pid, p in pairs.items():
        sets.setdefault(p["set"], []).append(pid)
    (out.parent / "assignments.json").write_text(json.dumps(sets, indent=1) + "\n", encoding="utf-8")
    print(f"{len(pairs)} pairs, {len(sets)} rater sets -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
