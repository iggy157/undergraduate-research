"""Linear probes on the pre-utterance hidden states (scripts/extract_hidden.py output): how much of the upcoming
line is decodable from the representation at the generation point, per condition (paper_draft §6).

usage: <vllm-server venv python> scripts/probe_hidden.py --log-dir log/main_gemma31b --hidden-dir hidden/main_gemma31b
           [--conditions single-batch,single-batch-stepped,single-online,multi-public,multi-private]
           [--layers 0,16,32,48,60] [--folds 5] [--out docs/main_gemma31b/probe_summary.md]

Targets at every gen_point position of a talk / pass line (one row per line the model is about to write):
  words      number of words of the line (0 for Skip / Over)
  yield      1 if the line is Skip / Over
  left_self  how many more lines this speaker writes in this period after this one
  left_game  how many more talk / pass lines follow in the whole game
  winner     (aiwolf) 1 if VILLAGE wins (game-level, constant over the game)
Ridge regression (closed form, standardised features) with grouped K-fold by setup; score = R^2 on held-out
setups (accuracy at 0.5 for the binary targets). Baseline: the same ridge on input features only (round, turn,
speaker one-hot, lines so far in the game and the period, words so far by this speaker in the period). The number
to compare across conditions is the gain of the hidden-state probe over the baseline, per layer.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.logwriter import read_log  # noqa: E402

CONDS = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "multi-private-stepped", "multi-private-stepped-process", "multi-public-stepped",
         "single-batch-process", "multi-private-process", "single-batch-stepped-process", "single-online-process",
         "multi-public-process", "multi-public-stepped-process"]


def lines_of(rows):
    """talk / pass rows in order with the targets."""
    tp = [r for r in rows if r.type in ("talk", "pass")]
    winner = next((r.text for r in rows if r.type == "result"), None)
    out = []
    n = len(tp)
    for i, r in enumerate(tp):
        words = int((r.extra or {}).get("words") or 0) if r.type == "talk" else 0
        left_self = sum(1 for q in tp[i + 1:] if q.round == r.round and q.agent == r.agent)
        so_far_game = i
        so_far_period = sum(1 for q in tp[:i] if q.round == r.round)
        words_self_period = sum(int((q.extra or {}).get("words") or 0) for q in tp[:i] if q.round == r.round and q.agent == r.agent and q.type == "talk")
        out.append({"agent": r.agent, "round": r.round, "turn": r.turn, "words": words, "yield": int(r.type == "pass"),
                    "left_self": left_self, "left_game": n - i - 1, "winner": None if winner is None else int(winner == "VILLAGE"),
                    "so_far_game": so_far_game, "so_far_period": so_far_period, "words_self_period": words_self_period})
    return out


def match_positions(index: dict, lines: list[dict], cond: str):
    """pair gen_point positions with lines; returns list of (position index in h, line)."""
    pos = [(k, p) for k, p in enumerate(index["positions"]) if p["gen_point"]]
    pairs = []
    if cond in ("single-batch", "single-batch-stepped"):
        labels = [(k, p) for k, p in pos if p["label"].startswith("- **")]
        if len(labels) != len(lines):
            return None
        for (k, p), ln in zip(labels, lines):
            if p["label"] != f"- **{ln['agent']}**:":
                return None
            pairs.append((k, ln))
    else:
        by_key = {(ln["round"], ln["turn"], ln["agent"]): ln for ln in lines}
        for k, p in pos:
            if p.get("request") != "TALK":
                continue
            name = p["label"][4:-3] if p["label"].startswith("- **") else None
            ln = by_key.get((p["round"], p["turn"], name))
            if ln is not None:
                pairs.append((k, ln))
    return pairs


LAMS = [1.0, 10.0, 100.0, 1e3, 1e4, 1e5]


_DEV = None


def _torch():
    global _DEV
    import torch
    if _DEV is None:
        _DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch


def _fit_predict(Xtr, ytr, Xte, lams):
    """Standardise on the training rows; ridge for every lambda from one eigendecomposition of the n x n Gram matrix
    (dual form). Runs on the GPU when one is visible. Returns one prediction vector per lambda."""
    torch = _torch()
    Xtr_t = torch.as_tensor(Xtr, dtype=torch.float64, device=_DEV)
    Xte_t = torch.as_tensor(Xte, dtype=torch.float64, device=_DEV)
    y_t = torch.as_tensor(ytr, dtype=torch.float64, device=_DEV)
    mu, sd = Xtr_t.mean(0), Xtr_t.std(0, unbiased=False) + 1e-6
    Xtr_t, Xte_t = (Xtr_t - mu) / sd, (Xte_t - mu) / sd
    ym = y_t.mean()
    yc = y_t - ym
    K = Xtr_t @ Xtr_t.T
    evals, evecs = torch.linalg.eigh(K)
    proj = evecs.T @ yc
    Kte = Xte_t @ Xtr_t.T
    out = []
    for lam in lams:
        a = evecs @ (proj / (evals + lam))
        out.append((Kte @ a + ym).cpu().numpy())
    return out


def ridge_cv(X, y, groups, folds, lam=None, binary=False):
    """Grouped K-fold; the ridge penalty is chosen inside each training fold by an inner grouped 3-fold split
    (nested CV) from LAMS, unless ``lam`` is given."""
    uniq = sorted(set(groups))
    rng = np.random.RandomState(0)
    rng.shuffle(uniq)
    fold_of = {g: i % folds for i, g in enumerate(uniq)}
    f = np.array([fold_of[g] for g in groups])
    pred = np.zeros_like(y, dtype=np.float64)
    for k in range(folds):
        tr, te = f != k, f == k
        if lam is not None:
            pred[te] = _fit_predict(X[tr], y[tr], X[te], [lam])[0]
            continue
        gtr = groups[tr]
        inner = {g: i % 3 for i, g in enumerate(sorted(set(gtr)))}
        fi = np.array([inner[g] for g in gtr])
        err = np.zeros(len(LAMS))
        Xk, yk = X[tr], y[tr]
        for j in range(3):
            a, b = fi != j, fi == j
            for li, p in enumerate(_fit_predict(Xk[a], yk[a], Xk[b], LAMS)):
                err[li] += ((yk[b] - p) ** 2).sum()
        pred[te] = _fit_predict(X[tr], y[tr], X[te], [LAMS[int(err.argmin())]])[0]
    if binary:
        return float(((pred > 0.5) == (y > 0.5)).mean())
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - pred) ** 2).sum() / ss) if ss > 0 else float("nan")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", default="log/main_gemma31b")
    ap.add_argument("--hidden-dir", default="hidden/main_gemma31b")
    ap.add_argument("--conditions", default=",".join(CONDS))
    ap.add_argument("--layers", default="0,16,32,48,60")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--lam", type=float, default=10.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    hdir = Path(a.hidden_dir)
    if a.layers == "auto":  # 5 evenly spaced layers among those stored
        stored = json.loads(next(hdir.glob("*.index.json")).read_text())["layers"]
        layers = sorted({stored[round(i * (len(stored) - 1) / 4)] for i in range(5)})
    else:
        layers = [int(x) for x in a.layers.split(",")]
    out = [f"# Linear probes on pre-utterance hidden states ({a.hidden_dir}; ridge, penalty chosen by nested grouped CV from {LAMS}, {a.folds}-fold by setup)\n"]
    names = ["words", "yield", "left_self", "left_game", "winner"]
    for cond in a.conditions.split(","):
        feats = {l: [] for l in layers}
        base, targets, groups, dom = [], defaultdict(list), [], []
        n_games = n_skipped = 0
        for idx_fp in sorted(hdir.glob(f"*__{cond}__*.index.json")):
            index = json.loads(idx_fp.read_text())
            gid = index["game_id"]
            gd = next(Path(a.log_dir).glob(f"*/*/{gid}"), None)
            if gd is None or not (idx_fp.with_suffix("").with_suffix(".npz")).exists():
                continue
            rows = list(read_log(gd / f"{gid}.log"))
            lines = lines_of(rows)
            pairs = match_positions(index, lines, cond)
            if not pairs:
                n_skipped += 1
                continue
            h = np.load(idx_fp.with_suffix("").with_suffix(".npz"))["h"]  # [n_pos, n_layers, H]
            lsel = {l: index["layers"].index(l) for l in layers}
            agents = sorted({ln["agent"] for ln in lines})
            setup = gid.split("__")[0]
            for k, ln in pairs:
                for l in layers:
                    feats[l].append(h[k, lsel[l]].astype(np.float32))
                onehot = [float(ln["agent"] == x) for x in agents] + [0.0] * (5 - len(agents))
                base.append([ln["round"] or 0, ln["turn"] or 0, ln["so_far_game"], ln["so_far_period"], ln["words_self_period"]] + onehot)
                for t in names:
                    targets[t].append(ln[t] if ln[t] is not None else np.nan)
                groups.append(setup)
                dom.append(setup.rsplit("_", 1)[0])
            n_games += 1
        if not groups:
            out.append(f"## {cond}: no data\n")
            continue
        B = np.array(base, dtype=np.float64)
        groups = np.array(groups)
        out.append(f"## {cond}: {n_games} games ({n_skipped} unmatched), {len(groups)} lines\n")
        out.append("| target | baseline (input features) | " + " | ".join(f"layer {l}" for l in layers) + " |")
        out.append("|---|---|" + "---|" * len(layers))
        for t in names:
            y = np.array(targets[t], dtype=np.float64)
            m = ~np.isnan(y)
            if m.sum() < 50 or np.nanstd(y[m]) == 0:
                continue
            binary = t in ("yield", "winner")
            b = ridge_cv(B[m], y[m], groups[m], a.folds, binary=binary)
            row = [f"{b:.3f}"]
            for l in layers:
                X = np.stack(feats[l])[m]
                row.append(f"{ridge_cv(X, y[m], groups[m], a.folds, binary=binary):.3f}")
            out.append(f"| {t}{' (acc)' if binary else ' (R2)'} | " + " | ".join(row) + " |")
        out.append("")
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
