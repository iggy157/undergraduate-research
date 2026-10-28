"""Violation accounting shared by both methods (DESIGN §8, IMPLEMENTATION_NOTES §6).

Input: the rows of ``<game_id>.log`` plus the ``GameContext``; output: ``[{seq, code, detail}]``.
Only the method-independent codes are detected here, on ``talk`` / ``pass`` rows. Nothing is
repaired: restoration (stripping name labels etc.) is done at analysis time. Detection is
deliberately simple and biased towards precision; every rule is described next to its regex.

Codes (all on talk rows unless noted):

``over_cap``          words (``\\S+`` tokens of the text column) > ``rules.word_cap``.
``name_label``        the text starts with a participant name followed by ``:`` / ``：`` or a dash
                      (`` - ``, `` – ``, `` — ``), optionally wrapped in ``**`` / ``[]`` / ``()``.
``multi_utt``         a later line (after a newline) starts with a name label of *any* participant.
``pass_punct``        pass rows whose ``extra.raw`` differs from the token beyond whitespace
                      (``Over.``, ``over``, ``"Skip"`` ...), or talk rows whose whole text is a
                      punctuation / case / quote variant of ``Skip`` / ``Over`` that the server did
                      not normalise.
``trailing_over``     a talk row whose text has other content and ends with ``Over`` / ``Skip``
                      (optionally ``.`` / ``!``), case-insensitive: an utterance with the pass token
                      glued to its end (``... see you tomorrow. Over.``). Record only; the text is
                      kept as logged.
``speak_for_others``  after the first line, a line starting with *another* participant's name
                      label, or anywhere a reported-speech pattern ``<Other> said/says/...`` followed
                      by a quotation mark.
``format_noise``      markdown headings (``# ``), bold (``**``), bracketed stage directions
                      (``[laughs]``), parenthesised stage directions in the third person
                      (``(laughs)``, ``(leans forward)``), ``*nods*`` asterisk actions, ``Turn N`` /
                      ``Round N`` / ``Day N`` scaffolding strings, horizontal rules.
``early_reveal``      discussion domains only. In rounds before the reveal round (3): the text
                      contains an option ``name`` (case-insensitive, word boundaries). In round 1
                      additionally: a 6-word contiguous match (case-insensitive, punctuation
                      stripped) with any card text of the instance.
``early_reveal_partial``
                      discussion domains only, coarser than ``early_reveal`` (record only): before the
                      reveal round a single token of an option ``name`` (>= 5 letters, not in
                      ``PARTIAL_STOPWORDS``) appears as a whole word, case-insensitive, in the text.
                      One item per (token, option label); options already caught by the full-name
                      match on the same row are not repeated here. Detail: token, label, name.
``truncated``         taken from jsonl ``llm_call`` records (``finish_reason == "length"`` or
                      ``truncated: true``) by :func:`find_truncations`; ``seq`` is the llm_call's
                      own ``seq`` (the merged, chronological one) and ``detail`` carries
                      seat / seat_seq / request / round / turn.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from typing import Any

from .logwriter import count_words
from .protocol import T_FORCE_SKIP
from .schema import LogRow
from .setup import GameContext

REVEAL_ROUND = 3          # options are revealed at the start of round 3 (DESIGN §5)
CARD_NGRAM = 6            # contiguous words shared with a card text that count as early_reveal
PASS_TOKENS = ("Skip", "Over")

CODES = ("over_cap", "name_label", "multi_utt", "pass_punct", "trailing_over", "speak_for_others",
         "format_noise", "early_reveal", "early_reveal_partial", "truncated")

# tokens of option names that are too generic to count as a partial reveal (lower-case)
PARTIAL_STOPWORDS = frozenset((
    "fixed", "weekly", "shared", "standing", "service", "central", "public", "system", "plan", "project",
    "centre", "center", "studio", "network", "hub", "app", "data", "open", "free", "paid", "managed",
    "rotating",
))
PARTIAL_MIN_LETTERS = 5

_LABEL_SEP = r"(?:\s*[:：]|\s+[-–—]\s)"
_WRAP_L = r"(?:\*\*|\[|\()?"
_WRAP_R = r"(?:\*\*|\]|\))?"
_SAID_VERBS = r"(?:said|says|saying|replied|replies|asked|asks|added|adds|answered|answers|wrote|writes)"
_STAGE_VERBS = (
    "laughs|laughing|chuckles|chuckling|sighs|sighing|nods|nodding|smiles|smiling|grins|grinning|"
    "frowns|frowning|pauses|pausing|shrugs|shrugging|leans|leaning|looks|looking|glances|glancing|"
    "turns|turning|whispers|whispering|clears|crosses|shakes|shaking|taps|tapping|raises|raising|"
    "gestures|gesturing|winks|winking|coughs|coughing|scoffs|scoffing|stares|staring|folds|folding|"
    "adjusts|adjusting|rubs|rubbing|tilts|tilting|exhales|inhales|squints|squinting|beat|pause"
)
_FORMAT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("heading", re.compile(r"(?m)^\s{0,3}#{1,6}\s")),
    ("bold", re.compile(r"\*\*")),
    ("bracket", re.compile(r"\[[^\]\n]{1,80}\]")),
    ("paren_stage", re.compile(r"\(\s*(?:" + _STAGE_VERBS + r")\b[^)\n]{0,80}\)", re.IGNORECASE)),
    ("asterisk_stage", re.compile(r"(?<!\*)\*(?!\*)\s*(?:" + _STAGE_VERBS + r")\b[^*\n]{0,80}\*(?!\*)",
                                  re.IGNORECASE)),
    ("scaffold", re.compile(r"(?m)^\s*(?:Turn|Round|Day)\s+\d+\b")),
    ("hrule", re.compile(r"(?m)^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")),
]
_PUNCT_RE = re.compile(r"[^\w\s]|_", re.UNICODE)
_TRAILING_PASS_RE = re.compile(r"(?:^|\s)(Over|Skip)[.!]?$")
_LETTERS_RE = re.compile(r"[A-Za-z]+")


# ---- helpers ---------------------------------------------------------------------------------
def _names_alt(names: Iterable[str]) -> str:
    return "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))


def _label_re(names: Iterable[str]) -> re.Pattern[str]:
    """Matches a name label at the start of a string: ``Name:``, ``**Name**:``, ``Name -``."""
    return re.compile(r"^\s*" + _WRAP_L + r"(" + _names_alt(names) + r")" + _WRAP_R + _LABEL_SEP)


def _normalize_words(text: str) -> list[str]:
    return _PUNCT_RE.sub(" ", text.lower()).split()


def _ngrams(words: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _pass_variant(text: str) -> str | None:
    """Return the canonical token when ``text`` is a punctuation/case/quote variant of Skip/Over."""
    core = text.strip().strip("\"'“”‘’`*_ ").rstrip(".!。！…").strip()
    for tok in PASS_TOKENS:
        if core.lower() == tok.lower():
            return tok
    return None


NORMALIZED = "normalized"   # a surface variant absorbed at write time (recorded, not a violation)
VIOLATION = "violation"


def _v(seq: int, code: str, *, _kind: str = VIOLATION, **detail: Any) -> dict[str, Any]:
    return {"seq": seq, "code": code, "kind": _kind, "detail": detail}


def _notes(row: LogRow) -> list[dict[str, Any]]:
    """Normalisation notes the writer attached to the row (``extra.norm``, common.normalize)."""
    out = []
    for note in row.extra.get("norm") or []:
        d = {k: v for k, v in dict(note).items() if k != "code"}
        out.append(_v(row.seq, str(note.get("code")), _kind=NORMALIZED, **d))
    return out


# ---- per-row checks ----------------------------------------------------------------------------
def _check_talk(row: LogRow, ctx: GameContext, names: list[str], label_any: re.Pattern[str],
                option_res: list[tuple[str, re.Pattern[str]]], card_ngrams: list[tuple[str, set]],
                word_cap: int | None,
                partial_res: list[tuple[str, str, str, re.Pattern[str]]] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    text = row.text
    lines = text.split("\n")

    # over_cap
    if word_cap is not None:
        n = count_words(text)
        if n > word_cap:
            out.append(_v(row.seq, "over_cap", words=n, cap=word_cap))

    # name_label (the speaker's own label is normalised away at write time; one that survives here
    # is from an older log -> recorded as normalised; another participant's label is a violation)
    m = label_any.match(lines[0])
    if m:
        own = m.group(1) == row.agent
        out.append(_v(row.seq, "name_label", _kind=NORMALIZED if own else VIOLATION, name=m.group(1), self=own))

    # multi_utt / speak_for_others (later lines)
    later_labels: list[tuple[int, str]] = []
    for i, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        m = label_any.match(line)
        if m:
            later_labels.append((i, m.group(1)))
    if later_labels:
        out.append(_v(row.seq, "multi_utt", lines=[i for i, _ in later_labels],
                      names=[n for _, n in later_labels]))
    others = [(i, n) for i, n in later_labels if n != row.agent]
    quoted = None
    other_names = [n for n in names if n != row.agent]
    if other_names:
        said = re.search(r"\b(" + _names_alt(other_names) + r")\s+" + _SAID_VERBS + r"\b[^\n\"“']{0,20}[\"“']",
                         text)
        if said:
            quoted = said.group(1)
    if others or quoted:
        out.append(_v(row.seq, "speak_for_others",
                      names=sorted({n for _, n in others} | ({quoted} if quoted else set()))))

    # pass_punct on talk rows: the whole utterance is a Skip/Over variant the server did not normalise
    tok = _pass_variant(text)
    if tok is not None and text.strip() != tok:
        out.append(_v(row.seq, "pass_punct", _kind=NORMALIZED, token=tok, raw=text))

    # trailing_over: other content followed by the pass token at the very end (older logs; the writer
    # now strips it and records a note)
    if tok is None:
        mt = _TRAILING_PASS_RE.search(text.rstrip())
        if mt:
            out.append(_v(row.seq, "trailing_over", _kind=NORMALIZED, token=mt.group(1), tail=mt.group(0)))

    # format_noise
    kinds = [k for k, rx in _FORMAT_RULES if rx.search(text)]
    if kinds:
        out.append(_v(row.seq, "format_noise", kinds=kinds))

    # early_reveal (discussion domains only)
    if option_res and row.round < REVEAL_ROUND:
        hit = [name for name, rx in option_res if rx.search(text)]
        if hit:
            out.append(_v(row.seq, "early_reveal", kind="option_name", names=hit))
        for label, name, token, rx in (partial_res or []):
            if name in hit:
                continue
            if rx.search(text):
                out.append(_v(row.seq, "early_reveal_partial", token=token, label=label, name=name))
        if row.round == 1 and card_ngrams:
            grams = _ngrams(_normalize_words(text), CARD_NGRAM)
            if grams:
                for card_id, cg in card_ngrams:
                    common = grams & cg
                    if common:
                        out.append(_v(row.seq, "early_reveal", kind="card_text", card_id=card_id,
                                      ngram=" ".join(min(common))))
    return out


def _check_pass(row: LogRow) -> list[dict[str, Any]]:
    """Pass rows with a ``raw`` that differs from the token beyond whitespace. Forced skips (timeout /
    ``ForceSkip``) and empty-reply Overs are protocol outcomes, not punctuation variants."""
    raw = row.extra.get("raw")
    if raw is None or row.extra.get("forced") or row.extra.get("empty"):
        return []
    raw = str(raw)
    if raw.strip() == row.text or raw.strip() == T_FORCE_SKIP:
        return []
    return [_v(row.seq, "pass_punct", _kind=NORMALIZED, token=row.text, raw=raw)]


# ---- public API ---------------------------------------------------------------------------------
def partial_tokens(name: str) -> list[str]:
    """Tokens of an option name that count for ``early_reveal_partial`` (letters only, >= 5, no stopword)."""
    out: list[str] = []
    for tok in _LETTERS_RE.findall(name):
        if len(tok) >= PARTIAL_MIN_LETTERS and tok.lower() not in PARTIAL_STOPWORDS and tok not in out:
            out.append(tok)
    return out


def find_violations(rows: list[LogRow], ctx: GameContext) -> list[dict[str, Any]]:
    """Method-independent violations on talk / pass rows. Items are ``{seq, code, detail}`` in seq order."""
    names = list(ctx.names)
    label_any = _label_re(names)
    word_cap = ctx.rules.get("word_cap")
    word_cap = int(word_cap) if word_cap is not None else None
    option_res: list[tuple[str, re.Pattern[str]]] = []
    partial_res: list[tuple[str, str, str, re.Pattern[str]]] = []
    card_ngrams: list[tuple[str, set]] = []
    if ctx.domain != "aiwolf" and ctx.instance is not None:
        # words that are legitimate vocabulary of this instance (problems, cards, topic context): a token of an
        # option name that occurs there is not a reveal (e.g. "campus" in a card about commuting)
        material = " ".join([str(ctx.instance["topic"].get("title", "")), str(ctx.instance["topic"].get("context", ""))]
                            + [str(p) for p in ctx.instance.get("problems", {}).values()]
                            + [str(c.get("text", "")) for c in ctx.card_pool()])
        material_words = set(_normalize_words(material))
        for o in ctx.options():
            name = str(o.get("name", "")).strip()
            if name:
                pat = r"\b" + r"\s+".join(re.escape(w) for w in name.split()) + r"\b"
                option_res.append((name, re.compile(pat, re.IGNORECASE)))
                for token in partial_tokens(name):
                    if token.lower() in material_words:
                        continue
                    partial_res.append((str(o.get("label", "")), name, token,
                                        re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)))
        # card titles are public from the start (dynamic mode): the title's word sequence is cut out of the
        # card text before its n-grams are taken, so quoting a title never counts as revealed card text
        for c in ctx.card_pool():
            words = _normalize_words(str(c.get("text", "")))
            tw = _normalize_words(str(c.get("title", "")))
            if tw:
                i = 0
                while i <= len(words) - len(tw):
                    if words[i:i + len(tw)] == tw:
                        del words[i:i + len(tw)]
                    else:
                        i += 1
            g = _ngrams(words, CARD_NGRAM)
            if g:
                card_ngrams.append((c["card_id"], g))
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.type == "talk":
            out.extend(_notes(row))
            out.extend(_check_talk(row, ctx, names, label_any, option_res, card_ngrams, word_cap,
                                   partial_res))
        elif row.type == "pass":
            noted = _notes(row)
            out.extend(noted)
            if not any(it["code"] == "pass_punct" for it in noted):
                out.extend(_check_pass(row))
    return out


def find_truncations(jsonl_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """``truncated`` items from jsonl ``llm_call`` records (finish_reason == length or truncated true)."""
    out: list[dict[str, Any]] = []
    for rec in jsonl_records:
        if rec.get("kind") != "llm_call":
            continue
        fr = rec.get("finish_reason")
        if not (rec.get("truncated") or fr == "length"):
            continue
        out.append(_v(rec.get("seq"), "truncated", source="llm_call", seat=rec.get("seat"),
                      seat_seq=rec.get("seat_seq"), request=rec.get("request"), round=rec.get("round"),
                      turn=rec.get("turn"), finish_reason=fr))
    return out


def summarize(violations: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count per code; every known code appears (0 when absent), unknown codes are appended."""
    c = Counter(v["code"] for v in violations)
    out = {code: c.pop(code, 0) for code in CODES}
    out.update(sorted(c.items()))
    return out


