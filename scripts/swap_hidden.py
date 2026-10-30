"""Hidden states of the goal-swap states (scripts/goal_swap.py) under BOTH framings, so that the length probe can be
compared on identical histories: the same game state, framed online and batch, each paired with the length of the
line that framing actually produced (the recorded line for the source framing, the re-generated one for the other).

For every state in a goal-swap output file the script builds the two prompts exactly as scripts/goal_swap.py did
(online: [system, user = transcript + label] with the generation prompt; batch: [system, user = single-batch writing
request] + transcript + label) and stores, for each, the residual stream at
  gen    the generation point (last prompt token; what scripts/probe_hidden.py used)
  label  the last token of the seat's label (the same token in both framings)
for the chosen layers.

usage: <vllm-server venv python> scripts/swap_hidden.py --log-dir log/main_gemma31b --swap log/goal_swap/gemma__multi-private.jsonl \
           --model-path <HF snapshot> --layers 20,40,48,56 --out-dir hidden/goal_swap/gemma__multi-private [--shard 0/3]
Output: <out-dir>/<shard>.npz with h [n, 2 framings, 2 positions, n_layers, H] (float16) and <shard>.json (rows).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # noqa: E402 (common.examples is imported lazily for the targeted rows)
sys.path.insert(0, str(ROOT / "scripts"))

from goal_swap import batch_requests, talk_calls  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--swap", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--layers", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--shard", default="0/1")
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
    tmpl_kw = {"enable_thinking": False} if "qwen" in a.model_path.lower() else {}
    layers = [int(x) for x in a.layers.split(",")]

    def chat_text(system, user):
        return tok.apply_chat_template([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                       tokenize=False, add_generation_prompt=True, **tmpl_kw)

    def online(system, transcript):
        text = chat_text(system, transcript)
        enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = list(enc["input_ids"]), enc["offset_mapping"]
        lab_ch = text.rfind(transcript) + len(transcript.rstrip()) - 1
        lab = next(i for i, (s, e) in enumerate(offs) if s <= lab_ch < e)
        return ids, len(ids) - 1, lab

    def batch(system, breq, transcript):
        ids = tok.encode(chat_text(system, breq), add_special_tokens=False) + tok.encode(transcript, add_special_tokens=False)
        return ids, len(ids) - 1, len(ids) - 1

    log_dir = Path(a.log_dir)
    breq = batch_requests(log_dir)
    rows = [json.loads(l) for l in Path(a.swap).read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r["game_id"].split("__")[1] in ("multi-private", "multi-private-stepped")]
    rows.sort(key=lambda r: (r["game_id"], r["seat"], r["call_seq"]))
    i, n = (int(x) for x in a.shard.split("/"))
    rows = rows[i::n]
    calls = {}
    for gid in sorted({r["game_id"] for r in rows}):
        gd = next(log_dir.glob(f"*/*/{gid}"))
        calls[gid] = {(c["seat"], c["seq"]): c for c in talk_calls(gd / "raw")}
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    H, meta = [], []
    for k, r in enumerate(rows):
        c = calls[r["game_id"]][(r["seat"], r["call_seq"])]
        system = c["messages"][0]["content"]
        if r["source"] == "multi-private":
            transcript = c["messages"][1]["content"]
            w_online, w_batch = r["words_orig"], r["words_swap"]
        else:
            transcript = c["messages"][2]["content"]
            w_online, w_batch = r["words_swap"], r["words_orig"]
        if r.get("target"):  # targeted re-generation: the one framing it used, with its examples
            if r.get("examples"):
                from common.examples import examples_block
                system = examples_block(r["setup"].rsplit("_", 1)[0], r["setup"], r["examples"]) + "\n\n---\n\n" + system
            frames = [online(system, transcript)] if r["target"] == "online" else [batch(system, breq[r["setup"]], transcript)]
            w_online = w_batch = r["words_swap"]
        else:
            frames = [online(system, transcript), batch(system, breq[r["setup"]], transcript)]
        per_frame = []
        for ids, gen, lab in frames:
            with torch.no_grad():
                out = model(torch.tensor([ids], device="cuda"), output_hidden_states=True, logits_to_keep=1)
            hs = out.hidden_states
            per_frame.append(torch.stack([torch.stack([hs[l][0, p] for l in layers]) for p in (gen, lab)]))
        H.append(torch.stack(per_frame).to(torch.float16).cpu().numpy())
        meta.append({"game_id": r["game_id"], "setup": r["setup"], "seat": r["seat"], "call_seq": r["call_seq"],
                     "round": r["round"], "turn": r["turn"], "source": r["source"],
                     "words_online": w_online, "words_batch": w_batch, "target": r.get("target"),
                     "examples": r.get("examples"), "words": r["words_swap"] if r.get("target") else None})
        if (k + 1) % 200 == 0:
            print(f"{k + 1}/{len(rows)}", flush=True)
    np.savez(out_dir / f"shard{i}.npz", h=np.stack(H))
    (out_dir / f"shard{i}.json").write_text(json.dumps({"layers": layers, "framings": ["online", "batch"],
                                                        "positions": ["gen", "label"], "rows": meta}))
    print("done", len(meta), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
