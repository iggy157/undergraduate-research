"""Judge single utterances in context (scripts/prompts/LINE_JUDGE_v2.md: the five items of ANNOTATION_INSTRUCTIONS_v2 for the last line): the recorded and re-generated lines of the
goal swap (scripts/goal_swap.py) and the lines of the steering pilots (scripts/steer_goal2.py), all with the same
protocol and blind to how the line was produced.

Each item: the seat's transcript so far (ending with its label ``- **Name**:``) + the line. The judge sees the
transcript with the line written after the label and annotates that last line.

usage: .venv/bin/python scripts/line_judge.py --log-dir log/main_gemma31b --swap log/goal_swap/gemma__multi-private.jsonl \
           [--steer log/steering_2026-10-30/pilot_gemma_s0.jsonl ...] --base-url http://localhost:8040/v1 \
           --model llama-3.3-70b --rater llama --out <jsonl> [--sample-first] [--only-sample] [--every N] [--threads 32]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from goal_swap import talk_calls  # noqa: E402

INSTR = (ROOT / "scripts" / "prompts" / "LINE_JUDGE_v2.md").read_text(encoding="utf-8")
LINE = re.compile(r"^- \*\*(.+?)\*\*: (.*)$")


def numbered(transcript: str, text: str):
    """The transcript with an id on every utterance line (as in the whole-transcript annotation), the line to judge
    appended after the label with the next id. Returns (body, target id, speaker, questions to the speaker since
    their previous line in this period: ids)."""
    lines = transcript.rstrip().split("\n")
    label = lines[-1]
    speaker = LINE.match(label + " x").group(1) if LINE.match(label + " x") else label.strip("-* :")
    out, k, period, utts = [], 0, None, []
    for ln in lines[:-1]:
        if ln.startswith("## "):
            period = ln
        m = LINE.match(ln)
        if m:
            k += 1
            out.append(f"- [{k}] **{m.group(1)}**: {m.group(2)}")
            utts.append((k, m.group(1), m.group(2), period))
        else:
            out.append(ln)
    tid = k + 1
    out.append(f"- [{tid}] **{speaker}**: " + " ".join(text.split()))
    since = []
    for uid, spk, txt, per in reversed(utts):
        if per != period or spk == speaker:
            break
        since.append((uid, spk, txt))
    qs = [uid for uid, spk, txt in since if "?" in txt and re.search(r"@(\w+)", txt) and re.search(r"@(\w+)", txt).group(1) == speaker]
    return "\n".join(out), tid, speaker, qs


def parse(text: str):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    try:
        out = {"content": min(max(int(d.get("content")), 0), 2), "resp": 1 if int(d.get("resp", 0)) else 0,
               "rebut": 1 if int(d.get("rebut", 0)) else 0, "padded": 1 if int(d.get("padded", 0)) else 0}
    except (TypeError, ValueError):
        return None
    rt = d.get("resp_to")
    try:
        out["resp_to"] = int(rt) if rt is not None else None
    except (TypeError, ValueError):
        out["resp_to"] = None
    ty = d.get("resp_type")
    out["resp_type"] = ty if ty in ("answer", "add", "object", "agree") else None
    out["note"] = str(d.get("note", ""))[:200]
    return out


def in_sample(game_id: str, call_seq: int, turn, k: int = 10) -> bool:
    """the goal_swap --per-game sample: every period's first turn + about k other calls per game."""
    if turn == 1:
        return True
    return (zlib.crc32(f"{game_id}:{call_seq}".encode()) % 100) < 20


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--swap", nargs="*", default=[])
    ap.add_argument("--steer", nargs="*", default=[])
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--rater", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--threads", type=int, default=32)
    ap.add_argument("--max-tokens", type=int, default=300)
    ap.add_argument("--only-sample", action="store_true", help="only the sampled states (turn 1 + ~20% of the rest)")
    ap.add_argument("--every", type=int, default=1, help="keep 1 in N of the (sampled) swap states (agreement subset)")
    ap.add_argument("--part", default="0/1", help="i/n: judge only the items whose key hashes to i mod n (several servers)")
    ap.add_argument("--done-from", nargs="*", default=[], help="further output files whose items count as done")
    a = ap.parse_args(argv)
    from openai import OpenAI
    client = OpenAI(base_url=a.base_url, api_key="EMPTY", timeout=600)
    log_dir = Path(a.log_dir)
    call_cache = {}

    def call_of(gid, seat, seq):
        if gid not in call_cache:
            gd = next(log_dir.glob(f"*/*/{gid}"))
            call_cache[gid] = {(c["seat"], c["seq"]): c for c in talk_calls(gd / "raw")}
        return call_cache[gid][(seat, seq)]

    items = []  # (key dict, transcript, line, priority)
    for fp in a.swap:
        for line in Path(fp).read_text().splitlines():
            r = json.loads(line)
            if r["game_id"].split("__")[1] not in ("multi-private", "multi-private-stepped"):
                continue
            samp = in_sample(r["game_id"], r["call_seq"], r.get("turn"))
            if a.only_sample and not samp:
                continue
            if a.every > 1 and zlib.crc32(f"{r['game_id']}:{r['call_seq']}:e".encode()) % a.every:
                continue
            c = call_of(r["game_id"], r["seat"], r["call_seq"])
            transcript = c["messages"][1]["content"] if r["source"] == "multi-private" else c["messages"][2]["content"]
            src_frame = "online" if r["source"] == "multi-private" else "batch"
            oth_frame = "batch" if src_frame == "online" else "online"
            base = {"kind": "swap", "game_id": r["game_id"], "seat": r["seat"], "call_seq": r["call_seq"],
                    "round": r["round"], "turn": r["turn"], "source": r["source"]}
            if r.get("target"):  # a targeted re-generation (possibly with examples): only the new line
                ex = r.get("examples")
                lab = r["target"] + (f"+ex-{ex['cond']}" if ex else "") + " (regenerated)"
                items.append(({**base, "variant": lab, "words": r["words_swap"]}, transcript, r["swap"] or "", 0 if samp else 1))
                continue
            items.append(({**base, "variant": src_frame + " (recorded)", "words": r["words_orig"]}, transcript, r["orig"] or "", 0 if samp else 1))
            items.append(({**base, "variant": oth_frame + " (swapped)", "words": r["words_swap"]}, transcript, r["swap"] or "", 0 if samp else 1))
    for fp in a.steer:
        for line in Path(fp).read_text().splitlines():
            r = json.loads(line)
            c = call_of(r["game_id"], r["seat"], r["call_seq"])
            items.append(({"kind": "steer", "game_id": r["game_id"], "seat": r["seat"], "call_seq": r["call_seq"],
                           "round": r["round"], "turn": r["turn"], "layer": r["layer"], "variant": r["variant"],
                           "words": r["words"], "broken": r.get("broken")}, c["messages"][2]["content"], r["text"] or "", 0))
    outp = Path(a.out)
    done = set()
    for fp in [outp] + [Path(x) for x in a.done_from]:
        if not fp.exists():
            continue
        for line in fp.read_text().splitlines():
            d = json.loads(line)
            done.add((d["kind"], d["game_id"], d["seat"], d["call_seq"], d["variant"], d.get("layer")))
    pi, pn = (int(x) for x in a.part.split("/"))
    if pn > 1:
        items = [it for it in items if zlib.crc32(f"{it[0]['kind']}:{it[0]['game_id']}:{it[0]['seat']}:{it[0]['call_seq']}:{it[0]['variant']}:{it[0].get('layer')}".encode()) % pn == pi]
    items = [it for it in items if (it[0]["kind"], it[0]["game_id"], it[0]["seat"], it[0]["call_seq"], it[0]["variant"], it[0].get("layer")) not in done]
    random.Random(0).shuffle(items)                 # blind order: framings and sources interleaved
    items.sort(key=lambda it: it[3])                # the sample first
    print(f"{len(items)} lines to judge ({len(done)} done)", flush=True)
    lock = threading.Lock()
    fh = outp.open("a")
    cnt = [0, 0]

    def run(it):
        key, transcript, text, _ = it
        body, tid, speaker, qs = numbered(transcript, text)
        res = None
        for attempt in range(3):
            try:
                r = client.chat.completions.create(model=a.model, temperature=0, max_tokens=a.max_tokens,
                                                   messages=[{"role": "system", "content": INSTR},
                                                             {"role": "user", "content": body}])
                res = parse(r.choices[0].message.content)
            except Exception as e:  # noqa: BLE001
                print(f"error: {type(e).__name__}: {e}", flush=True)
            if res:
                break
        with lock:
            cnt[0] += 1
            if res is None:
                cnt[1] += 1
            else:
                # named questions to this speaker since their previous line: answered iff resp_to points at one
                # (the type-independent definition of scripts/annotation_qa.py, at most one per line)
                res.update({"target_id": tid, "n_questions": len(qs), "answers_q": int(res["resp_to"] in qs) if qs else None})
                fh.write(json.dumps({**key, "rater": a.rater, **res}, ensure_ascii=False) + "\n")
                fh.flush()
            if cnt[0] % 1000 == 0:
                print(f"{cnt[0]}/{len(items)} ({cnt[1]} unparsed)", flush=True)

    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        list(ex.map(run, items))
    fh.close()
    print(f"done {cnt[0]} ({cnt[1]} unparsed)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
