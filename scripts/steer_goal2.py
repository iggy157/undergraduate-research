"""Steering test of the generation-goal direction, version 2 (contrastive activation addition, Rimsky et al. 2024).

Version 1 (scripts/steer_goal.py) took the difference at the last prompt token, which is a different token in the two
framings (the script label ``:`` vs the chat generation header): the direction was mostly a token-identity
difference and broke the generation. Here the contrast is taken at the SAME token in both framings, and on the
states where the goal swap moves the length most (scripts/goal_swap.py: a multi-batch state re-framed online gets
about 11 words longer).

States: recorded talk calls of multi-batch games (multi-private-stepped, no plan), framed two ways:
  batch  : [system, user = single-batch writing request] + transcript + label as the assistant's own output
  online : [system, user = transcript + label]       (the label is the end of the user message)
Contrast position: the last token of the label ``- **Name**:`` in both (the colon).
1. Direction: mean over the TRAINING setups of h_L(batch, label) - h_L(online, label).
2. Test, on the HELD-OUT setups, online framing with alpha * v added from the label position on (the label token,
   the end-of-turn and generation-header tokens, every generated token); alpha in --alphas; a random direction of
   the same norm as v (alpha 1) as control; the batch framing without steering as the reference.
Each line is also checked for broken text (glued words, repetition).

usage: <vllm-server venv python> scripts/steer_goal2.py --log-dir log/main_gemma31b --model-path <HF snapshot> \
           --layer 40 --out <jsonl> [--train-setups 60] [--states-per-setup 4] [--test-states-per-setup 4] \
           [--alphas=0,0.5,1,1.5] [--shard 0/2] [--limit-tests N]
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

from goal_swap import STOP, talk_calls, words  # noqa: E402
from steer_goal import decoder_layers  # noqa: E402


def broken(text: str) -> dict:
    ws = text.split()
    if not ws:
        return {"glued": 0.0, "rep": 0.0, "nonalpha": 0.0}
    glued = sum(len(w) > 18 for w in ws) / len(ws)
    top = max(ws.count(w) for w in set(ws)) / len(ws)
    letters = sum(c.isalpha() or c.isspace() for c in text) / max(len(text), 1)
    return {"glued": round(glued, 3), "rep": round(top, 3), "nonalpha": round(1 - letters, 3)}


def is_broken(b: dict, n_words: int) -> bool:
    return b["glued"] > 0.1 or (n_words >= 8 and b["rep"] > 0.3) or b["nonalpha"] > 0.35


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--train-setups", type=int, default=60)
    ap.add_argument("--states-per-setup", type=int, default=4)
    ap.add_argument("--test-states-per-setup", type=int, default=4)
    ap.add_argument("--alphas", default="0,0.5,1,1.5")
    ap.add_argument("--max-new-tokens", type=int, default=128)
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--limit-tests", type=int, default=0, help="pilot: only the first N test states (after sharding)")
    ap.add_argument("--vector", default=None)
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
    tmpl_kw = {"enable_thinking": False} if "qwen" in a.model_path.lower() else {}

    def chat_text(system, user):
        return tok.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                       tokenize=False, add_generation_prompt=True, **tmpl_kw)

    def framing_batch(system, breq, transcript):
        ids = tok.encode(chat_text(system, breq), add_special_tokens=False) + tok.encode(transcript, add_special_tokens=False)
        return ids, len(ids) - 1

    def framing_online(system, transcript):
        text = chat_text(system, transcript)
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = list(enc["input_ids"]), enc["offset_mapping"]
        lab_ch = text.rfind(transcript) + len(transcript.rstrip()) - 1  # the label's colon
        pos = next(i for i, (s, e) in enumerate(offs) if s <= lab_ch < e)
        return ids, pos

    log_dir = Path(a.log_dir)
    games = [g for g in sorted(log_dir.glob("*/multi-private-stepped/*/")) if g.name.split("__")[1] == "multi-private-stepped"]
    setups = sorted({g.name.split("__")[0] for g in games})
    rng = random.Random(0)
    order = setups[:]
    rng.shuffle(order)
    train, test = set(order[:a.train_setups]), order[a.train_setups:]
    states = {}
    for g in games:
        s = g.name.split("__")[0]
        calls = [r for r in talk_calls(g / "raw") if r.get("continuation") and len(r["messages"]) == 3]
        r2 = random.Random(zlib.crc32(g.name.encode()))
        k = a.states_per_setup if s in train else a.test_states_per_setup
        states[s] = [(g.name, r) for r in r2.sample(calls, min(k, len(calls)))]

    def h_at(ids, pos, L):
        with torch.no_grad():
            out = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, logits_to_keep=1)
        return out.hidden_states[L][0, pos].float()

    vec_path = Path(a.vector) if a.vector else Path(a.out).with_suffix(f".v{a.layer}.npy")
    if not vec_path.exists() and not a.shard.startswith("0/"):
        while not vec_path.exists():
            time.sleep(20)
        time.sleep(5)
    if vec_path.exists():
        v = torch.tensor(np.load(vec_path), device="cuda")
    else:
        diffs, norms = [], []
        for s in sorted(train):
            for gid, r in states[s]:
                system, breq, transcript = (m["content"] for m in r["messages"])
                ib, pb = framing_batch(system, breq, transcript)
                io, po = framing_online(system, transcript)
                hb, ho = h_at(ib, pb, a.layer), h_at(io, po, a.layer)
                diffs.append((hb - ho).cpu())
                norms.append(float(ho.norm()))
        v = torch.stack(diffs).mean(0).to("cuda")
        np.save(vec_path, v.cpu().numpy())
        print(f"direction from {len(diffs)} paired states at the label token, |v| = {v.norm():.1f}, "
              f"mean |h_online| = {sum(norms) / len(norms):.1f}", flush=True)
    g = torch.Generator(device="cpu").manual_seed(1)
    rnd = torch.randn(v.shape, generator=g).to("cuda")
    rnd = rnd / rnd.norm() * v.norm()

    state = {"vec": None, "start": None}

    def hook(_mod, _inp, out):
        if state["vec"] is None:
            return out
        hs = out[0] if isinstance(out, tuple) else out
        if hs.shape[1] > 1:
            hs[:, state["start"]:, :] += state["vec"].to(hs.dtype)
        else:
            hs += state["vec"].to(hs.dtype)
        return out

    handle = blocks[a.layer - 1].register_forward_hook(hook)

    def generate(ids, start, vec):
        state["vec"], state["start"] = vec, start
        x = torch.tensor([ids], device="cuda")
        with torch.no_grad():
            out = model.generate(x, attention_mask=torch.ones_like(x), max_new_tokens=a.max_new_tokens, do_sample=False,
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
    if a.limit_tests:
        tests = tests[:a.limit_tests]
    outp = Path(a.out)
    done = set()
    if outp.exists():
        for line in outp.read_text().splitlines():
            rr = json.loads(line)
            done.add((rr["game_id"], rr["call_seq"], rr["variant"]))
    fh = outp.open("a")
    for k, (s, gid, r) in enumerate(tests):
        system, breq, transcript = (m["content"] for m in r["messages"])
        io, po = framing_online(system, transcript)
        ib, pb = framing_batch(system, breq, transcript)
        variants = [(f"online+{al:g}v", io, po, (al * v) if al else None) for al in alphas]
        variants += [("online+rand", io, po, rnd), ("batch", ib, pb, None)]
        for name, ids, start, vec in variants:
            if (gid, r["seq"], name) in done:
                continue
            text, ntok = generate(ids, start, vec)
            nw = words(text)
            b = broken(text)
            fh.write(json.dumps({"game_id": gid, "setup": s, "seat": r["seat"], "call_seq": r["seq"], "round": r["round"],
                                 "turn": r["turn"], "layer": a.layer, "variant": name, "text": text, "words": nw,
                                 "new_tokens": ntok, "broken": is_broken(b, nw), **b, "recorded": r.get("response"),
                                 "words_recorded": words(r.get("response"))}, ensure_ascii=False) + "\n")
            fh.flush()
        print(f"{k + 1}/{len(tests)}", flush=True)
    handle.remove()
    fh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
