"""Normalisation of agent replies (IMPLEMENTATION_NOTES §3, DESIGN §4.5-5/6).

Pure functions so they can be unit-tested without a socket.
"""
from __future__ import annotations

import re
from typing import Any

from common.normalize import TalkNorm, normalize_talk
from common.protocol import T_FORCE_SKIP, T_OVER, T_SKIP

_PASS_RE = re.compile(r"(skip|over)[\s.。!！]*", re.IGNORECASE)
_EDGE_PUNCT = " \t\r\n.,!?;:。、！？\"'`“”‘’"
_LABEL_PREFIX_RE = re.compile(r"^(?:option|candidate)\s+", re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*(?:[-*•·]+|\d+[.)]|\(\d+\))\s*")


def classify_talk(raw: str | None, agent: str = "") -> tuple[str, str, dict[str, bool]]:
    """Classify a TALK reply: ``(kind, text, flags)`` with kind in ``talk`` / ``skip`` / ``over``.
    Thin wrapper over :func:`common.normalize.normalize_talk` (the full result is in ``normalize``)."""
    n = normalize_talk(raw, agent)
    return n.kind, n.text, dict(n.flags)


def normalize(raw: str | None, agent: str) -> TalkNorm:
    """The full normalisation result (text, over_after, notes) of a TALK reply; see common.normalize."""
    return normalize_talk(raw, agent)


def strip_edges(s: str) -> str:
    return s.strip().strip(_EDGE_PUNCT).strip()


def match_name(raw: str | None, candidates: list[str]) -> str | None:
    """Match a reply against player names (case-insensitive, edge punctuation / '@' tolerated)."""
    if raw is None:
        return None
    s = strip_edges(raw)
    if s.startswith("@"):
        s = s[1:].strip()
    # "Shizue (werewolf)": the batch-style writer (single-batch-stepped) states the result after the name
    s = re.sub(r"\s*\([^)]*\)[\s.!]*$", "", s).strip()
    low = {c.lower(): c for c in candidates}
    return low.get(s.lower())


def match_option(raw: str | None, options: list[dict[str, str]]) -> str | None:
    """Match a reply against option labels: "A", "A.", "Option A", "Candidate A" (case-insensitive).
    The option's full name is accepted too."""
    if raw is None:
        return None
    s = strip_edges(raw)
    s = strip_edges(_LABEL_PREFIX_RE.sub("", s))
    if not s:
        return None
    for o in options:
        if s.lower() == str(o["label"]).lower() or s.lower() == str(o.get("name", "")).lower():
            return str(o["label"])
    return None


def parse_investigate(raw: str | None, cards: list[dict[str, Any]], choose: int = 2
                      ) -> tuple[list[dict[str, Any]], str]:
    """Parse an INVESTIGATE reply: one title per line (';' also accepted as separator), bullets /
    numbering / quotes stripped, matched case-insensitively. The first ``choose`` distinct matches
    are adopted. Returns ``(cards, parse)`` with parse in ok / partial / fail."""
    found: list[dict[str, Any]] = []
    if raw is not None:
        by_title = {str(c["title"]).strip().lower(): c for c in cards if c.get("title")}
        for line in raw.splitlines():
            for part in line.split(";"):
                t = _BULLET_RE.sub("", part).strip().strip("\"'`“”‘’").strip()
                c = by_title.get(t.lower()) or by_title.get(t.rstrip(".").strip().lower())
                if c is not None and all(c["card_id"] != f["card_id"] for f in found):
                    found.append(c)
                if len(found) >= choose:
                    break
            if len(found) >= choose:
                break
    if len(found) >= choose:
        return found, "ok"
    return found, ("partial" if found else "fail")


__all__ = ["classify_talk", "match_name", "match_option", "normalize", "parse_investigate", "strip_edges"]
