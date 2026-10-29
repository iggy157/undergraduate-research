"""Question -> answer rate derived from the v2 annotations (resp_to / resp_type), plus the position-aligned
content rate (ANNOTATION_INSTRUCTIONS v2; scripts/annotation_summary.py gives the main tables).

usage: .venv/bin/python scripts/annotation_qa.py --annot-dir <dir with games/, games.json, out/>

A question is an utterance whose text contains "?"; it is addressed when it contains "@Name". It counts as answered
when a later utterance in the same period (by the addressed participant if any, else by anyone else) has
resp_to = its id and resp_type = answer, according to the rater. Rates per condition and rater.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

ORDER = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "single-batch-process", "multi-private-process", "multi-private-stepped", "multi-public-stepped", "multi-private-stepped-process"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annot-dir", required=True)
    a = ap.parse_args(argv)
    d = Path(a.annot_dir)
    games = json.loads((d / "games.json").read_text())
    utts = {}  # game -> seq -> (speaker, text, period)
    for g in games:
        rows, period = {}, None
        for line in (d / "games" / g).read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                period = line[3:]
            m = re.match(r"- \[(\d+)\] \*\*(.+?)\*\*: (.*)", line)
            if m:
                rows[int(m.group(1))] = (m.group(2), m.group(3), period)
        utts[g] = rows
    ann = defaultdict(dict)
    for fp in sorted((d / "out").glob("*.json")):
        m = re.match(r"([A-Za-z0-9]+)_(?:_[^/]+|\d+)\.json$", fp.name)
        if not m:
            continue
        for g, items in json.loads(fp.read_text()).items():
            g = Path(g).name
            if g in games:
                ann[m.group(1)][g] = {int(i["seq"]): i for i in items if str(i.get("seq", "")).isdigit()}
    raters = sorted(ann)
    out = ["# Question -> answer rate (derived from resp_to / resp_type)\n",
           "| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee |",
           "|---|---|---|---|---|---|"]
    for cond in ORDER:
        for r in raters:
            nq, nad, ans_any, ans_addr, ng = [], 0, 0, 0, 0
            for g, info in games.items():
                if info["condition"] != cond or g not in ann[r]:
                    continue
                ng += 1
                rows, an = utts[g], ann[r][g]
                q_in_game = 0
                for seq, (spk, text, period) in rows.items():
                    if "?" not in text:
                        continue
                    q_in_game += 1
                    m = re.search(r"@(\w+)", text)
                    addressee = m.group(1) if m else None
                    if addressee:
                        nad += 1
                    later = [(s2, rows[s2]) for s2 in rows if s2 > seq and rows[s2][2] == period]
                    hit_any = hit_addr = False
                    for s2, (spk2, _, _) in later:
                        it = an.get(s2)
                        if it and it.get("resp_to") == seq and it.get("resp_type") == "answer":
                            hit_any = True
                            if addressee and spk2 == addressee:
                                hit_addr = True
                    ans_any += hit_any
                    ans_addr += hit_addr
                nq.append(q_in_game)
            tot = sum(nq)
            if ng and tot:
                out.append(f"| {cond} | {r} | {st.mean(nq):.1f} | {nad / tot:.2f} | {ans_any / tot:.2f} | "
                           f"{(ans_addr / nad) if nad else float('nan'):.2f} |")
    out.append("\n# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)\n")
    out.append("| period | turn | " + " | ".join(ORDER) + " |")
    out.append("|---|---|" + "---|" * len(ORDER))
    acc = defaultdict(lambda: defaultdict(list))
    for g, info in games.items():
        for r in raters:
            for seq, it in ann[r].get(g, {}).items():
                pt = info["turn"].get(str(seq))
                if pt:
                    c = it.get("content")
                    acc[(pt[0], pt[1])][info["condition"]].append(max(0, min(2, int(c))) if isinstance(c, (int, float)) else 0)
    for (p, t) in sorted(acc):
        out.append(f"| {p} | {t} | " + " | ".join(f"{st.mean(acc[(p, t)][c]):.2f} (n={len(acc[(p, t)][c])})" if acc[(p, t)][c] else "" for c in ORDER) + " |")
    text = "\n".join(out) + "\n"
    (d / "qa_summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