def summarize_kinds(violations: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Counts by ``kind``: real violations vs normalisation records (items without a kind count as violations)."""
    c = Counter(str(v.get("kind") or VIOLATION) for v in violations)
    return {VIOLATION: c.get(VIOLATION, 0), NORMALIZED: c.get(NORMALIZED, 0)}


def merge_violations(existing: Iterable[dict[str, Any]], recomputed: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """One ``violations`` record from structural items + recomputed common ones.

    Keeps every existing item that is not a row-level common one (code not in ``CODES``, or a structural
    item from the single converter that carries a markdown ``line``), appends the recomputed common items,
    and drops duplicates (same seq and code; for items without a row, same code and detail).
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def key(it: dict[str, Any]) -> str:
        # The same row-level finding may be reported by the single converter (structural pass) and by
        # find_violations (common pass): one item per (seq, code) when the row is known.
        if it.get("seq") is not None:
            return json.dumps({"seq": it.get("seq"), "code": it.get("code")}, sort_keys=True)
        return json.dumps({"seq": None, "code": it.get("code"), "detail": it.get("detail")},
                          sort_keys=True, ensure_ascii=False, default=str)

    for it in existing:
        if it.get("code") in CODES and it.get("line") is None:
            continue
        k = key(it)
        if k not in seen:
            seen.add(k)
            out.append(it)
    by_key = {key(it): i for i, it in enumerate(out)}
    for it in recomputed:
        k = key(it)
        if k not in seen:
            seen.add(k)
            by_key[k] = len(out)
            out.append(it)
        elif k in by_key and "kind" not in out[by_key[k]] and "kind" in it:
            out[by_key[k]] = it  # an item from an older log without a kind: take the recomputed one
    return out


__all__ = ["CARD_NGRAM", "CODES", "NORMALIZED", "PARTIAL_STOPWORDS", "REVEAL_ROUND", "VIOLATION", "find_truncations",
           "find_violations", "merge_violations", "partial_tokens", "summarize", "summarize_kinds"]
