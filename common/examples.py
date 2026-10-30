"""Discussion examples ("## Examples" block, the few-shot conditions; DESIGN §16).

The block is switched on by the environment variable ``UGR_EXAMPLES`` (a JSON object), so that the same prompt
builder serves every condition and the examples reach the single writer and every multi seat identically:

    {"src": "log/main_gemma31b", "cond": "single-batch" | "multi-private", "n": 3}

Examples = whole recorded discussions of ``cond`` from ``src`` (the model's own generations), of the SAME domain
and of OTHER setups: the first ``n`` setups in sorted order, skipping the setup being generated. Only the talk
lines are kept, one per line as ``- **Name**: text`` (Skip / Over included), as in manyshot-ablation's talk_only
scripts. The introduction follows manyshot-ablation's wording (scripts/run_deliberation.py ``_SCENARIO_INTRO``),
without its formatting clause (the examples here use the transcript grammar of this repository), and without the
fixed assistant acknowledgement and the per-turn reminder (condition A: the examples are the only difference).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INTRO = ("The following are reference scripts of past discussions, provided for prior study. {count}. They show how "
         "a five-party discussion flows; the participants in them are different people from this session. Learn the "
         "discussion flow, pacing, and tone — do not copy lines verbatim.")


def config() -> dict | None:
    raw = os.environ.get("UGR_EXAMPLES")
    return json.loads(raw) if raw else None


@lru_cache(maxsize=None)
def _games(src: str, domain: str, cond: str) -> tuple[tuple[str, Path], ...]:
    """(setup_id, log path) of the recorded games of ``cond`` (no plan) in ``src``, one per setup, sorted."""
    out = {}
    base = (ROOT / src) if not Path(src).is_absolute() else Path(src)
    for gd in sorted((base / domain / cond).glob("*/")):
        parts = gd.name.split("__")
        if len(parts) < 2 or parts[1] != cond:
            continue
        logs = sorted(gd.glob("*.log"))
        if logs and parts[0] not in out:
            out[parts[0]] = logs[0]
    return tuple(sorted(out.items()))


@lru_cache(maxsize=None)
def _transcript(path: Path) -> str:
    from .logwriter import read_log
    lines = [f"- **{r.agent}**: {' '.join(str(r.text).split())}" for r in read_log(path) if r.type in ("talk", "pass")]
    return "\n".join(lines)


def chosen(domain: str, setup_id: str, cfg: dict) -> list[str]:
    games = [(s, p) for s, p in _games(cfg["src"], domain, cfg["cond"]) if s != setup_id]
    return [s for s, _ in games[: int(cfg.get("n", 3))]]


def examples_block(domain: str, setup_id: str, cfg: dict | None = None) -> str | None:
    cfg = cfg if cfg is not None else config()
    if not cfg:
        return None
    games = [(s, p) for s, p in _games(cfg["src"], domain, cfg["cond"]) if s != setup_id][: int(cfg.get("n", 3))]
    if not games:
        raise ValueError(f"UGR_EXAMPLES: no {cfg['cond']} games of domain {domain} in {cfg['src']}")
    n = len(games)
    count = "1 transcript follows" if n == 1 else f"{n} transcripts follow"
    body = "\n\n---\n\n".join(_transcript(p) for _, p in games)
    return INTRO.format(count=count) + "\n\n--- Scripts begin ---\n\n" + body + "\n\n--- Scripts end ---"
