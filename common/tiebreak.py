"""Deterministic tie-break shared by server (multi) and converter (single). DESIGN §6.1.

Candidates are sorted by name/label; the winner is the ``sha1(f"{setup_id}:{round}") mod n``-th one.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass


def choose(candidates: list[str], setup_id: str, round_no: int) -> str:
    cands = sorted(set(candidates))
    if not cands:
        raise ValueError("no candidates")
    if len(cands) == 1:
        return cands[0]
    h = hashlib.sha1(f"{setup_id}:{round_no}".encode("utf-8")).hexdigest()
    return cands[int(h, 16) % len(cands)]


@dataclass
class Tally:
    counts: dict[str, int]
    top: list[str]
    chosen: str | None
    tie: bool


def tally(votes: dict[str, str | None], setup_id: str, round_no: int) -> Tally:
    """votes: voter -> target (None = invalid / not counted). Returns the elected target."""
    c = Counter(t for t in votes.values() if t)
    if not c:
        return Tally({}, [], None, False)
    best = max(c.values())
    top = sorted(k for k, v in c.items() if v == best)
    chosen = top[0] if len(top) == 1 else choose(top, setup_id, round_no)
    return Tally(dict(sorted(c.items())), top, chosen, len(top) > 1)
