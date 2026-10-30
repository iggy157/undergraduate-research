"""Length probe on identical histories (scripts/swap_hidden.py output): for the same game states framed online and
batch, how well does the pre-generation hidden state predict the length of the line that framing produced?

Rows = states of both swap directions (short histories from multi-batch games, long histories from multi-online
games). For each framing, position (gen = last prompt token, label = the label's colon, the same token in both) and
layer: ridge, grouped 5-fold by setup with a nested penalty choice (scripts/probe_hidden2.py). R^2 and Pearson r.
Also split by history (the source condition of the state).

usage: <vllm-server venv python> scripts/swap_probe.py --hidden-root hidden/goal_swap --model gemma --out <md>
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


def load(root: Path, model: str):
    H, rows, layers = [], [], None
    for src in ("multi-private", "multi-private-stepped"):
        d = root / f"{model}__{src}"
        for js in sorted(d.glob("shard*.json")):
            meta = json.loads(js.read_text())
            layers = meta["layers"]
            H.append(np.load(js.with_suffix(".npz"))["h"])
            rows += meta["rows"]
    return np.concatenate(H), rows, layers


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hidden-root", default="hidden/goal_swap")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    H, rows, layers = load(Path(a.hidden_root), a.model)
    groups = np.array([r["setup"] for r in rows])
    hist = np.array(["short (multi-batch game)" if r["source"] == "multi-private-stepped" else "long (multi-online game)" for r in rows])
    y = {"online": np.array([r["words_online"] for r in rows], float), "batch": np.array([r["words_batch"] for r in rows], float)}
    base = np.array([[r["round"] or 0, r["turn"] or 0] for r in rows], float)
    fo = folds_of(groups)
    out = [f"# Length probe on identical histories: {a.model} ({len(rows)} states)\n",
           "Each state is the same game state under both framings; y = words of the line that framing produced "
           "(recorded or re-generated, scripts/goal_swap.py). Ridge, grouped 5-fold by setup, nested penalty. "
           "`base` = round and turn only. R^2 (r).\n"]
    out.append("## All states\n")
    out.append("| framing | mean words | sd | base | " + " | ".join(f"gen L{l}" for l in layers) + " | " + " | ".join(f"label L{l}" for l in layers) + " |")
    out.append("|---|---|---|---|" + "---|" * (2 * len(layers)))
    preds = {}
    for fi, fr in enumerate(("online", "batch")):
        yy = y[fr]
        cells = []
        for pi in range(2):
            for li in range(len(layers)):
                p = cv_predict(H[:, fi, pi, li].astype(np.float32), yy, groups, fo)
                preds[(fr, pi, li)] = p
                cells.append(f"{r2(yy, p):.2f} ({pearson(yy, p):.2f})")
        b = cv_predict(base, yy, groups, fo)
        out.append(f"| {fr} | {yy.mean():.1f} | {yy.std():.1f} | {r2(yy, b):.2f} | " + " | ".join(cells) + " |")
        print(fr, cells, flush=True)
    out.append("\n## By history (same predictions, scored within each subset; best layer of each position)\n")
    out.append("| history | framing | n | mean words | sd | gen: best R^2 (r) | label: best R^2 (r) |")
    out.append("|---|---|---|---|---|---|---|")
    for hname in sorted(set(hist)):
        m = hist == hname
        for fr in ("online", "batch"):
            yy = y[fr][m]
            best = []
            for pi in range(2):
                sc = [(r2(yy, preds[(fr, pi, li)][m]), pearson(yy, preds[(fr, pi, li)][m]), layers[li]) for li in range(len(layers))]
                s = max(sc, key=lambda t: t[0])
                best.append(f"{s[0]:.2f} ({s[1]:.2f}) L{s[2]}")
            out.append(f"| {hname} | {fr} | {int(m.sum())} | {yy.mean():.1f} | {yy.std():.1f} | {best[0]} | {best[1]} |")
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
