"""Length probe on identical long-history states with and without discussion examples (the tug-of-war run):
for each goal, the hidden states without examples (hidden/goal_swap/<m>__multi-private, scripts/swap_hidden.py) and
with 3 short examples (hidden/goal_swap_ex/<m>__<goal>_exshort), on the same states; y = words of the line each
produced. Ridge, grouped 5-fold by setup, nested penalty (scripts/probe_hidden2.py). Talk lines only (Skip / Over
dropped) as a check that the result is not a yield effect.

usage: <vllm-server venv python> scripts/tug_probe.py --model gemma --out <md>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from probe_hidden2 import cv_predict, folds_of, pearson, r2  # noqa: E402


def load(d: Path):
    H, rows, layers = [], [], None
    for js in sorted(d.glob("shard*.json")):
        meta = json.loads(js.read_text())
        layers = meta["layers"]
        H.append(np.load(js.with_suffix(".npz"))["h"])
        rows += meta["rows"]
    return np.concatenate(H), rows, layers


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    Hb, rb, layers = load(ROOT / "hidden/goal_swap" / f"{a.model}__multi-private")
    key = lambda r: (r["game_id"], r["seat"], r["call_seq"])
    ib = {key(r): i for i, r in enumerate(rb)}
    out = [f"# Length probe, long-history states with / without 3 short examples: {a.model}\n",
           "Same states (multi-online games). gen = last prompt token. R^2 (r) at each stored layer; `talk` = Skip / Over lines dropped.\n",
           "| goal | examples | n | mean words | " + " | ".join(f"L{l}" for l in layers) + " | best (talk only) |",
           "|---|---|---|---|" + "---|" * len(layers) + "---|"]
    for goal, fi in (("online", 0), ("batch", 1)):
        He, re_, _ = load(ROOT / "hidden/goal_swap_ex" / f"{a.model}__{goal}_exshort")
        common = [k for k in (key(r) for r in re_) if k in ib]
        ie = {key(r): i for i, r in enumerate(re_)}
        groups = np.array([k[0].split("__")[0] for k in common])
        fo = folds_of(groups)
        for lab, X_of, y_of in (("none", lambda li: Hb[[ib[k] for k in common], fi, 0, li], np.array([rb[ib[k]]["words_" + goal] for k in common], float)),
                                ("3 short", lambda li: He[[ie[k] for k in common], 0, 0, li], np.array([re_[ie[k]]["words"] for k in common], float))):
            cells, best_talk = [], -9.0
            for li in range(len(layers)):
                X = X_of(li).astype(np.float32)
                p = cv_predict(X, y_of, groups, fo)
                cells.append(f"{r2(y_of, p):.2f} ({pearson(y_of, p):.2f})")
                m = y_of > 0
                pt = cv_predict(X[m], y_of[m], groups[m], fo)
                best_talk = max(best_talk, r2(y_of[m], pt))
            out.append(f"| {goal} | {lab} | {len(common)} | {y_of.mean():.1f} | " + " | ".join(cells) + f" | {best_talk:.2f} |")
            print(goal, lab, cells, best_talk, flush=True)
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
