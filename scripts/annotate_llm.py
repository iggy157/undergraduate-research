"""Utterance-level annotation (ANNOTATION_INSTRUCTIONS.md) with a locally served LLM judge (vLLM, OpenAI API).

usage: .venv/bin/python scripts/annotate_llm.py --annot-dir <dir with games/ and ANNOTATION_INSTRUCTIONS.md>
           --base-url http://localhost:8040/v1 --model llama-3.3-70b --rater llama [--games game_001.md,...]
           [--temperature 0] [--max-tokens 8192] [--chat-template-kwargs '{"enable_thinking": false}']

One request per game: system = the instruction file, user = the transcript + a reminder of the output format.
The reply is parsed as a JSON list (code fences tolerated); utterances missing from the reply are reported and
left out. Output: out/<rater>__<game stem>.json per game ({game: [items]}) plus raw/<rater>__<game stem>.txt with the model's
full reply, so that scripts/annotation_summary.py can aggregate. (Earlier versions numbered the files by the position in
the game list, which shifts when games are added; names are now stable.)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from openai import OpenAI

FLAGS = ["resp", "rebut", "empty", "ignore", "misattr", "reversal", "padded"]  # 0/1 fields (v1 and v2)
V2_EXTRA = ["content", "resp_to", "resp_type"]  # v2 fields kept as given


def parse_reply(text: str) -> list[dict]:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", t, re.S)
    if m:
        t = m.group(1)
    else:
        i, j = t.find("["), t.rfind("]")
        if i >= 0 and j > i:
            t = t[i:j + 1]
    return json.loads(t)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annot-dir", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--rater", required=True, help="name used in out/<rater>_<game>.json")
    ap.add_argument("--games", default=None, help="comma list of game files; default all in games/")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--chat-template-kwargs", default=None, help="JSON passed as extra_body.chat_template_kwargs")
    ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--reparse", action="store_true", help="re-parse the saved raw/ replies instead of calling the model")
    a = ap.parse_args(argv)
    d = Path(a.annot_dir)
    instructions = (d / "ANNOTATION_INSTRUCTIONS.md").read_text(encoding="utf-8")
    all_games = sorted(p.name for p in (d / "games").glob("*.md"))
    games = a.games.split(",") if a.games else all_games
    index = {g: g[:-3] if g.endswith(".md") else g for g in all_games}  # output name = <rater>__<game file stem>.json (stable across runs)
    (d / "out").mkdir(exist_ok=True)
    (d / "raw").mkdir(exist_ok=True)
    client = None if a.reparse else OpenAI(base_url=a.base_url, api_key=a.api_key, timeout=1800, max_retries=1)
    extra = {}
    if a.chat_template_kwargs:
        extra["chat_template_kwargs"] = json.loads(a.chat_template_kwargs)
    n_ok = 0
    for g in games:
        if not a.reparse and (d / "out" / f"{a.rater}__{index[g]}.json").exists():
            n_ok += 1
            continue  # already annotated (the runs over a growing set of games are restarted as games complete)
        text = (d / "games" / g).read_text(encoding="utf-8")
        seqs = [int(m.group(1)) for m in re.finditer(r"^- \[(\d+)\] \*\*", text, re.M)]
        user = (f"Annotate every utterance of the transcript below ({len(seqs)} utterances, ids "
                f"{seqs[0]}..{seqs[-1]}). Output only the JSON list, one object per utterance in order.\n\n" + text)
        t0 = time.time()
        raw_fp = d / "raw" / f"{a.rater}__{index[g]}.txt"
        if a.reparse:
            if not raw_fp.exists():
                print(f"{g}: no raw reply", file=sys.stderr)
                continue
            reply, finish = raw_fp.read_text(encoding="utf-8"), "reparse"
        else:
          try:
            r = client.chat.completions.create(model=a.model, temperature=a.temperature, max_tokens=a.max_tokens,
                                               messages=[{"role": "system", "content": instructions},
                                                         {"role": "user", "content": user}],
                                               extra_body=extra or None)
            reply = r.choices[0].message.content or ""
            finish = r.choices[0].finish_reason
          except Exception as e:  # noqa: BLE001
            print(f"{g}: request failed: {e}", file=sys.stderr)
            continue
          raw_fp.write_text(reply, encoding="utf-8")
        try:
            items = parse_reply(reply)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"{g}: unparsable reply ({finish}): {e}", file=sys.stderr)
            continue
        by_seq = {}
        for it in items:
            try:
                s = int(it["seq"])
            except (KeyError, ValueError, TypeError):
                continue
            by_seq[s] = {"seq": s, "speaker": it.get("speaker", ""),
                         **{f: int(bool(it.get(f, 0))) for f in FLAGS if f in it},
                         **{f: it.get(f) for f in V2_EXTRA if f in it},
                         "note": str(it.get("note", ""))[:200]}
        out = [by_seq[s] for s in seqs if s in by_seq]
        missing = [s for s in seqs if s not in by_seq]
        (d / "out" / f"{a.rater}__{index[g]}.json").write_text(json.dumps({g: out}, ensure_ascii=False, indent=1) + "\n",
                                                               encoding="utf-8")
        n_ok += 1
        print(f"{g}: {len(out)}/{len(seqs)} utterances, missing {missing[:5]}{'...' if len(missing) > 5 else ''}, "
              f"finish={finish}, {time.time() - t0:.0f}s")
    print(f"{n_ok}/{len(games)} games annotated -> {d / 'out'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
