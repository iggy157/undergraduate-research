"""Second round of probes on the pre-utterance hidden states (scripts/extract_hidden.py output), for the
generation-goal story: the 2x2 core (writer x goal) plus the format-matched single pair.

usage: <vllm-server venv python> scripts/probe_hidden2.py --log-dir log/main_qwen38 --hidden-dir hidden/main_qwen38 \
           --annot-dir <annotation dir with games.json, games/, out/> --out docs/main_qwen38/probe_summary_v3.md

Targets at the generation point of every talk / pass line (one row per line the model is about to write):
  words       words of the line (0 for Skip / Over)                                  R^2 and Pearson r
  content     number of new contributions in the line (LLM annotation, 0-2)          R^2 and Pearson r
  has_content 1 if the line has at least one new contribution                        AUC
  answers     only lines that are the addressee's next line after an "@Name ...?" question in the same period:
              1 if the line responds to that question (annotation resp_to)            AUC
Every target is also fitted on input features only (round, turn, speaker one-hot, lines so far in the game and the
period, words so far by this speaker in the period): the baseline.
Ridge (standardised on the training rows), grouped 5-fold by setup, penalty chosen by an inner grouped 3-fold split.

Sections of the output:
  A  best layer per condition and target (hidden vs baseline)
  B  the whole layer curve for words (every stored layer)
  C  transfer of the words probe between conditions: fit on condition A (training setups), apply to condition B
     (held-out setups); Pearson r, which does not depend on the scale of the predictions
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from common.logwriter import read_log  # noqa: E402
from probe_hidden import LAMS, _fit_predict, lines_of, match_positions  # noqa: E402

CORE = ["single-batch", "single-batch-stepped", "single-online", "multi-private-stepped", "multi-private"]
SHORT = {"single-batch": "single-batch", "single-batch-stepped": "single-batch-stepped", "single-online": "single-online",
         "multi-private-stepped": "multi-batch", "multi-private": "multi-online"}
TARGETS = ["words", "content", "has_content", "answers"]
BINARY = {"has_content", "answers"}


def load_annotations(annot_dir: Path, rater: str):
    """(setup, condition) -> {(round, turn, speaker): {"content": c, "answers": 0/1 or None}}."""
    games = json.loads((annot_dir / "games.json").read_text())
    out = {}
    for g, info in games.items():
        fp = annot_dir / "out" / f"{rater}__{g[:-3]}.json"
        if not fp.exists():
            continue
        items = list(json.loads(fp.read_text()).values())[0]
        an = {int(i["seq"]): i for i in items if str(i.get("seq", "")).isdigit()}
        rows, period = {}, None
        for line in (annot_dir / "games" / g).read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                period = line[3:]
            m = re.match(r"- \[(\d+)\] \*\*(.+?)\*\*: (.*)", line)
            if m:
                rows[int(m.group(1))] = (m.group(2), m.group(3), period)
        answers = {}
        for seq, (spk, text, per) in rows.items():
            if "?" not in text:
                continue
            m = re.search(r"@(\w+)", text)
            if not m:
                continue
            nxt = next((s2 for s2 in sorted(rows) if s2 > seq and rows[s2][2] == per and rows[s2][0] == m.group(1)), None)
            if nxt is not None and nxt not in answers:
                answers[nxt] = int((an.get(nxt) or {}).get("resp_to") == seq)
        d = {}
        for seq, (spk, _, _) in rows.items():
            rt = info["turn"].get(str(seq))
            if not rt or seq not in an:
                continue
            c = an[seq].get("content")
            d[(rt[0], rt[1], spk)] = {"content": None if c is None else min(int(c), 2), "answers": answers.get(seq)}
        out[(info["setup_id"], info["condition"])] = d
    return out


def load_condition(log_dir: Path, hdir: Path, cond: str, ann):
    feats, base, groups, tg = defaultdict(list), [], [], defaultdict(list)
    layers = None
    for idx_fp in sorted(hdir.glob(f"*__{cond}__*.index.json")):
        index = json.loads(idx_fp.read_text())
        gid = index["game_id"]
        gd = next(log_dir.glob(f"*/*/{gid}"), None)
        npz = idx_fp.with_suffix("").with_suffix(".npz")
        if gd is None or not npz.exists():
            continue
        lines = lines_of(list(read_log(gd / f"{gid}.log")))
        pairs = match_positions(index, lines, cond)
        if not pairs:
            continue
        setup = gid.split("__")[0]
        a = ann.get((setup, cond), {})
        h = np.load(npz)["h"]
        layers = index["layers"]
        agents = sorted({ln["agent"] for ln in lines})
        for k, ln in pairs:
            for li in range(len(layers)):
                feats[li].append(h[k, li].astype(np.float32))
            onehot = [float(ln["agent"] == x) for x in agents] + [0.0] * (5 - len(agents))
            base.append([ln["round"] or 0, ln["turn"] or 0, ln["so_far_game"], ln["so_far_period"], ln["words_self_period"]] + onehot)
            groups.append(setup)
            an = a.get((ln["round"], ln["turn"], ln["agent"]), {})
            c = an.get("content")
            is_talk = ln["words"] > 0
            tg["words"].append(ln["words"])
            tg["content"].append(np.nan if (c is None or not is_talk) else c)
            tg["has_content"].append(np.nan if (c is None or not is_talk) else float(c > 0))
            ans = an.get("answers")
            tg["answers"].append(np.nan if (ans is None or not is_talk) else float(ans))
    X = {li: np.stack(v) for li, v in feats.items()}
    return {"X": X, "B": np.array(base, dtype=np.float64), "g": np.array(groups),
            "t": {k: np.array(v, dtype=np.float64) for k, v in tg.items()}, "layers": layers}


def folds_of(groups, k=5):
    uniq = sorted(set(groups))
    rng = np.random.RandomState(0)
    rng.shuffle(uniq)
    return {g: i % k for i, g in enumerate(uniq)}


def cv_predict(X, y, groups, fold_of, k=5):
    f = np.array([fold_of[g] for g in groups])
    pred = np.zeros_like(y)
    for j in range(k):
        tr, te = f != j, f == j
        if te.sum() == 0 or tr.sum() == 0:
            continue
        lam = choose_lam(X[tr], y[tr], groups[tr])
        pred[te] = _fit_predict(X[tr], y[tr], X[te], [lam])[0]
    return pred


def choose_lam(X, y, groups):
    inner = {g: i % 3 for i, g in enumerate(sorted(set(groups)))}
    fi = np.array([inner[g] for g in groups])
    err = np.zeros(len(LAMS))
    for j in range(3):
        a, b = fi != j, fi == j
        for li, p in enumerate(_fit_predict(X[a], y[a], X[b], LAMS)):
            err[li] += ((y[b] - p) ** 2).sum()
    return LAMS[int(err.argmin())]


def r2(y, p):
    ss = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - p) ** 2).sum() / ss) if ss > 0 else float("nan")


def pearson(y, p):
    return float(np.corrcoef(y, p)[0, 1]) if y.std() > 0 and p.std() > 0 else float("nan")


def auc(y, p):
    pos, neg = p[y > 0.5], p[y <= 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def score(t, y, p):
    return (auc(y, p), None) if t in BINARY else (r2(y, p), pearson(y, p))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--hidden-dir", required=True)
    ap.add_argument("--annot-dir", required=True)
    ap.add_argument("--rater", default="llama")
    ap.add_argument("--conditions", default=",".join(CORE))
    ap.add_argument("--out", default=None)
    ap.add_argument("--talk-only", action="store_true", help="drop Skip / Over lines (words = 0) from every target")
    ap.add_argument("--targets", default=",".join(TARGETS))
    ap.add_argument("--no-transfer", action="store_true")
    a = ap.parse_args(argv)
    log_dir, hdir = Path(a.log_dir), Path(a.hidden_dir)
    ann = load_annotations(Path(a.annot_dir), a.rater)
    conds = a.conditions.split(",")
    data = {c: load_condition(log_dir, hdir, c, ann) for c in conds}
    if a.talk_only:  # keep only the rows of talk lines
        for c, d in data.items():
            keep = d["t"]["words"] > 0
            d["X"] = {li: x[keep] for li, x in d["X"].items()}
            d["B"], d["g"] = d["B"][keep], d["g"][keep]
            d["t"] = {k: v[keep] for k, v in d["t"].items()}
    out = [f"# Probes v3 ({a.hidden_dir}; annotations {a.annot_dir}, rater {a.rater})\n",
           "Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. "
           "`base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.\n"]
    # ---- A: best layer per target
    out.append("## A. Best layer per condition and target\n")
    out.append("| condition | lines | target | n | base | hidden (best layer) | layer | gain |")
    out.append("|---|---|---|---|---|---|---|---|")
    curves = {}
    for c in conds:
        d = data[c]
        fo = folds_of(d["g"])
        for t in a.targets.split(","):
            y = d["t"][t]
            m = ~np.isnan(y)
            if m.sum() < 100 or np.nanstd(y[m]) == 0:
                out.append(f"| {SHORT[c]} | {len(y)} | {t} | {int(m.sum())} | – | – | – | – |")
                continue
            sb = score(t, y[m], cv_predict(d["B"][m], y[m], d["g"][m], fo))[0]
            per = []
            for li, layer in enumerate(d["layers"]):
                per.append(score(t, y[m], cv_predict(d["X"][li][m], y[m], d["g"][m], fo)))
            if t == "words":
                curves[c] = per
            best = int(np.nanargmax([s[0] for s in per]))
            bs, br = per[best]
            extra = f" (r {br:.2f})" if br is not None else ""
            out.append(f"| {SHORT[c]} | {len(y)} | {t} | {int(m.sum())} | {sb:.3f} | {bs:.3f}{extra} | {d['layers'][best]} | {bs - sb:+.3f} |")
            print(c, t, f"base {sb:.3f} best {bs:.3f} @ {d['layers'][best]}", flush=True)
    # ---- B: layer curves
    out.append("\n## B. Layer curve, words (R^2)\n")
    layers = data[conds[0]]["layers"]
    out.append("| condition | " + " | ".join(str(l) for l in layers) + " |")
    out.append("|---|" + "---|" * len(layers))
    for c in conds:
        if c in curves:
            out.append(f"| {SHORT[c]} | " + " | ".join(f"{s[0]:.2f}" for s in curves[c]) + " |")
    # ---- C: transfer of the words probe (at each condition's best words layer of the source)
    if a.no_transfer:
        conds_tr = []
    else:
        conds_tr = conds
    out.append("\n## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)\n")
    out.append("| fitted on \\ applied to | " + " | ".join(SHORT[c] for c in conds) + " |")
    out.append("|---|" + "---|" * len(conds))
    for src in conds_tr:
        if src not in curves:
            continue
        li = int(np.nanargmax([s[0] for s in curves[src]]))
        ds = data[src]
        fo = folds_of(np.concatenate([data[c]["g"] for c in conds]))
        row = []
        for dst in conds:
            dd = data[dst]
            fs = np.array([fo[g] for g in ds["g"]])
            fd = np.array([fo[g] for g in dd["g"]])
            ys, yd = ds["t"]["words"], dd["t"]["words"]
            pred = np.zeros_like(yd)
            for j in range(5):
                tr, te = fs != j, fd == j
                if te.sum() == 0:
                    continue
                lam = choose_lam(ds["X"][li][tr], ys[tr], ds["g"][tr])
                pred[te] = _fit_predict(ds["X"][li][tr], ys[tr], dd["X"][li][te], [lam])[0]
            row.append(f"{pearson(yd, pred):.2f}")
        out.append(f"| {SHORT[src]} (layer {ds['layers'][li]}) | " + " | ".join(row) + " |")
        print("transfer", src, row, flush=True)
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
