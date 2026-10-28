"""Aggregate utterance-level annotations (scripts/render_annotation.py + ANNOTATION_INSTRUCTIONS.md).

usage: .venv/bin/python scripts/annotation_summary.py --annot-dir <dir with games.json and out/<rater>_<set>.json>

Each out file maps game file names to lists of {seq, speaker, resp, rebut, empty, ignore, misattr, reversal}.
The summary gives, per condition and rater, the rate of each flag per 100 utterances (game means, then condition
means), the agreement between raters per flag (percent agreement and Cohen's kappa over utterances both annotated),
and per-domain tables.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

FLAGS = ["resp", "rebut", "empty", "ignore", "misattr", "reversal"]
ORDER = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "single-batch-process", "multi-private-process"]


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annot-dir", required=True)
    a = ap.parse_args(argv)
    d = Path(a.annot_dir)
    games = json.loads((d / "games.json").read_text())
    # ann[rater][game][seq] = {flag: 0/1}
    ann: dict[str, dict[str, dict[int, dict]]] = defaultdict(dict)
    problems = []
    for fp in sorted((d / "out").glob("*.json")):
        m = re.match(r"(\w+?)_(\d+)\.json$", fp.name)
        if not m:
            continue
        rater = m.group(1)
        try:
            obj = json.loads(fp.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{fp.name}: {e}")
            continue
        for g, items in obj.items():
            g = g if g.endswith(".md") else g + ".md"
            if g not in games:
                problems.append(f"{fp.name}: unknown game {g}")
                continue
            rows = {}
            for it in items:
                try:
                    rows[int(it["seq"])] = {f: int(it.get(f, 0) or 0) for f in FLAGS}
                except (KeyError, ValueError, TypeError):
                    problems.append(f"{fp.name}: bad item in {g}: {it}")
            if len(rows) != games[g]["n_talk"]:
                problems.append(f"{fp.name}: {g} has {len(rows)} annotations for {games[g]['n_talk']} utterances")
            ann[rater][g] = rows
    raters = sorted(ann)
    out = [f"# Utterance-level annotations: {d}  (raters: {', '.join(raters)}; {len(games)} games)\n"]
    if problems:
        out.append("Problems:\n" + "\n".join(f"- {p}" for p in problems) + "\n")

    def rate_table(title, filt):
        out.append(f"## {title}\n")
        out.append("| condition | games | rater | " + " | ".join(FLAGS) + " |")
        out.append("|---|---|---|" + "---|" * len(FLAGS))
        for cond in ORDER:
            gs = [g for g, info in games.items() if info["condition"] == cond and filt(info)]
            if not gs:
                continue
            for r in raters:
                per_game = {f: [] for f in FLAGS}
                n = 0
                for g in gs:
                    rows = ann[r].get(g)
                    if not rows:
                        continue
                    n += 1
                    for f in FLAGS:
                        per_game[f].append(100 * sum(v[f] for v in rows.values()) / len(rows))
                if n:
                    out.append(f"| {cond} | {n} | {r} | " + " | ".join(f"{st.mean(per_game[f]):.1f}" for f in FLAGS) + " |")
        out.append("")

    rate_table("Rate per 100 utterances (game mean, then condition mean; all domains)", lambda i: True)
    for dom in sorted({i["domain"] for i in games.values()}):
        rate_table(f"Rate per 100 utterances: {dom}", lambda i, dom=dom: i["domain"] == dom)
    if len(raters) >= 2:
        out.append("## Agreement between raters (utterances annotated by both)\n")
        out.append("| flag | n | percent agreement | Cohen's kappa | rate " + raters[0] + " | rate " + raters[1] + " |")
        out.append("|---|---|---|---|---|---|")
        r0, r1 = raters[0], raters[1]
        for f in FLAGS:
            A, B = [], []
            for g in games:
                x, y = ann[r0].get(g), ann[r1].get(g)
                if not x or not y:
                    continue
                for seq in x:
                    if seq in y:
                        A.append(x[seq][f])
                        B.append(y[seq][f])
            if A:
                po = sum(1 for p, q in zip(A, B) if p == q) / len(A)
                out.append(f"| {f} | {len(A)} | {po:.2f} | {kappa(A, B):.2f} | {100 * sum(A) / len(A):.1f} | {100 * sum(B) / len(B):.1f} |")
        out.append("")
    text = "\n".join(out) + "\n"
    (d / "summary.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
