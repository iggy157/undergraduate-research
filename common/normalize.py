"""Normalisation of a TALK reply, shared by the server (multi) and the single converter.

One function decides what the other participants see and what is recorded. The rules tolerate
surface variants that have nothing to do with the quality of the discussion (DESIGN §8.1); every
tolerance is recorded as a *normalisation note* (``kind: normalized``), never silently.

- whitespace / edge trimming (newlines inside the utterance are kept);
- a pass token with punctuation, quotes or case variants ("Over.", "skip", '"Over"') -> the token
  (note ``pass_punct``);
- the whole utterance wrapped in quotes or ``**`` -> unwrapped (note ``format_noise`` kind ``wrap``);
- the speaker's own name label at the start ("Kenji: ...", "**Kenji**: ...") -> removed
  (note ``name_label``; another participant's label is left in place: that is ``speak_for_others``,
  a real violation, judged later by common.violations);
- content followed by the exact pass token at the very end ("... see you tomorrow. Over.") -> the
  token is removed (note ``trailing_over``); a trailing *Over* also ends the speaker's turns for the
  round (``over_after``), exactly as if "Over" had been said on the next turn. The match is
  case-sensitive so that an ordinary "... turn it over." is left alone.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .protocol import T_FORCE_SKIP, T_OVER, T_SKIP

_WRAP_CHARS = "\"'“”‘’`*_ "
_PASS_RE = re.compile(r"(skip|over)", re.IGNORECASE)
_TRAIL_RE = re.compile(r"(?:^|\s)(Skip|Over)[\s.!。！…]*$")  # exact token only: "turn it over." is a sentence
_NEXT_LINE_RE = re.compile(r"\n\s*(?:- \*\*|#{2,4} )")  # next transcript line: another speaker's label or a heading
_WRAP_PAIRS = (('"', '"'), ("“", "”"), ("'", "'"), ("‘", "’"), ("**", "**"), ("*", "*"), ("_", "_"))


@dataclass
class TalkNorm:
    kind: str                     # talk | skip | over
    text: str                     # what the others see (stripped, newlines kept) or the pass token
    over_after: bool = False      # talk followed by a trailing Over: no further turns this round
    flags: dict[str, bool] = field(default_factory=dict)   # forced / empty
    notes: list[dict[str, Any]] = field(default_factory=list)  # normalisation notes {code, ...}

    def note(self, code: str, **detail: Any) -> None:
        self.notes.append({"code": code, **detail})


def _pass_core(s: str) -> str | None:
    core = s.strip().strip(_WRAP_CHARS).rstrip(".!。！…").strip()
    if _PASS_RE.fullmatch(core):
        return T_SKIP if core.lower() == "skip" else T_OVER
    return None


def _unwrap(s: str) -> tuple[str, bool]:
    for left, right in _WRAP_PAIRS:
        if len(s) > len(left) + len(right) and s.startswith(left) and s.endswith(right):
            inner = s[len(left):-len(right)].strip()
            if inner and left not in inner.strip(_WRAP_CHARS):
                return inner, True
    return s, False


def _own_label_re(name: str) -> re.Pattern[str]:
    return re.compile(r"^\s*(?:\*\*|\[|\()?\s*" + re.escape(name) + r"\s*(?:\*\*|\]|\))?\s*(?:[:：]|-\s|–\s|—\s)\s*",
                      re.IGNORECASE)


def normalize_talk(raw: str | None, agent: str, pass_skip: str = T_SKIP, pass_over: str = T_OVER) -> TalkNorm:
    """Classify and normalise one TALK reply of ``agent``. ``raw`` is None when the agent timed out."""
    if raw is None:
        return TalkNorm("skip", pass_skip, flags={"forced": True})
    s = raw.strip()
    if s == "":
        return TalkNorm("over", pass_over, flags={"empty": True})
    if s == T_FORCE_SKIP:
        return TalkNorm("skip", pass_skip, flags={"forced": True})
    tok = _pass_core(s)
    if tok is not None:
        tok = pass_skip if tok == T_SKIP else pass_over
        n = TalkNorm("skip" if tok == pass_skip else "over", tok)
        if s != tok:
            n.note("pass_punct", token=tok, raw=s)
        return n
    n = TalkNorm("talk", s)
    cut = _NEXT_LINE_RE.search(s)
    if cut and s[:cut.start()].strip():  # the model went on to the next transcript line (another speaker / heading)
        n.note("multi_utt", cut=s[cut.start():].strip()[:80])
        s = s[:cut.start()].rstrip()
    text, wrapped = _unwrap(s)
    if wrapped:
        n.note("format_noise", kinds=["wrap"], raw=s)
    m = _own_label_re(agent).match(text)
    if m:
        stripped = text[m.end():].strip()
        if stripped:
            n.notes.append({"code": "name_label", "name": agent, "self": True, "raw": text})
            text = stripped
    mt = _TRAIL_RE.search(text)
    if mt and text[:mt.start()].strip():
        tok = pass_skip if mt.group(1) == "Skip" else pass_over
        n.note("trailing_over", token=tok, tail=text[mt.start():].strip())
        text = text[:mt.start()].rstrip()
        if tok == pass_over:
            n.over_after = True
    n.text = text.strip()
    return n


__all__ = ["TalkNorm", "normalize_talk"]
