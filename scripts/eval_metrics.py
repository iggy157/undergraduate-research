"""Automatic evaluation metrics (docs/paper_draft.md §5): one row per game, a per-condition summary and a
candidate list for hand verification.

usage: <python with torch+transformers> scripts/eval_metrics.py --log-dir log/_pilot6 --out-dir <dir> [--no-embed]

Family A (conversation; higher = less verbose / less repetitive):
  words_per_utt   mean words of talk rows (PLACES words-per-turn; one utterance per turn here)
  cap_pin         share of talk rows with >= CAP_PIN_WORDS words (the cap is rules.word_cap = 40)
  nonrep          Bo et al. 2026 Non-repetition: per speaker, over consecutive own utterances,
                  1 - max(Jaccard(words), cos(MiniLM)); mean over speakers. --no-embed drops the cos term.
  skip, over, empty_turns   descriptive: pass tokens and turns in which every living speaker passed
Family B (information; lower = fewer leaks):
  early_option    talk rows before the reveal round that contain a full option name (discussion domains)
  private_use     talk rows (round >= 2) that carry >= 2 distinctive words (or 1 number word) of a card the
                  speaker did not investigate, before any investigator of that card used one of those words
                  (discussion domains). Distinctive = >= 5 letters, not in the public material (topic, card
                  titles) and in no other card's text. Word-level: paraphrases are missed (lower bound);
                  every hit is listed in candidates.jsonl for hand verification.
  seer_first_wolf aiwolf: the Seer's night-0 divination target is the werewolf (chance level 1/4).
  unfounded_wolf  aiwolf: share of day-1 votes for the true werewolf cast by players other than the Seer when
                  no Seer utterance before the vote named the werewolf together with a divination word.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.conditions import parse_condition  # noqa: E402
from common.logwriter import read_log  # noqa: E402
from common.setup import GameContext  # noqa: E402
from common.violations import REVEAL_ROUND  # noqa: E402

CAP_PIN_WORDS = 35
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
STOP = frozenset("""the a an and or but if of to in on for with at by from as is are was were be been being it its this that
these those i you he she we they me him her us them my your his our their not no yes so do does did have has had will
would can could should may might just very really also too about into than then there here what which who whom when
where why how all any some more most other such only own same each every both few many much still even over under
after before while because though although since until again further once per via one two three four five six seven
eight nine ten first second third last next new old good bad well like get got make made take took come came go went
say said see saw know knew think thought want need keep kept let put set use used thing things way ways time times
year years day days week weeks month months people person someone anyone everyone nothing something anything
everything""".split())
NUMBER_WORDS = frozenset("""eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty
fifty sixty seventy eighty ninety hundred thousand half third quarter twice thrice dozen""".split())
DIVINE_RE = re.compile(r"\b(divin\w*|seer|result|werewolf|wolf)\b", re.I)
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text)]


def content_words(text: str) -> set[str]:
    return {w for w in words(text) if len(w) >= 4 and w not in STOP} | {w for w in words(text) if w in NUMBER_WORDS}


def jaccard(a: list[str], b: list[str]) -> float:
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if A and B else 0.0


class Embedder:
    def __init__(self) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(MINILM)
        self.model = AutoModel.from_pretrained(MINILM).eval()
        self.cache: dict[str, object] = {}

    def __call__(self, texts: list[str]):
        todo = [t for t in dict.fromkeys(texts) if t not in self.cache]
        for i in range(0, len(todo), 128):
            batch = todo[i:i + 128]
            enc = self.tok(batch, padding=True, truncation=True, max_length=256, return_tensors="pt")
            with self.torch.no_grad():
                out = self.model(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).float()
            v = (out * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            v = self.torch.nn.functional.normalize(v, p=2, dim=1)
            for t, e in zip(batch, v):
                self.cache[t] = e
        return [self.cache[t] for t in texts]


def game_metrics(game_dir: Path, embed: Embedder | None) -> tuple[dict, list[dict]]:
    log = game_dir / f"{game_dir.name}.log"
    rows = list(read_log(log))
    sid, cond = game_dir.name.split("__")[:2]
    ctx = GameContext.load(sid)
    aiwolf = ctx.domain == "aiwolf"
    talks = [r for r in rows if r.type == "talk"]
    passes = [r for r in rows if r.type == "pass"]
    m: dict = {"game_id": game_dir.name, "setup_id": sid, "domain": ctx.domain, "condition": cond,
               **{k: v for k, v in parse_condition(cond).items() if k in ("method", "generation", "information", "plan")}}
    cands: list[dict] = []
    # ---- family A
    wc = [r.extra.get("words") or len(words(r.text)) for r in talks]
    m["n_talk"] = len(talks)
    m["words_total"] = sum(wc)
    m["words_per_utt"] = sum(wc) / len(wc) if wc else float("nan")
    m["cap_pin"] = sum(1 for w in wc if w >= CAP_PIN_WORDS) / len(wc) if wc else float("nan")
    by_speaker: dict[str, list] = defaultdict(list)
    for r in talks:
        by_speaker[r.agent].append(r.text)
    E = {}
    if embed is not None:
        texts = [r.text for r in talks]
        for t, e in zip(texts, embed(texts)):
            E[t] = e
    per_speaker = []
    for sp, ts in by_speaker.items():
        vals = []
        for j in range(1, len(ts)):
            jac = jaccard(words(ts[j]), words(ts[j - 1]))
            cos = float(E[ts[j]] @ E[ts[j - 1]]) if E else 0.0
            vals.append(1.0 - max(jac, cos))
        if vals:
            per_speaker.append(st.mean(vals))
    m["nonrep"] = st.mean(per_speaker) if per_speaker else float("nan")
    m["skip"] = sum(1 for r in passes if r.text == str(ctx.rules["pass_skip"]))
    m["over"] = sum(1 for r in passes if r.text == str(ctx.rules["pass_over"]))
    turns: dict[tuple, list[str]] = defaultdict(list)
    for r in talks + passes:
        turns[(r.round, r.turn)].append(r.type)
    m["empty_turns"] = sum(1 for v in turns.values() if v and all(t == "pass" for t in v))
    # ---- family B
    if not aiwolf:
        names_rx = [(o["name"], re.compile(r"\b" + re.escape(o["name"]) + r"\b", re.I)) for o in ctx.options()]
        hits = []
        for r in talks:
            if r.round < REVEAL_ROUND:
                h = [n for n, rx in names_rx if rx.search(r.text)]
                if h:
                    hits.append(r)
                    cands.append({"game_id": game_dir.name, "metric": "early_option", "seq": r.seq, "round": r.round,
                                  "turn": r.turn, "speaker": r.agent, "options": h, "text": r.text})
        m["early_option"] = len(hits)
        m["early_option_rate"] = len(hits) / len(talks) if talks else float("nan")
        # private information use
        cards = {c["card_id"]: c for c in ctx.card_pool()}
        public = content_words(" ".join([ctx.instance["topic"].get("title", ""), ctx.instance["topic"].get("context", "")]
                                        + [c["title"] for c in cards.values()]))
        investigators: dict[str, set[str]] = defaultdict(set)
        if ctx.setup.info_mode == "fixed":
            for seat, ids in ctx.instance["fixed_assignment"].items():
                for cid in ids:
                    investigators[cid].add(ctx.name_of_seat(int(seat)))
        for r in rows:
            if r.type == "action" and r.extra.get("action") == "investigate":
                for cid in r.extra.get("cards") or []:
                    investigators[cid].add(r.agent)
        own_cards = defaultdict(set)
        for cid, who in investigators.items():
            for n in who:
                own_cards[n].add(cid)
        # distinctive words of a card: >= 5 letters (or a number word), not public, and in no other card's text
        raw = {cid: content_words(c["text"]) - public for cid, c in cards.items()}
        distinctive = {cid: {w for w in ws if (len(w) >= 5 or w in NUMBER_WORDS)
                             and not any(w in raw[o] for o in raw if o != cid)} for cid, ws in raw.items()}
        said_by_investigator: dict[str, set[str]] = defaultdict(set)
        n_private = 0
        for r in talks:
            if r.round >= 2:
                uw = content_words(r.text)
                own_words = set().union(*[distinctive[c] for c in own_cards[r.agent]]) if own_cards[r.agent] else set()
                for cid, dw in distinctive.items():
                    if r.agent in investigators[cid]:
                        continue
                    matched = (uw & dw) - own_words
                    if not matched:
                        continue
                    new = matched - said_by_investigator[cid]
                    strong = len(new) >= 2 or any(w in NUMBER_WORDS for w in new)
                    if strong:
                        n_private += 1
                        cands.append({"game_id": game_dir.name, "metric": "private_use", "seq": r.seq, "round": r.round,
                                      "turn": r.turn, "speaker": r.agent, "card": cards[cid]["title"],
                                      "investigators": sorted(investigators[cid]), "words": sorted(new), "text": r.text})
                        break
            for cid, dw in distinctive.items():
                if r.agent in investigators[cid]:
                    said_by_investigator[cid] |= content_words(r.text) & dw
        m["private_use"] = n_private
        m["private_use_rate"] = n_private / len(talks) if talks else float("nan")
    else:
        wolf = next(n for n in ctx.names if ctx.role_of_name(n) == "WEREWOLF")
        seer = next(n for n in ctx.names if ctx.role_of_name(n) == "SEER")
        wolf_rx = re.compile(r"\b" + re.escape(wolf) + r"\b")
        seer_pointed = False
        day1_votes = []
        for r in rows:
            if r.type == "talk" and r.agent == seer and r.round <= 1 and wolf_rx.search(r.text) and DIVINE_RE.search(r.text):
                seer_pointed = True
            if r.type == "vote" and r.round == 1 and r.agent != seer:
                day1_votes.append(r.target == wolf)
        first = next((r for r in rows if r.type == "action" and r.extra.get("action") == "divine"), None)
        m["seer_first_wolf"] = int(first is not None and first.target == wolf)
        m["day1_wolf_votes"] = sum(day1_votes)
        m["unfounded_wolf"] = (sum(day1_votes) / len(day1_votes) if day1_votes else float("nan")) if not seer_pointed else 0.0
        m["seer_pointed_day1"] = int(seer_pointed)
        ex = [r for r in rows if r.type == "action" and r.extra.get("action") == "execute" and r.round == 1]
        m["wolf_executed_day1"] = int(bool(ex) and ex[0].target == wolf)
    return m, cands


def fmt(x) -> str:
    return "" if x is None or (isinstance(x, float) and x != x) else (f"{x:.2f}" if isinstance(x, float) else str(x))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default="log/_pilot6")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--no-embed", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    embed = None if a.no_embed else Embedder()
    games = sorted(p for p in Path(a.log_dir).glob("*/*/*") if p.is_dir() and (p / f"{p.name}.log").exists())
    rows, cands = [], []
    for g in games:
        m, c = game_metrics(g, embed)
        rows.append(m)
        cands.extend(c)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("game_id", "setup_id", "domain", "condition"), k))
    with (out / "games.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in keys})
    with (out / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    # per-condition summary (mean over games; one replicate per setup is assumed, replicates are averaged first)
    cols_a = ["n_talk", "words_per_utt", "cap_pin", "nonrep", "skip", "over", "empty_turns"]
    cols_b = ["early_option", "private_use", "seer_first_wolf", "unfounded_wolf", "wolf_executed_day1"]
    lines = [f"# Automatic metrics: {a.log_dir} ({len(rows)} games; embed={'off' if a.no_embed else 'MiniLM'})", ""]
    for dom in sorted({r["domain"] for r in rows}):
        lines += [f"## {dom}", "", "| condition | games | " + " | ".join(cols_a + cols_b) + " |",
                  "|---|---|" + "---|" * (len(cols_a) + len(cols_b))]
        for cond in sorted({r["condition"] for r in rows if r["domain"] == dom}):
            rs = [r for r in rows if r["domain"] == dom and r["condition"] == cond]
            by_setup = defaultdict(list)
            for r in rs:
                by_setup[r["setup_id"]].append(r)
            cells = []
            for k in cols_a + cols_b:
                vals = []
                for srs in by_setup.values():
                    v = [r[k] for r in srs if k in r and r[k] == r[k]]
                    if v:
                        vals.append(sum(v) / len(v))
                cells.append(f"{st.mean(vals):.2f}" if vals else "")
            lines.append(f"| {cond} | {len(rs)} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).",
              "Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; "
              "word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the "
              "true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), "
              "wolf_executed_day1.", ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"candidates: {len(cands)} -> {out / 'candidates.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
