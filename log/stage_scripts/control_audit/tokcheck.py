"""CPU-only check: can the logged `messages` reproduce vLLM's prompt token count?

- Renders the chat template of the snapshot vLLM served (842da379...) with transformers'
  apply_chat_template and counts tokens; compares with usage.prompt_tokens of every llm_call.
- Also renders the older template blob (e61bbfe9...) to see whether the two differ for our messages.
- Re-tokenizes the response text and compares with usage.completion_tokens.
- For single: finds the token offsets of each '- **Name**: ' line start inside the response.
"""
import glob
import json
import os
import sys
from collections import Counter

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from transformers import AutoTokenizer  # noqa: E402

ROOT = "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
SNAP = os.path.expanduser("~/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475")
OLD_TPL = os.path.expanduser("~/.cache/huggingface/hub/models--google--gemma-4-31B-it/blobs/e61bbfe9a31db79ea1e4e557b046f895ad7899d0")

tok = AutoTokenizer.from_pretrained(SNAP)
print("tokenizer class:", type(tok).__name__, "vocab", len(tok), "bos", tok.bos_token, tok.bos_token_id,
      "eos", tok.eos_token, tok.eos_token_id, file=sys.stderr)
old_tpl = open(OLD_TPL, encoding="utf-8").read()

GEN_SUFFIX = "<|turn>model\n<|channel>thought\n<channel|>"


def render(messages, template=None, add_gen=True):
    kw = {"tokenize": False, "add_generation_prompt": add_gen}
    if template is not None:
        kw["chat_template"] = template
    return tok.apply_chat_template(messages, **kw)


summary = Counter()
details = []
for p in sorted(glob.glob(f"{ROOT}/log/*/*/*/*.jsonl")):
    if "_pilot1" in p:
        continue
    recs = [json.loads(l) for l in open(p, encoding="utf-8")]
    calls = [r for r in recs if r["kind"] == "llm_call"]
    gid = os.path.basename(p)[:-6]
    for c in calls:
        txt = render(c["messages"])
        old = render(c["messages"], old_tpl)
        ids = tok(txt, add_special_tokens=False)["input_ids"]
        n_prompt = len(ids)
        logged = c["usage"]["prompt_tokens"] if c.get("usage") else None
        same_tpl = (txt == old)
        assert txt.endswith(GEN_SUFFIX), txt[-80:]
        resp = c["response"] or ""
        rid = tok(resp, add_special_tokens=False)["input_ids"]
        # the model emits the content then <turn|> (eos 106): completion_tokens usually = len(content)+1
        n_comp_logged = c["usage"]["completion_tokens"] if c.get("usage") else None
        key = (c["request"],)
        summary[("prompt_match" if n_prompt == logged else "prompt_mismatch", c["request"])] += 1
        summary[("tpl_same" if same_tpl else "tpl_differs", c["request"])] += 1
        summary[("comp+1" if len(rid) + 1 == n_comp_logged else ("comp=" if len(rid) == n_comp_logged else "comp_other"), c["request"])] += 1
        details.append((gid, c["seq"], c["request"], c["seat"], logged, n_prompt, n_comp_logged, len(rid), same_tpl))
        # round-trip of the response: does detok(tok(resp)) == resp ?
        rt = tok.decode(rid)
        summary[("resp_roundtrip_ok" if rt == resp else "resp_roundtrip_differs", c["request"])] += 1
        if c["request"] == "FULL":
            # alignment points: token index of each utterance line's content start
            lines = []
            for ln in resp.split("\n"):
                lines.append(ln)
            # compute offsets using offset mapping
            enc = tok(resp, add_special_tokens=False, return_offsets_mapping=True)
            offs = enc["offset_mapping"]
            import re
            pts = []
            for m in re.finditer(r"^- \*\*([^*]+)\*\*: ", resp, flags=re.M):
                char = m.end()
                # token whose span starts at/after char
                ti = next((i for i, (a, b) in enumerate(offs) if a >= char), None)
                prev_tok = tok.convert_ids_to_tokens(enc["input_ids"][ti - 1]) if ti else None
                this_tok = tok.convert_ids_to_tokens(enc["input_ids"][ti]) if ti is not None else None
                clean = offs[ti][0] == char if ti is not None else False
                pts.append((m.group(1), char, ti, clean, prev_tok, this_tok))
            print(f"\n[{gid}] FULL: prompt logged={logged} rendered={n_prompt}; completion logged={n_comp_logged} retok={len(rid)}")
            print("  first 12 utterance alignment points (name, char, tok_idx, boundary_clean, prev_tok, this_tok):")
            for x in pts[:12]:
                print("   ", x)
            n_clean = sum(1 for x in pts if x[3])
            print(f"  alignment points: {len(pts)}, clean token boundary: {n_clean}")
            # show how '- **Minako**: ' tokenizes
            sample = "\n- **Minako**: Hello"
            print("  sample tokens:", tok.convert_ids_to_tokens(tok(sample, add_special_tokens=False)["input_ids"]))

print("\n=== summary ===")
for k in sorted(summary):
    print(k, summary[k])
print("\n=== mismatches (gid, seq, request, seat, logged_prompt, rendered_prompt, logged_comp, retok_comp, tpl_same) ===")
for d in details:
    if d[4] != d[5] or d[6] not in (d[7], d[7] + 1):
        print(d)

# Example rendered prompt (multi, one TALK call) for the report
p = sorted(glob.glob(f"{ROOT}/log/aiwolf/multi/*/*.jsonl"))[0]
recs = [json.loads(l) for l in open(p, encoding="utf-8")]
c = [r for r in recs if r["kind"] == "llm_call" and r["request"] == "TALK"][1]
txt = render(c["messages"])
print("\n=== rendered multi TALK prompt (head 700 chars / tail 400 chars) ===")
print(txt[:700])
print("....")
print(txt[-400:])
ids = tok(txt, add_special_tokens=False)["input_ids"]
print("last 12 tokens:", tok.convert_ids_to_tokens(ids[-12:]))
# single
p = sorted(glob.glob(f"{ROOT}/log/aiwolf/single/*/*.jsonl"))[0]
recs = [json.loads(l) for l in open(p, encoding="utf-8")]
c = [r for r in recs if r["kind"] == "llm_call"][0]
txt = render(c["messages"])
print("\n=== rendered single prompt (head 300 / tail 300) ===")
print(txt[:300]); print("...."); print(txt[-300:])
