"""Hidden states at the "about to write this line" positions of logged games (DESIGN §14, paper_draft §5).

usage: <vllm-server venv python> scripts/extract_hidden.py --game-dir log/<domain>/<condition>/<game_id> [...]
           --model-path <HF snapshot dir> --out-dir hidden [--layers 0,4,8,...|all] [--dtype bfloat16] [--check-only]

For every llm_call of a game the prompt is rebuilt exactly as the server saw it (the same chat template as
vLLM: ``add_generation_prompt`` for a request, ``continue_final_message`` for single-batch-stepped) and, for the
single-batch call, the recorded transcript is appended as the assistant message (teacher forcing). One forward
pass per sequence with ``output_hidden_states`` gives, at the positions of interest, the residual-stream vectors
of the selected layers:

  kind "label"  : the last token of the label ``- **Name**:`` / ``- Name ->`` / ``- divine: Name ->`` (the token from
                  which the first token of the line is predicted in single-batch and single-batch-stepped)
  kind "prompt" : the last token of the prompt (the generation-prompt marker) in single-online / multi-*
  gen_point     : True for the position from which the line's first token is predicted (label in batch / stepped,
                  prompt in the request conditions). Cross-condition comparisons use gen_point positions; the label
                  token of a request condition predicts the end-of-turn marker, not the utterance (audit 2026-10-28 D)

Runs from 2026-10-28 on record ``prompt_token_ids`` (vLLM /tokenize at generation time) and the generated token ids,
so the sequence is rebuilt from the record without re-templating (vLLM's rendering differs from the HF template by a
space token in the system message). Older logs fall back to the HF chat template, with the checks: for single-batch
the appended transcript retokenises to the recorded token ids (minus the final end-of-turn); for the server
pipeline the rebuilt prompt has ``usage.prompt_tokens`` tokens.

Output: ``<out-dir>/<game_id>.npz`` with ``h`` [n_pos, n_layers, hidden] (float16) and ``index.json``
(positions: seq, seat, request, round, turn, kind, token position, checks; layers; model path; dtype).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_LABEL_RE = re.compile(r"\n(- \*\*[^*\n]+\*\*:|- [^\n]+? ->|- (?:divine|attack|investigate): [^\n]+? ->)(?= |\n|$)")


def read_jsonl(p: Path) -> list[dict]:
    with open(p, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f if ln.strip()]


def token_ids_of(tokens: list[dict]) -> list[int]:
    return [int(t["token"].split(":")[-1]) for t in tokens]


def label_end_offsets(text: str) -> list[tuple[int, str]]:
    """(char offset in ``text`` of the label's last char, label) for every transcript label in ``text``.
    The regex runs on "\n" + text so that a label on the first line matches; the offsets are shifted back."""
    return [(m.end(1) - 2, m.group(1)) for m in _LABEL_RE.finditer("\n" + text)]


def build_sequence(tok, call: dict, header: dict) -> tuple[list[int], list[dict], dict]:
    """Token ids of the whole sequence and the positions of interest [{kind, pos, label}].

    The prompt is always the chat template *with the generation prompt* (that is what vLLM fed: for Gemma 4 with
    thinking off it ends with an empty thought channel). single-batch: prompt + the recorded response (teacher
    forcing). single-batch-stepped: prompt + the recorded assistant prefix (what the completions call was fed).
    Others: the prompt alone (the request's user message ends with the label)."""
    msgs = [dict(m) for m in call["messages"]]
    chat = msgs[:2] if msgs and msgs[-1]["role"] == "assistant" else msgs
    pipeline = header.get("pipeline") or ("batch" if header.get("method") == "single" and call.get("request") == "FULL" else "server")
    rec_prompt = call.get("prompt_token_ids")
    if rec_prompt:  # the ids vLLM saw (recorded at generation time): no re-templating needed
        rec_prompt = [int(x) for x in rec_prompt]
        if pipeline == "batch":
            resp = token_ids_of(call.get("tokens") or [])
            ids = rec_prompt + resp
            pieces = [tok.decode([i]) for i in resp]
            text = "".join(pieces)
            starts = []
            c = 0
            for pc in pieces:
                starts.append(c)
                c += len(pc)
            positions = []
            for off, label in label_end_offsets(text):
                pos = max(i for i, st in enumerate(starts) if st <= off)
                positions.append({"kind": "label", "pos": len(rec_prompt) + pos, "label": label.strip()})
            return ids, positions, {"n_prompt": len(rec_prompt), "kind": "batch", "recorded": True}
        label = msgs[-1]["content"].rsplit("\n", 1)[-1]
        kind = "stepped" if msgs[-1]["role"] == "assistant" else "request"
        positions = [{"kind": "label" if kind == "stepped" else "prompt", "pos": len(rec_prompt) - 1, "label": label}]
        if kind == "request":  # the label token = last token of the user text (before the end-of-turn marker)
            tail = [tok.decode([i]) for i in rec_prompt[-12:]]
            k = next((len(tail) - 1 - i for i, pc in enumerate(reversed(tail)) if pc.rstrip().endswith((":", "->"))), None)
            if k is not None:
                positions.append({"kind": "label", "pos": len(rec_prompt) - len(tail) + k, "label": label})
        return rec_prompt, positions, {"n_prompt": len(rec_prompt), "kind": kind, "recorded": True}
    prompt = tok.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
    n_prompt = len(tok.encode(prompt, add_special_tokens=False))
    if pipeline == "batch":
        text = call["response"] or ""
        full = prompt + text
        ids = tok.encode(full, add_special_tokens=False)
        offsets = tok(full, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        positions = []
        for off, label in label_end_offsets(text):
            ch = len(prompt) + off
            pos = next((i for i, (a, b) in enumerate(offsets) if a <= ch < b), None)
            if pos is not None:
                positions.append({"kind": "label", "pos": pos, "label": label.strip()})
        return ids, positions, {"n_prompt": n_prompt, "kind": "batch"}
    if msgs and msgs[-1]["role"] == "assistant":  # stepped: prompt ids + prefix ids (special-token boundary)
        prefix = msgs[-1]["content"]
        ids = tok.encode(prompt, add_special_tokens=False) + tok.encode(prefix, add_special_tokens=False)
        label = prefix.rsplit("\n", 1)[-1]
        return ids, [{"kind": "label", "pos": len(ids) - 1, "label": label}], {"n_prompt": len(ids), "kind": "stepped"}
    ids = tok.encode(prompt, add_special_tokens=False)
    label = msgs[-1]["content"].rsplit("\n", 1)[-1]
    positions = [{"kind": "prompt", "pos": len(ids) - 1, "label": label}]
    # the label token: the last token of the user message text (before the end-of-turn marker)
    offsets = tok(prompt, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
    lab_ch = prompt.rfind(label) + len(label) - 1 if label else -1
    lab_pos = next((i for i, (a, b) in enumerate(offsets) if a <= lab_ch < b), None) if lab_ch >= 0 else None
    if lab_pos is not None:
        positions.append({"kind": "label", "pos": lab_pos, "label": label})
    return ids, positions, {"n_prompt": n_prompt, "kind": "request"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game-dir", nargs="+", required=True)
    ap.add_argument("--model-path", required=True, help="HF snapshot directory of the generation model")
    ap.add_argument("--out-dir", default="hidden")
    ap.add_argument("--layers", default="every4", help="'all', 'every4', or a comma list of layer indices (0 = embeddings)")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--max-len", type=int, default=32768)
    ap.add_argument("--check-only", action="store_true", help="rebuild the sequences and run the checks, no model")
    a = ap.parse_args(argv)

    import os
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")  # long sequences: avoid fragmentation OOM
    import torch
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model_path)
    model = None
    if not a.check_only:
        from transformers import AutoModelForCausalLM
        dtype = getattr(torch, a.dtype)
        model = AutoModelForCausalLM.from_pretrained(a.model_path, dtype=dtype)  # no accelerate: plain .to(device)
        model.to(a.device)
        model.eval()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for gd in a.game_dir:
        gd = Path(gd)
        recs = read_jsonl(gd / f"{gd.name}.jsonl")
        header = recs[0]
        calls = [r for r in recs if r.get("kind") == "llm_call"]
        index = {"game_id": header.get("game_id", gd.name), "condition": header.get("condition"), "model_path": a.model_path,
                 "dtype": a.dtype, "layers": None, "positions": []}
        feats: list[np.ndarray] = []
        for call in calls:
            ids, positions, checks = build_sequence(tok, call, header)
            ok = {}
            if checks.get("recorded"):
                pt = (call.get("usage") or {}).get("prompt_tokens")
                ok["prompt_token_count_match"] = (pt is None) or (pt == checks["n_prompt"])
            elif checks["kind"] == "batch":
                rec_ids = token_ids_of(call.get("tokens") or [])
                resp_ids = ids[checks["n_prompt"]:]
                ok["response_tokens_match"] = bool(rec_ids) and (resp_ids == rec_ids or resp_ids == rec_ids[:-1])
            elif checks["kind"] == "stepped":
                n = (call.get("prompt_ids") or 0) + (call.get("prefix_ids") or 0)
                ok["prompt_token_count_match"] = (not n) or (n == len(ids))
            else:
                pt = (call.get("usage") or {}).get("prompt_tokens")
                ok["prompt_token_count_match"] = (pt is None) or (pt == checks["n_prompt"])
            if not all(ok.values()):
                rc = 1
            if model is not None and len(ids) <= a.max_len:
                outp = None
                for attempt in range(2):
                    try:
                        with torch.no_grad():
                            x = torch.tensor([ids], device=a.device)
                            try:  # logits for the last position only: the full [T, vocab] logits of a 20k-token
                                outp = model(x, output_hidden_states=True, logits_to_keep=1)  # sequence are >10 GB
                            except TypeError:
                                outp = model(x, output_hidden_states=True)
                        break
                    except torch.OutOfMemoryError:
                        outp = None
                        torch.cuda.empty_cache()
                if outp is None:  # skipped: recorded, no positions of this call go into h / positions
                    index.setdefault("skipped_calls", []).append({"seq": call.get("seq"), "n_tokens": len(ids), "reason": "oom"})
                    print(f"{gd.name}: call seq {call.get('seq')} skipped (OOM, {len(ids)} tokens)", file=sys.stderr)
                    continue
                hs = outp.hidden_states  # tuple(n_layers+1) of [1, T, H]
                if index["layers"] is None:
                    n = len(hs)
                    if a.layers == "all":
                        sel = list(range(n))
                    elif a.layers == "every4":
                        sel = sorted(set(list(range(0, n, 4)) + [n - 1]))
                    else:
                        sel = [int(x) for x in a.layers.split(",")]
                    index["layers"] = sel
                for p in positions:
                    vec = torch.stack([hs[l][0, p["pos"]] for l in index["layers"]]).to(torch.float16).cpu().numpy()
                    feats.append(vec)
                del outp, hs
                if len(ids) > 12000:
                    torch.cuda.empty_cache()
            for p in positions:
                # the generation point = the position from which the first token of the line is predicted: the label
                # token in batch / stepped, the prompt end (after the generation prompt) in the request conditions
                gen_point = (p["kind"] == "label") if checks["kind"] in ("batch", "stepped") else (p["kind"] == "prompt")
                index["positions"].append({"seq": call.get("seq"), "seat": call.get("seat"), "request": call.get("request"),
                                           "round": call.get("round"), "turn": call.get("turn"), **p, "gen_point": gen_point,
                                           "n_tokens": len(ids), "checks": ok})
        if feats:
            np.savez_compressed(out_dir / f"{index['game_id']}.npz", h=np.stack(feats))
        (out_dir / f"{index['game_id']}.index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
        bad = sum(1 for p in index["positions"] if not all(p["checks"].values()))
        print(f"{index['game_id']}: {len(index['positions'])} positions, {len(calls)} calls, checks failed: {bad}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
