"""Run the violation accounting over every game log and store it in the jsonl (DESIGN §8, §3.2).

usage: .venv/bin/python scripts/convert_logs.py [--log-dir log] [--domain d] [--method m] [--game-id id]
                                               [--dry-run] [--quiet]

For each ``<log_dir>/<domain>/<method>/<game_id>/<game_id>.log``:
  1. load the setup named by the jsonl header (``setup_id``; falls back to the game_id prefix) and
     apply the header's ``info_mode`` (the setup file may say otherwise: ``--info-mode`` runs),
  2. ``find_violations(rows, ctx)`` + ``find_truncations(llm_call records)``,
  3. replace (or append) the single ``{"kind": "violations", "items": [...]}`` record in
     ``<game_id>.jsonl`` (all other records are kept byte-for-byte). Structural items already in the
     record (single converter codes, ``llm_error`` ...) are kept; only the row-level common codes are
     recomputed; duplicates are dropped (``common.violations.merge_violations``),
  4. print one summary row per game (count per code; structural codes are not in the table) and a
     total row.

``--dry-run`` only prints. Exit code 0; games whose setup cannot be loaded are reported and skipped.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import DOMAINS, LOG_DIRS, METHODS
from common.logwriter import read_jsonl, read_log
from common.setup import GameContext
from common.violations import CODES, find_truncations, find_violations, merge_violations, summarize, summarize_kinds


def iter_games(log_dir: Path, domain: str | None, method: str | None, game_id: str | None):
    for dom in sorted(DOMAINS):
        if domain and dom != domain:
            continue
        for meth in LOG_DIRS:
            if method and meth != method and not meth.startswith(method + "-"):
                continue
            base = log_dir / dom / meth
            if not base.is_dir():
                continue
            for gdir in sorted(p for p in base.iterdir() if p.is_dir()):
                if game_id and gdir.name != game_id:
                    continue
                log = gdir / f"{gdir.name}.log"
                if log.is_file():
                    yield dom, meth, gdir, log


def header_of(records: list[dict]) -> dict:
    for r in records:
        if r.get("kind") == "header":
            return r
    return {}


def setup_id_of(game_dir: Path, records: list[dict]) -> str:
    sid = header_of(records).get("setup_id")
    return str(sid) if sid else game_dir.name.split("__", 1)[0]


def context_of(game_dir: Path, records: list[dict]) -> GameContext:
    """GameContext of the game as it was played: the header's ``info_mode`` overrides the setup file."""
    ctx = GameContext.load(setup_id_of(game_dir, records))
    mode = header_of(records).get("info_mode")
    if mode in ("dynamic", "fixed"):
        ctx.setup.info_mode = str(mode)
    return ctx


def process(game_dir: Path, log: Path, dry_run: bool) -> tuple[dict[str, int], int]:
    jsonl = game_dir / f"{game_dir.name}.jsonl"
    records = list(read_jsonl(jsonl)) if jsonl.is_file() else []
    ctx = context_of(game_dir, records)
    rows = read_log(log)
    existing = [it for r in records if r.get("kind") == "violations" for it in r.get("items", [])]
    items = merge_violations(existing, find_violations(rows, ctx) + find_truncations(records))
    if not dry_run:
        kept = [json.dumps(r, ensure_ascii=False) for r in records if r.get("kind") != "violations"]
        kept.append(json.dumps({"kind": "violations", "items": items}, ensure_ascii=False))
        jsonl.write_text("\n".join(kept) + "\n", encoding="utf-8")
    s = summarize(items)
    s.update({f"#{k}": v for k, v in summarize_kinds(items).items()})
    return s, len([r for r in rows if r.type == "talk"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--log-dir", default="log")
    ap.add_argument("--domain", choices=DOMAINS)
    ap.add_argument("--method", help="single | multi | a condition directory (single-batch, multi-public, ...)")
    ap.add_argument("--game-id")
    ap.add_argument("--dry-run", action="store_true", help="compute and print, do not touch the jsonl")
    ap.add_argument("--quiet", action="store_true", help="only the total row")
    a = ap.parse_args(argv)

    log_dir = Path(a.log_dir)
    if not log_dir.is_absolute():
        log_dir = (ROOT / log_dir).resolve() if not log_dir.exists() else log_dir.resolve()
    cols = [*CODES, "#violation", "#normalized"]
    header = ["game_id", "talks", *cols]
    widths = [max(len(h), 5) for h in header]
    total = {c: 0 for c in cols}
    n_games = n_talks = 0
    lines: list[list[str]] = []
    for dom, meth, gdir, log in iter_games(log_dir, a.domain, a.method, a.game_id):
        try:
            summary, talks = process(gdir, log, a.dry_run)
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"skip {gdir.name}: {e.__class__.__name__}: {e}", file=sys.stderr)
            continue
        n_games += 1
        n_talks += talks
        for c in cols:
            total[c] += summary.get(c, 0)
        lines.append([gdir.name, str(talks), *[str(summary.get(c, 0)) for c in cols]])
    lines.append([f"TOTAL ({n_games} games)", str(n_talks), *[str(total[c]) for c in cols]])
    if a.quiet:
        lines = lines[-1:]
    for row in lines:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    fmt = "  ".join(f"{{:<{w}}}" if i == 0 else f"{{:>{w}}}" for i, w in enumerate(widths))
    print(fmt.format(*header))
    for row in lines:
        print(fmt.format(*row))
    if a.dry_run:
        print("(dry run: jsonl files not modified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
