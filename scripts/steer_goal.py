"""Steering test of the generation-goal direction (contrastive activation addition, Rimsky et al. 2024 / Turner et
al. 2023), on identical game states.

For a recorded multi-online talk call (multi-private) the same state can be framed two ways (scripts/goal_swap.py):
  online : [system, user = transcript + label]                           (the recorded call)
  batch  : [system, user = single-batch writing request] + transcript + label as the assistant's own output
1. Direction: on the states of the TRAINING setups, the residual stream at the generation point (the last prompt
   token) of layer L, batch minus online, averaged: v_L.
2. Test, on the states of the HELD-OUT setups: generate the line (greedy, the seat's stop strings) from
     online + alpha * v_L   for alpha in --alphas   (added at the last prompt position and every generated position)
     online + a random direction of the same norm  (control, alpha 1)
     batch (no steering)                            (the goal swap itself, as reference)
   and record words and the text.

usage: <vllm-server venv python> scripts/steer_goal.py --log-dir log/main_gemma31b --model-path <HF snapshot> \
           --layer 40 --out <jsonl> [--train-setups 60] [--states-per-setup 6] [--test-states-per-setup 5] \
           [--alphas 0,1,2] [--shard 0/1]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from goal_swap import STOP, batch_requests, talk_calls, words  # noqa: E402


def decoder_layers(model):
    import torch.nn as nn
    best = None
    for _, mod in model.named_modules():
        if isinstance(mod, nn.ModuleList) and len(mod) > 8 and "DecoderLayer" in type(mod[0]).__name__:
            if best is None or len(mod) > len(best):
                best = mod
    if best is None:
        raise RuntimeError("no decoder layer list found")
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--layer", type=int, required=True, help="hidden_states index (0 = embeddings): the output of block layer-1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--train-setups", type=int, default=60)
    ap.add_argument("--states-per-setup", type=int, default=6)
    ap.add_argument("--test-states-per-setup", type=int, default=5)
    ap.add_argument("--alphas", default="0,1,2")
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--shard", default="0/1", help="i/n: this process runs test states i, i+n, ...")
    ap.add_argument("--vector", default=None, help="load v from this .npy (else compute and save next to --out)")
    a = ap.parse_args(argv)
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    import numpy as np
    import torch
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model_path)
    from transformers import AutoModelForCausalLM
    try:
        model = AutoModelForCausalLM.from_pretrained(a.model_path, dtype=torch.bfloat16)
    except ValueError:
        from transformers import AutoModelForImageTextToText
        model = AutoModelForImageTextToText.from_pretrained(a.model_path, dtype=torch.bfloat16)
    model.to("cuda").eval()
    blocks = decoder_layers(model)
    qwen = "qwen" in a.model_path.lower()
    tmpl_kw = {"enable_thinking": False} if qwen else {}

    def ids_online(system, user):
        return tok.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                       tokenize=True, add_generation_prompt=True, **tmpl_kw)

    def ids_batch(system, breq, transcript):
        p = tok.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": breq}],
                                    tokenize=True, add_generation_prompt=True, **tmpl_kw)
        return list(p) + tok.encode(transcript, add_special_tokens=False)

    def as_list(x):
        return list(x["input_ids"]) if isinstance(x, dict) or hasattr(x, "keys") else list(x)

    log_dir = Path(a.log_dir)
    breq = batch_requests(log_dir)
    games = sorted(log_dir.glob("*/multi-private/*/"))
    setups = sorted({g.name.split("__")[0] for g in games if g.name.split("__")[0] in breq})
    rng = random.Random(0)
    order = setups[:]
    rng.shuffle(order)
    train, test = set(order[:a.train_setups]), [s for s in order[a.train_setups:]]
    states = {}
    for g in games:
        s = g.name.split("__")[0]
        if s not in breq:
            continue
        calls = [r for r in talk_calls(g / "raw")]
        rng2 = random.Random(zlib.crc32(g.name.encode()))
        k = a.states_per_setup if s in train else a.test_states_per_setup
        states[s] = [(g.name, r) for r in rng2.sample(calls, min(k, len(calls)))]

    def resid_at_last(ids, L):
        with torch.no_grad():
            out = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, logits_to_keep=1)
        return out.hidden_states[L][0, -1].float()

    vec_path = Path(a.vector) if a.vector else Path(a.out).with_suffix(f".v{a.layer}.npy")
    if not vec_path.exists() and not a.shard.startswith("0/"):
        while not vec_path.exists():  # shard 0 computes the direction; the others wait for it
            time.sleep(20)
        time.sleep(5)
    if vec_path.exists():
        v = torch.tensor(np.load(vec_path), device="cuda")
    else:
        diffs = []
        for s in sorted(train):
            for gid, r in states[s]:
                system, user = r["messages"][0]["content"], r["messages"][1]["content"]
                hb = resid_at_last(as_list(ids_batch(system, breq[s], user)), a.layer)
                ho = resid_at_last(as_list(ids_online(system, user)), a.layer)
                diffs.append((hb - ho).cpu())
        v = torch.stack(diffs).mean(0).to("cuda")
        np.save(vec_path, v.cpu().numpy())
        print(f"direction from {len(diffs)} paired states, |v| = {v.norm():.1f}", flush=True)
    g = torch.Generator(device="cpu").manual_seed(1)
    rnd = torch.randn(v.shape, generator=g).to("cuda")
    rnd = rnd / rnd.norm() * v.norm()

    state = {"vec": None, "start": None}

    def hook(_mod, _inp, out):
        if state["vec"] is None:
            return out
        hs = out[0] if isinstance(out, tuple) else out
        if hs.shape[1] > 1:   # prefill: from the last prompt position on
            hs[:, state["start"]:, :] += state["vec"].to(hs.dtype)
        else:
            hs += state["vec"].to(hs.dtype)
        return out

    handle = blocks[a.layer - 1].register_forward_hook(hook)

    def generate(ids, vec):
        state["vec"], state["start"] = vec, len(ids) - 1
        with torch.no_grad():
            out = model.generate(torch.tensor([ids], device="cuda"), max_new_tokens=a.max_new_tokens, do_sample=False,
                                 stop_strings=STOP, tokenizer=tok, pad_token_id=tok.pad_token_id or tok.eos_token_id)
        state["vec"] = None
        text = tok.decode(out[0, len(ids):], skip_special_tokens=True)
        for s in STOP:
            text = text.split(s)[0]
        return text, int(out.shape[1] - len(ids))

    alphas = [float(x) for x in a.alphas.split(",")]
    tests = [(s, gid, r) for s in test for gid, r in states[s]]
    i, n = (int(x) for x in a.shard.split("/"))
    tests = tests[i::n]
    outp = Path(a.out)
    done = set()
    if outp.exists():
        for line in outp.read_text().splitlines():
            rr = json.loads(line)
            done.add((rr["game_id"], rr["call_seq"], rr["variant"]))
    fh = outp.open("a")
    for k, (s, gid, r) in enumerate(tests):
        system, user = r["messages"][0]["content"], r["messages"][1]["content"]
        on = as_list(ids_online(system, user))
        variants = [(f"online+{al:g}v", on, (al * v) if al else None) for al in alphas]
        variants += [("online+rand", on, rnd), ("batch", as_list(ids_batch(system, breq[s], user)), None)]
        for name, ids, vec in variants:
            if (gid, r["seq"], name) in done:
                continue
            text, ntok = generate(ids, vec)
            fh.write(json.dumps({"game_id": gid, "setup": s, "seat": r["seat"], "call_seq": r["seq"], "round": r["round"],
                                 "turn": r["turn"], "layer": a.layer, "variant": name, "text": text, "words": words(text),
                                 "new_tokens": ntok, "recorded": r.get("response"),
                                 "words_recorded": words(r.get("response"))}, ensure_ascii=False) + "\n")
            fh.flush()
        print(f"{k + 1}/{len(tests)}", flush=True)
    handle.remove()
    fh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
