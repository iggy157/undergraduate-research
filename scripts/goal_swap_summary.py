"""Summarise scripts/goal_swap.py output: words of the recorded line vs the line re-generated from the same state
under the other generation goal, overall and by position (the first turn of a period vs later turns).

usage: python scripts/goal_swap_summary.py --files <label>=<jsonl> [<label>=<jsonl> ...] [--out <md>]
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path


def summarise(label: str, fp: Path) -> list[str]:
    rows = [json.loads(l) for l in fp.read_text().splitlines() if l.strip()]
    if not rows:
        return [f"## {label}: no rows\n"]
    src = rows[0]["source"]
    a, b = ("online (recorded)", "batch (swapped)") if src == "multi-private" else ("batch (recorded)", "online (swapped)")
    out = [f"## {label}: {len(rows)} states from {len({r['game_id'] for r in rows})} games (source {src})\n",
           f"| position | n | words {a} | words {b} | diff | share shorter | share longer | pass {a} | pass {b} |",
           "|---|---|---|---|---|---|---|---|---|"]
    groups = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups["period turn 1" if r.get("turn") == 1 else "later turns"].append(r)
        groups[f"round {r.get('round')}"].append(r)
    for k in ["all", "period turn 1", "later turns"] + sorted(k for k in groups if k.startswith("round ")):
        g = groups[k]
        wo = [r["words_orig"] for r in g]
        ws = [r["words_swap"] for r in g]
        d = [s - o for o, s in zip(wo, ws)]
        out.append(f"| {k} | {len(g)} | {st.mean(wo):.1f} | {st.mean(ws):.1f} | {st.mean(d):+.1f} | "
                   f"{sum(x < 0 for x in d) / len(d):.2f} | {sum(x > 0 for x in d) / len(d):.2f} | "
                   f"{sum(o == 0 for o in wo) / len(g):.2f} | {sum(s == 0 for s in ws) / len(g):.2f} |")
    # per-setup paired comparison
    per = defaultdict(lambda: [[], []])
    for r in rows:
        per[r["setup"]][0].append(r["words_orig"])
        per[r["setup"]][1].append(r["words_swap"])
    diffs = [st.mean(v[1]) - st.mean(v[0]) for v in per.values()]
    out.append(f"\nPer-setup mean difference (swapped − recorded): median {st.median(diffs):+.1f} words, "
               f"swapped shorter in {sum(x < 0 for x in diffs)}/{len(diffs)} setups.\n")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = ["# Goal swap on identical histories (scripts/goal_swap.py)\n",
           "The same recorded game state (system prompt + transcript so far + the seat's label) is given to the model "
           "under the other generation goal: online = the state as the user message (next line only); batch = the "
           "single-batch writing request as the user message and the transcript continued as the model's own output. "
           "Greedy, the seat's stop strings. words = whitespace tokens (0 for Skip / Over).\n"]
    for item in a.files:
        label, fp = item.split("=", 1)
        rows = [json.loads(l) for l in Path(fp).read_text().splitlines() if l.strip()]
        by_cond = defaultdict(list)
        for r in rows:  # plan conditions share the log folder of their base condition: report them apart
            by_cond[r["game_id"].split("__")[1]].append(r)
        for cond in sorted(by_cond):
            tmp = Path(fp).with_suffix(f".{cond}.tmp")
            tmp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in by_cond[cond]) + "\n")
            out += summarise(f"{label} ({cond})", tmp)
            tmp.unlink()
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
