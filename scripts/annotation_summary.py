"""Aggregate utterance-level annotations (scripts/render_annotation.py + ANNOTATION_INSTRUCTIONS v1 or v2).

usage: .venv/bin/python scripts/annotation_summary.py --annot-dir <dir with games.json and out/<rater>_<set>.json>

Each out file maps game file names to lists of per-utterance objects. v1 flags: resp, rebut, empty, ignore,
misattr, reversal. v2 fields: content (0/1/2), resp, resp_to, resp_type, rebut, padded. Both are handled: a v2
file gets ``empty = (content == 0)``. The summary gives, per condition and rater, the rate of each flag per 100
utterances (game means, then condition means), density figures when games.json carries per-utterance word
counts (words per new contribution, share of words in no-progress utterances, contributions per game), the
distribution of resp_type, agreement between raters per flag (percent agreement and Cohen's kappa), and
per-domain tables. ``--by-position`` adds the rates by period and turn (survivorship check).
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

V1_FLAGS = ["resp", "rebut", "empty", "ignore", "misattr", "reversal"]
V2_FLAGS = ["resp", "rebut", "empty", "padded"]
ORDER = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "single-batch-process", "multi-private-process"]
TYPES = ["answer", "add", "object", "agree"]


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def norm_item(it: dict) -> dict | None:
    try:
        seq = int(it["seq"])
    except (KeyError, ValueError, TypeError):
        return None
    out = {"seq": seq}
    if "content" in it:  # v2
        c = it.get("content")
        c = int(c) if isinstance(c, (int, float)) else 0
        out["content"] = max(0, min(2, c))
        out["empty"] = int(c == 0)
        out["padded"] = int(bool(it.get("padded", 0)))
        out["resp_to"] = it.get("resp_to")
        out["resp_type"] = it.get("resp_type") if it.get("resp_type") in TYPES else None
    for f in V1_FLAGS:
        if f in it:
            out[f] = int(bool(it[f]))
    out.setdefault("resp", 0)
    out.setdefault("rebut", 0)
    out.setdefault("empty", 0)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annot-dir", required=True)
    ap.add_argument("--by-position", action="store_true")
    a = ap.parse_args(argv)
    d = Path(a.annot_dir)
    games = json.loads((d / "games.json").read_text())
    ann: dict[str, dict[str, dict[int, dict]]] = defaultdict(dict)
    problems = []
    for fp in sorted((d / "out").glob("*.json")):
        m = re.match(r"([A-Za-z0-9]+)_(?:_[^/]+|\d+)\.json$", fp.name)
        if not m:
            continue
        rater = m.group(1)
        try:
            obj = json.loads(fp.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{fp.name}: {e}")
            continue
        for g, items in obj.items():
            g = Path(g).name  # tolerate "games/<name>.md"
            g = g if g.endswith(".md") else g + ".md"
            if g not in games:
                problems.append(f"{fp.name}: unknown game {g}")
                continue
            rows = {}
            for it in items:
                n = norm_item(it)
                if n is None:
                    problems.append(f"{fp.name}: bad item in {g}: {str(it)[:80]}")
                else:
                    rows[n["seq"]] = n
            if len(rows) != games[g]["n_talk"]:
                problems.append(f"{fp.name}: {g} has {len(rows)} annotations for {games[g]['n_talk']} utterances")
            ann[rater][g] = rows
    raters = sorted(ann)
    v2 = any("content" in r for rt in ann.values() for rows in rt.values() for r in rows.values())
    flags = V2_FLAGS if v2 else V1_FLAGS
    has_words = all("words" in info for info in games.values())
    out = [f"# Utterance-level annotations: {d}  (raters: {', '.join(raters)}; {len(games)} games; "
           f"{'v2' if v2 else 'v1'} fields)\n"]
    if problems:
        out.append("Problems:\n" + "\n".join(f"- {p}" for p in problems) + "\n")

    def game_stats(rows: dict[int, dict], info: dict) -> dict:
        n = len(rows)
        s = {f: 100 * sum(v[f] for v in rows.values()) / n for f in flags}
        if v2 and has_words:
            words = info["words"]
            tot_w = sum(words.get(str(q), 0) for q in rows)
            contrib = sum(v["content"] for v in rows.values())
            empty_w = sum(words.get(str(q), 0) for q, v in rows.items() if v["empty"])
            s["contrib_per_game"] = contrib
            s["words_per_contrib"] = tot_w / contrib if contrib else float("nan")
            s["empty_word_share"] = 100 * empty_w / tot_w if tot_w else float("nan")
        return s

    def table(title, filt):
        cols = flags + (["contrib_per_game", "words_per_contrib", "empty_word_share"] if v2 and has_words else [])
        out.append(f"## {title}\n")
        out.append("| condition | games | rater | " + " | ".join(cols) + " |")
        out.append("|---|---|---|" + "---|" * len(cols))
        for cond in ORDER:
            gs = [g for g, info in games.items() if info["condition"] == cond and filt(info)]
            if not gs:
                continue
            for r in raters:
                per = defaultdict(list)
                n = 0
                for g in gs:
                    rows = ann[r].get(g)
                    if not rows:
                        continue
                    n += 1
                    for k, v in game_stats(rows, games[g]).items():
                        if v == v:
                            per[k].append(v)
                if n:
                    out.append(f"| {cond} | {n} | {r} | " + " | ".join(f"{st.mean(per[c]):.1f}" if per[c] else "" for c in cols) + " |")
        out.append("")

    table("Per 100 utterances (game mean, then condition mean; all domains)", lambda i: True)
    for dom in sorted({i["domain"] for i in games.values()}):
        table(f"Per 100 utterances: {dom}", lambda i, dom=dom: i["domain"] == dom)
    if v2 and has_words:
        out.append("## Totals per game (condition means; content = number of new contributions)\n")
        out.append("| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |")
        out.append("|---|---|---|---|---|---|---|")
        for cond in ORDER:
            for r in raters:
                tw, tc, tu, n = [], [], [], 0
                for g, info in games.items():
                    if info["condition"] != cond or g not in ann[r]:
                        continue
                    rows = ann[r][g]
                    n += 1
                    tw.append(sum(info["words"].get(str(q), 0) for q in rows))
                    tc.append(sum(v["content"] for v in rows.values()))
                    tu.append(len(rows))
                if n:
                    out.append(f"| {cond} | {r} | {st.mean(tw):.0f} | {st.mean(tu):.1f} | {st.mean(tc):.1f} | "
                               f"{sum(tw) / sum(tc):.1f} | {100 * sum(tc) / sum(tw):.2f} |")
        out.append("")
    if v2:
        out.append("## Response types (share of responsive utterances; all domains)\n")
        out.append("| condition | rater | " + " | ".join(TYPES) + " |")
        out.append("|---|---|" + "---|" * len(TYPES))
        for cond in ORDER:
            for r in raters:
                cnt = Counter()
                for g, info in games.items():
                    if info["condition"] != cond or g not in ann[r]:
                        continue
                    for v in ann[r][g].values():
                        if v["resp"] and v.get("resp_type"):
                            cnt[v["resp_type"]] += 1
                tot = sum(cnt.values())
                if tot:
                    out.append(f"| {cond} | {r} | " + " | ".join(f"{100 * cnt[t] / tot:.0f}" for t in TYPES) + " |")
        out.append("")
    if a.by_position and all("turn" in info for info in games.values()):
        out.append("## Rates by period and turn (all raters pooled; empty / resp per 100 utterances)\n")
        out.append("| condition | period | turn | n | empty | resp |")
        out.append("|---|---|---|---|---|---|")
        for cond in ORDER:
            acc = defaultdict(lambda: [0, 0, 0])
            for g, info in games.items():
                if info["condition"] != cond:
                    continue
                for r in raters:
                    for q, v in ann[r].get(g, {}).items():
                        pt = info["turn"].get(str(q))
                        if pt:
                            acc[(pt[0], pt[1])][0] += 1
                            acc[(pt[0], pt[1])][1] += v["empty"]
                            acc[(pt[0], pt[1])][2] += v["resp"]
            for (p, t), (n, e, rr) in sorted(acc.items()):
                out.append(f"| {cond} | {p} | {t} | {n} | {100 * e / n:.0f} | {100 * rr / n:.0f} |")
        out.append("")
    if len(raters) >= 2:
        from itertools import combinations
        out.append("## Agreement between raters (utterances annotated by both; every pair)\n")
        out.append("| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |")
        out.append("|---|---|---|---|---|---|---|")
        for r0, r1 in combinations(raters, 2):
            for f in flags + (["content"] if v2 else []):
                A, B = [], []
                for g in games:
                    x, y = ann[r0].get(g), ann[r1].get(g)
                    if not x or not y:
                        continue
                    for seq in x:
                        if seq in y:
                            A.append(x[seq][f])
                            B.append(y[seq][f])
                if not A:
                    continue
                po = sum(1 for a_, b_ in zip(A, B) if a_ == b_) / len(A)
                if f == "content":
                    out.append(f"| {r0} vs {r1} | content (0/1/2) | {len(A)} | {po:.2f} | - | mean {st.mean(A):.2f} | mean {st.mean(B):.2f} |")
                else:
                    out.append(f"| {r0} vs {r1} | {f} | {len(A)} | {po:.2f} | {kappa(A, B):.2f} | {100 * sum(A) / len(A):.1f} | {100 * sum(B) / len(B):.1f} |")
        out.append("")
    text = "\n".join(out) + "\n"
    (d / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
