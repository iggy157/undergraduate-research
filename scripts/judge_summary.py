"""Aggregate pairwise judgements (LLM judge or human raters) over the pairs of scripts/render_judge_pairs.py.

usage: .venv/bin/python scripts/judge_summary.py --judge-dir <dir with pairs.json and out/*.json> [--metrics games.csv]

Each out/<rater>_<set>_<order>.json is a JSON list of {"pair", "verdict", "reasons", "cues"}. The verdict is mapped
back to the conditions through pairs.json (o1 / o2), so that the summary reports, per comparison, how often the
first condition of the comparison won. A pair judged in both orders by the same rater counts as "consistent" when
the same condition wins in both; an "order effect" is the share of such pairs whose winner flips with the position.
If --metrics is given, "longer wins" is the share of decided judgements in which the transcript with more words won.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

COMPARISONS = {"C1": ("single-batch", "multi-private"), "C2": ("single-batch", "single-online"),
               "C3": ("single-online", "multi-public"), "C4": ("multi-public", "multi-private"),
               "C5": ("single-batch", "single-batch-process")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge-dir", required=True)
    ap.add_argument("--metrics", default=None, help="games.csv of scripts/eval_metrics.py (for the length check)")
    a = ap.parse_args(argv)
    d = Path(a.judge_dir)
    pairs = json.loads((d / "pairs.json").read_text())
    assignments = json.loads((d / "assignments.json").read_text()) if (d / "assignments.json").exists() else {}
    words = {}
    if a.metrics:
        with open(a.metrics, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                words[r["game_id"]] = float(r["words_total"])
    # judgements: (rater, pair, order) -> winner condition or "Tie"
    J: dict[tuple, str] = {}
    reasons: list[dict] = []
    for fp in sorted((d / "out").glob("*.json")):
        m = re.match(r"(\w+?)_(\d+)_(o[12])\.json$", fp.name)
        if not m:
            continue
        rater, set_no, order = m.group(1), m.group(2), m.group(3)
        in_set = assignments.get(set_no, [])
        try:
            items = json.loads(fp.read_text())
        except json.JSONDecodeError as e:
            print(f"!! {fp.name}: {e}")
            continue
        for it in items:
            pid = re.sub(r"_o[12](\.md)?$", "", it["pair"])
            if pid not in pairs:  # a rater that dropped the comparison suffix: recover it from the rater's set
                cand = [p for p in in_set if p.split("__")[0] == pid]
                if len(cand) == 1:
                    pid = cand[0]
            if pid not in pairs:
                print(f"!! {fp.name}: unknown pair {it['pair']}")
                continue
            v = it["verdict"].strip()
            win = "Tie" if v.lower() == "tie" else pairs[pid][order][v]
            J[(rater, pid, order)] = win
            reasons.append({"rater": rater, "pair": pid, "order": order, "comparison": pairs[pid]["comparison"],
                            "setup": pairs[pid]["setup_id"], "winner": win, "A": pairs[pid][order]["A"],
                            "B": pairs[pid][order]["B"], "verdict": v, "reasons": it.get("reasons", ""),
                            "cues": it.get("cues", [])})
    raters = sorted({k[0] for k in J})
    out = []
    out.append(f"# Pairwise judgements: {d}  ({len(J)} judgements, raters: {', '.join(raters)})\n")
    out.append("## Win rate of the first condition, per comparison and rater (both orders pooled; Tie = 0.5)\n")
    out.append("| comparison | first vs second | " + " | ".join(raters) + " | all | n |")
    out.append("|---|---|" + "---|" * (len(raters) + 2))
    for cid, (c1, c2) in COMPARISONS.items():
        cells = []
        tot = []
        for r in raters:
            js = [w for (rr, pid, o), w in J.items() if rr == r and pairs[pid]["comparison"] == cid]
            if js:
                s = sum(1.0 if w == c1 else 0.5 if w == "Tie" else 0.0 for w in js) / len(js)
                cells.append(f"{s:.2f} ({sum(w == c1 for w in js)}-{sum(w == 'Tie' for w in js)}-{sum(w == c2 for w in js)})")
                tot += js
            else:
                cells.append("")
        s = sum(1.0 if w == c1 else 0.5 if w == "Tie" else 0.0 for w in tot) / len(tot) if tot else float("nan")
        out.append(f"| {cid} | {c1} vs {c2} | " + " | ".join(cells) + f" | {s:.2f} | {len(tot)} |")
    out.append("\nCells: win rate of the first condition (wins-ties-losses).\n")
    # per domain
    out.append("## Win rate of the first condition per domain (all raters, both orders)\n")
    doms = sorted({pairs[p]["setup_id"].rsplit("_", 1)[0] for p in pairs})
    out.append("| comparison | " + " | ".join(doms) + " |")
    out.append("|---|" + "---|" * len(doms))
    for cid, (c1, c2) in COMPARISONS.items():
        cells = []
        for dom in doms:
            js = [w for (rr, pid, o), w in J.items() if pairs[pid]["comparison"] == cid and pairs[pid]["setup_id"].startswith(dom)]
            cells.append(f"{sum(1.0 if w == c1 else 0.5 if w == 'Tie' else 0.0 for w in js) / len(js):.2f} (n={len(js)})" if js else "")
        out.append(f"| {cid} | " + " | ".join(cells) + " |")
    # order consistency
    out.append("\n## Order effect (same rater, same pair, both orders)\n")
    out.append("| rater | pairs with both orders | same winner | flipped | tie in one |")
    out.append("|---|---|---|---|---|")
    for r in raters:
        pids = {pid for (rr, pid, o) in J if rr == r}
        both = [pid for pid in pids if (r, pid, "o1") in J and (r, pid, "o2") in J]
        same = sum(1 for pid in both if J[(r, pid, "o1")] == J[(r, pid, "o2")] and J[(r, pid, "o1")] != "Tie")
        tie1 = sum(1 for pid in both if "Tie" in (J[(r, pid, "o1")], J[(r, pid, "o2")]) and J[(r, pid, "o1")] != J[(r, pid, "o2")])
        flip = len(both) - same - tie1 - sum(1 for pid in both if J[(r, pid, "o1")] == J[(r, pid, "o2")] == "Tie")
        out.append(f"| {r} | {len(both)} | {same} | {flip} | {tie1} |")
    # position bias: how often A (first shown) wins
    out.append("\n## Position: share of decided judgements won by the transcript shown first (A)\n")
    for r in raters:
        dec = [(pid, o, w) for (rr, pid, o), w in J.items() if rr == r and w != "Tie"]
        a_wins = sum(1 for pid, o, w in dec if pairs[pid][o]["A"] == w)
        out.append(f"- {r}: {a_wins}/{len(dec)} = {a_wins / len(dec):.2f}" if dec else f"- {r}: no decided judgements")
    # inter-rater agreement (per pair+order)
    if len(raters) >= 2:
        out.append("\n## Agreement between raters (same pair, same order)\n")
        for i in range(len(raters)):
            for j in range(i + 1, len(raters)):
                keys = [(pid, o) for (rr, pid, o) in J if rr == raters[i] and (raters[j], pid, o) in J]
                agree = sum(1 for pid, o in keys if J[(raters[i], pid, o)] == J[(raters[j], pid, o)])
                out.append(f"- {raters[i]} vs {raters[j]}: {agree}/{len(keys)} = {agree / len(keys):.2f}" if keys else "")
    # length check
    if words:
        out.append("\n## Length: share of decided judgements won by the transcript with more words\n")
        for r in raters + ["all"]:
            dec = [(pid, w) for (rr, pid, o), w in J.items() if (r == "all" or rr == r) and w != "Tie"]
            longer = 0
            n = 0
            for pid, w in dec:
                g = pairs[pid]["games"]
                conds = list(g)
                lw = {c: words.get(g[c], float("nan")) for c in conds}
                if any(v != v for v in lw.values()):
                    continue
                n += 1
                longer += lw[w] == max(lw.values())
            out.append(f"- {r}: {longer}/{n} = {longer / n:.2f}" if n else f"- {r}: n/a")
    # cue tags
    out.append("\n## Cue tags given by the raters (top 15, per winner family)\n")
    fam = lambda c: "single" if c.startswith("single") else "multi"
    cnt: dict[str, Counter] = defaultdict(Counter)
    for it in reasons:
        if it["winner"] != "Tie":
            for c in it["cues"]:
                cnt[fam(it["winner"])][c.strip().lower()] += 1
    for k in ("single", "multi"):
        out.append(f"- when a {k} transcript won: " + "; ".join(f"{c} ({n})" for c, n in cnt[k].most_common(15)))
    text = "\n".join(out) + "\n"
    (d / "summary.md").write_text(text, encoding="utf-8")
    with (d / "judgements.jsonl").open("w", encoding="utf-8") as f:
        for it in reasons:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
