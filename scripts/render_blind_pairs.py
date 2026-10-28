"""Condition-blind transcript bundles for the preliminary (qualitative) evaluation.

usage: .venv/bin/python scripts/render_blind_pairs.py --log-dir log/_pilot6 --out-dir <dir> [--setups a,b] [--seed 1]

For every setup found under ``<log-dir>/<domain>/<condition>/``, the writer view of each game (one game per
condition; the first replicate of single-batch) is rendered in the common grammar with the ``# <setup_id>`` line
replaced by ``# Transcript <letter>`` and written as ``<setup_id>.md`` (all conditions of the setup, in a seeded
random order with letters A, B, C, ...). ``<setup_id>.key.json`` maps the letters back to the conditions and game ids
(the raters do not get it). Headings and labels are kept, so a reader can still tell the length and the Skip/Over
habits apart: that is part of what the preliminary evaluation looks at.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.logwriter import read_log  # noqa: E402
from common.setup import GameContext  # noqa: E402
from common.transcript import view_from_rows  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default="log/_pilot6")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--setups", default=None, help="comma list; default all")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    log_dir = Path(a.log_dir)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    games: dict[str, dict[str, Path]] = {}  # setup -> condition -> game dir (first by timestamp)
    for dom in sorted(p for p in log_dir.iterdir() if p.is_dir()):
        for cond_dir in sorted(p for p in dom.iterdir() if p.is_dir()):
            for gd in sorted(p for p in cond_dir.iterdir() if p.is_dir()):
                parts = gd.name.split("__")
                if len(parts) < 4:
                    continue
                sid, cond = parts[0], parts[1]
                games.setdefault(sid, {}).setdefault(cond, gd)
    wanted = set(a.setups.split(",")) if a.setups else set(games)
    rng = random.Random(a.seed)
    for sid in sorted(wanted):
        conds = games.get(sid, {})
        if not conds:
            continue
        ctx = GameContext.load(sid)
        order = sorted(conds)
        rng.shuffle(order)
        letters = [chr(ord("A") + i) for i in range(len(order))]
        key = {}
        blocks = []
        for letter, cond in zip(letters, order):
            gd = conds[cond]
            rows = list(read_log(gd / f"{gd.name}.log"))
            text = view_from_rows(rows, ctx, None).render()
            text = text.replace(f"# {sid}", f"# Transcript {letter}", 1)
            blocks.append(text)
            key[letter] = {"condition": cond, "game_id": gd.name}
        (out / f"{sid}.md").write_text("\n\n---\n\n".join(blocks) + "\n", encoding="utf-8")
        (out / f"{sid}.key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{sid}: {len(order)} transcripts -> {out / (sid + '.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
