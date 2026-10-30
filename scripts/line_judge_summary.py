"""Summary of the line judge (scripts/line_judge.py, v2 items) on the goal swap and the steering pilots.

A. Goal swap, paired by state: the recorded line and the line re-generated from the same state under the other
   goal, both judged blind with the same protocol. Per history (states from multi-batch games = short history,
   from multi-online games = long history): words, new contributions per line and per 100 words, padded share,
   responsive / rebuttal share, and the named-question rate (the addressee's line points at the question,
   resp_to; per question as in scripts/annotation_qa.py). Per-setup comparison of the content per 100 words.
B. Agreement: Llama vs gpt-oss on the shared lines; line protocol vs the whole-transcript annotation of the same
   recorded lines (annotation dirs with games.json, out/llama__*.json).
C. Steering pilots: per layer and variant.

usage: python scripts/line_judge_summary.py --model gemma --log-dir log/main_gemma31b --annot-dir <dir> --out <md>
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from goal_swap import talk_calls  # noqa: E402


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def load(pattern):
    rows = []
    for f in sorted(glob.glob(pattern)):
        rows += [json.loads(l) for l in open(f)]
    return rows


def stats(x):
    w = sum(r["words"] for r in x)
    c = sum(r["content"] for r in x)
    nq = sum(r["n_questions"] for r in x)
    hit = sum(r["answers_q"] or 0 for r in x)
    return {"n": len(x), "words": w / len(x), "content": c / len(x), "per100": 100 * c / max(w, 1),
            "padded": st.mean(r["padded"] for r in x), "resp": st.mean(r["resp"] for r in x),
            "rebut": st.mean(r["rebut"] for r in x), "nq": nq, "q_rate": hit / nq if nq else float("nan")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--annot-dir", required=True)
    ap.add_argument("--judge-dir", default="log/line_judge")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    L = load(f"{a.judge_dir}/llama__{a.model}*.jsonl")
    G = load(f"{a.judge_dir}/gptoss__{a.model}*.jsonl")
    key = lambda r: (r["kind"], r["game_id"], r["seat"], r["call_seq"], r["variant"], r.get("layer"))
    out = [f"# Line judge (v2 items), {a.model}\n",
           "Each line judged alone in its context (the transcript so far with ids, the line last) with the five items "
           "of ANNOTATION_INSTRUCTIONS_v2, blind to how it was produced. Rater Llama 3.3 70B unless noted.\n"]
    # ---- A
    out.append("## A. Goal swap: the same state, two goals\n")
    out.append("| history | goal | n | words | content / line | content / 100 words | padded | responsive | rebuttal | named questions | answered rate |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    per_state = defaultdict(dict)
    for r in L:
        if r["kind"] == "swap":
            per_state[(r["game_id"], r["seat"], r["call_seq"])][r["variant"].split()[0]] = r
    paired = {k: v for k, v in per_state.items() if "online" in v and "batch" in v}
    setup_diff = defaultdict(lambda: defaultdict(lambda: {"online": [0, 0], "batch": [0, 0]}))
    for hist, src in (("short (multi-batch game)", "multi-private-stepped"), ("long (multi-online game)", "multi-private")):
        states = [v for v in paired.values() if v["online"]["source"] == src]
        for goal in ("batch", "online"):
            s = stats([v[goal] for v in states])
            rec = "recorded" if (goal == "batch") == (src == "multi-private-stepped") else "swapped"
            out.append(f"| {hist} | {goal} ({rec}) | {s['n']} | {s['words']:.1f} | {s['content']:.2f} | {s['per100']:.1f} | "
                       f"{s['padded']:.2f} | {s['resp']:.2f} | {s['rebut']:.2f} | {s['nq']} | {s['q_rate']:.2f} |")
        for v in states:
            g = v["online"]["game_id"].split("__")[0]
            for goal in ("online", "batch"):
                setup_diff[hist][g][goal][0] += v[goal]["content"]
                setup_diff[hist][g][goal][1] += v[goal]["words"]
    out.append("")
    for hist, d in setup_diff.items():
        diffs = [100 * x["batch"][0] / max(x["batch"][1], 1) - 100 * x["online"][0] / max(x["online"][1], 1) for x in d.values()]
        out.append(f"- {hist}: content per 100 words, batch − online per setup: median {st.median(diffs):+.2f}, "
                   f"batch higher in {sum(x > 0 for x in diffs)}/{len(diffs)} setups.")
    # ---- B
    out.append("\n## B. Agreement\n")
    lk = {key(r): r for r in L}
    shared = [(lk[key(g)], g) for g in G if key(g) in lk]
    if shared:
        out.append(f"Llama vs gpt-oss on {len(shared)} shared lines: κ content {kappa([x['content'] for x, _ in shared], [y['content'] for _, y in shared]):.2f}, "
                   f"padded {kappa([x['padded'] for x, _ in shared], [y['padded'] for _, y in shared]):.2f}, "
                   f"resp {kappa([x['resp'] for x, _ in shared], [y['resp'] for _, y in shared]):.2f}, "
                   f"rebut {kappa([x['rebut'] for x, _ in shared], [y['rebut'] for _, y in shared]):.2f}.")
        for goal in ("batch", "online"):
            for nm, rows in (("Llama", [x for x, _ in shared]), ("gpt-oss", [y for _, y in shared])):
                sel = [r for r in rows if r["kind"] == "swap" and r["variant"].startswith(goal)]
                if sel:
                    s = stats(sel)
                    out.append(f"  - {nm}, {goal}: content / 100 words {s['per100']:.1f}, padded {s['padded']:.2f} (n {s['n']})")
    # line protocol vs the whole-transcript annotation, recorded lines
    ad = Path(a.annot_dir)
    games = json.loads((ad / "games.json").read_text())
    by_gid = {info["game_id"]: (g, info) for g, info in games.items()}
    pairs = []
    calls_cache = {}
    for r in L:
        if r["kind"] != "swap" or "recorded" not in r["variant"] or r["game_id"] not in by_gid:
            continue
        g, info = by_gid[r["game_id"]]
        fp = ad / "out" / f"llama__{g[:-3]}.json"
        if not fp.exists():
            continue
        if r["game_id"] not in calls_cache:
            gd = next(Path(a.log_dir).glob(f"*/*/{r['game_id']}"))
            calls_cache[r["game_id"]] = ({(c["seat"], c["seq"]): c for c in talk_calls(gd / "raw")},
                                         {int(i["seq"]): i for i in list(json.loads(fp.read_text()).values())[0] if str(i.get("seq", "")).isdigit()})
        calls, ann = calls_cache[r["game_id"]]
        c = calls[(r["seat"], r["call_seq"])]
        label = c["messages"][-1]["content"].rstrip().split("\n")[-1]
        m = re.match(r"- \*\*(.+?)\*\*:", label)
        if not m:
            continue
        seq = next((int(s) for s, rt in info["turn"].items() if rt == [r["round"], r["turn"]] and int(s) in ann and ann[int(s)].get("speaker") == m.group(1)), None)
        if seq is not None and all(k in ann[seq] for k in ("content", "padded", "resp")):
            pairs.append((r, ann[seq]))
    if pairs:
        out.append(f"\nLine protocol vs whole-transcript annotation (Llama, the same recorded lines, n {len(pairs)}): "
                   f"κ content {kappa([x['content'] for x, _ in pairs], [min(int(y['content']), 2) for _, y in pairs]):.2f}, "
                   f"padded {kappa([x['padded'] for x, _ in pairs], [int(y['padded']) for _, y in pairs]):.2f}, "
                   f"resp {kappa([x['resp'] for x, _ in pairs], [int(y['resp']) for _, y in pairs]):.2f}; "
                   f"mean content {st.mean(x['content'] for x, _ in pairs):.2f} vs {st.mean(min(int(y['content']), 2) for _, y in pairs):.2f}, "
                   f"padded {st.mean(x['padded'] for x, _ in pairs):.2f} vs {st.mean(int(y['padded']) for _, y in pairs):.2f}.")
    # ---- C
    stl = [r for r in L if r["kind"] == "steer"]
    if stl:
        out.append("\n## C. Steering pilots (gemma)\n")
        out.append("| layer | variant | n | words | content / line | padded | broken |")
        out.append("|---|---|---|---|---|---|---|")
        by = defaultdict(list)
        for r in stl:
            by[(r["layer"], r["variant"])].append(r)
        for (layer, v), x in sorted(by.items()):
            out.append(f"| {layer} | {v} | {len(x)} | {st.mean(r['words'] for r in x):.1f} | {st.mean(r['content'] for r in x):.2f} | "
                       f"{st.mean(r['padded'] for r in x):.2f} | {st.mean(1 if r.get('broken') else 0 for r in x):.2f} |")
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
