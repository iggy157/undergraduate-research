"""Goal swap on identical histories: re-generate a seat's next line from the very same game state with only the
generation goal changed (paper: the generation-goal hypothesis, DESIGN §15).

A multi-online seat (multi-private) and a multi-batch seat (multi-private-stepped) see the same text at a talk
turn: ``build_talk_message(view.render(), name)`` (the transcript so far + the seat's label). They differ only in
how it is framed:
  online : [system = participant prompt, user = transcript + label]            -> chat completion
  batch  : [system = participant prompt, user = the single-batch writing request] + transcript + label as the
           assistant's own output                                              -> continuation (/v1/completions)
For every recorded talk call of the source condition this script builds the other framing from the same record
(the batch request of a setup is taken from any recorded multi-batch call of that setup) and generates the line
again, greedy, with the seat's stop strings. The recorded line is the reference for the source framing.

usage: .venv/bin/python scripts/goal_swap.py --log-dir log/main_gemma31b --source multi-private \
           --models default_c,default_d,default_e,default_f --out <jsonl> [--pin-by-setup] [--limit-games N]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import zlib
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


STOP = ["\n- **", "\n####", "\n###", "\n##"]
PASS = {"skip", "over", "[skip]", "[over]"}


def words(text: str | None) -> int:
    t = (text or "").strip()
    if t.rstrip(".").lower() in PASS:
        return 0
    return len(t.split())


def talk_calls(raw_dir: Path):
    for fp in sorted(raw_dir.glob("agent.*.jsonl")):
        for line in fp.read_text().splitlines():
            r = json.loads(line)
            if r.get("kind") == "llm_call" and r.get("request") == "TALK" and not r.get("error"):
                yield r


def batch_requests(log_dir: Path) -> dict[str, str]:
    out = {}
    for gd in sorted(log_dir.glob("*/multi-private-stepped/*/")):
        setup = gd.name.split("__")[0]
        if setup in out:
            continue
        for r in talk_calls(gd / "raw"):
            if r.get("continuation"):
                out[setup] = r["messages"][1]["content"]
                break
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--source", choices=["multi-private", "multi-private-stepped"], required=True)
    ap.add_argument("--models", required=True, help="comma-separated model config names (one per server)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pin-by-setup", action="store_true", help="the same server for every call of a setup")
    ap.add_argument("--threads-per-model", type=int, default=8)
    ap.add_argument("--limit-games", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--target", choices=["other", "online", "batch"], default="other",
                    help="framing to re-generate in (other = the framing the source did not use)")
    ap.add_argument("--examples", default=None,
                    help='JSON like {"src": "log/main_gemma31b", "cond": "single-batch", "n": 3}: discussion examples '
                         '(common/examples.py) put before the system prompt of the re-generated call')
    ap.add_argument("--per-game", type=int, default=0,
                    help="sample: the first talk call of every period (turn 1, every seat) + this many other calls at random")
    a = ap.parse_args(argv)
    log_dir = Path(a.log_dir)
    ex_cfg = json.loads(a.examples) if a.examples else None
    breq = batch_requests(log_dir)
    from agent.base.llm import OpenAILLM, load_model_config  # imported here: the steering script reuses the helpers
    clients = [OpenAILLM(load_model_config(m)) for m in a.models.split(",")]
    setups = sorted({p.name.split("__")[0] for p in log_dir.glob(f"*/{a.source}/*/")})
    pin = {s: i % len(clients) for i, s in enumerate(setups)}
    done = set()
    outp = Path(a.out)
    if outp.exists():
        for line in outp.read_text().splitlines():
            r = json.loads(line)
            done.add((r["game_id"], r["seat"], r["call_seq"]))
    jobs = []
    for n, gd in enumerate(sorted(log_dir.glob(f"*/{a.source}/*/"))):
        if a.limit_games and n >= a.limit_games:
            break
        setup = gd.name.split("__")[0]
        if setup not in breq or gd.name.split("__")[1] != a.source:  # plan conditions share the folder: skip them
            continue
        calls = list(talk_calls(gd / "raw"))
        if a.per_game:
            first = [r for r in calls if r.get("turn") == 1]
            rest = [r for r in calls if r.get("turn") != 1]
            rng = random.Random(zlib.crc32(gd.name.encode()))
            calls = first + rng.sample(rest, min(a.per_game, len(rest)))
        for r in calls:
            if (gd.name, r["seat"], r["seq"]) not in done:
                jobs.append((gd.name, setup, r))
    print(f"{len(jobs)} calls to re-generate ({len(done)} already done)", flush=True)
    lock = threading.Lock()
    fh = outp.open("a")
    counter = [0]

    def run(job, ci):
        gid, setup, r = job
        system, user = r["messages"][0]["content"], r["messages"][1]["content"]
        cl = clients[ci]
        transcript = user if a.source == "multi-private" else r["messages"][2]["content"]
        target = a.target if a.target != "other" else ("batch" if a.source == "multi-private" else "online")
        if ex_cfg is not None:
            from common.examples import examples_block
            system = examples_block(setup.rsplit("_", 1)[0], setup, ex_cfg) + "\n\n---\n\n" + system
        if target == "batch":
            text, meta = cl.complete_continuation([{"role": "system", "content": system}, {"role": "user", "content": breq[setup]}],
                                                  transcript, a.max_tokens, stop=STOP)
        else:
            text, meta = cl.complete([{"role": "system", "content": system}, {"role": "user", "content": transcript}],
                                     a.max_tokens, stop=STOP)
        rec = {"game_id": gid, "setup": setup, "seat": r["seat"], "call_seq": r["seq"], "round": r["round"], "turn": r["turn"],
               "source": a.source, "target": target, "examples": ex_cfg, "orig": r.get("response"), "swap": text, "words_orig": words(r.get("response")),
               "words_swap": words(text), "finish_swap": meta.get("finish_reason"),
               "prompt_tokens_swap": (meta.get("usage") or {}).get("prompt_tokens")}
        with lock:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            counter[0] += 1
            if counter[0] % 200 == 0:
                print(f"{counter[0]}/{len(jobs)}", flush=True)

    by_client = [[] for _ in clients]
    for i, job in enumerate(jobs):
        ci = pin[job[1]] if a.pin_by_setup else i % len(clients)
        by_client[ci].append(job)
    with ThreadPoolExecutor(max_workers=len(clients) * a.threads_per_model) as ex:
        # interleave the servers so that every server gets work from the start
        futs = [ex.submit(run, by_client[ci][k], ci) for k in range(max(map(len, by_client)))
                for ci in range(len(by_client)) if k < len(by_client[ci])]
        for f in futs:
            f.result()
    fh.close()
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
