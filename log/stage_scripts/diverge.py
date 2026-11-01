import sys, glob, json
sys.path.insert(0, "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research")
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/3548789868c5356dbf307c98e6f609007b82b3eb/")
LOG="log/_pilot5"
def ids(toks): return [int(t["token"].split(":")[-1]) for t in toks]
for dom in ["aiwolf","candidate_selection","shared_living"]:
    for n in ["0001","0002","0003"]:
        setup=f"{dom}_{n}"
        bf=[f for f in glob.glob(f"{LOG}/{dom}/single-batch/{setup}__single-batch__*/*.jsonl") if "/raw/" not in f][0]
        sf=[f for f in glob.glob(f"{LOG}/{dom}/single-batch-stepped/{setup}__*/*.jsonl") if "/raw/" not in f][0]
        b=[json.loads(l) for l in open(bf)]; s=[json.loads(l) for l in open(sf)]
        bcall=[r for r in b if r.get("kind")=="llm_call"][0]
        scalls=[r for r in s if r.get("kind")=="llm_call"]
        bids=ids(bcall["tokens"]); blp=[t["logprob"] for t in bcall["tokens"]]
        # prompt identity
        same_prompt = bcall["prompt_token_ids"]==scalls[0]["prompt_token_ids"]
        # walk stepped calls: each call's assistant prefix tokens should be a prefix of batch prompt+response
        bresp_text = tok.decode(bids)
        first=None
        for c in scalls:
            pre = c["messages"][-1]["content"]
            # tokens of prefix as sent: prefix_ids count
            cids=ids(c["tokens"]); clp=[t["logprob"] for t in c["tokens"]]
            # locate prefix text in batch response
            if not bresp_text.startswith(pre):
                # find where prefix diverges from batch text
                k=next((i for i,(x,y) in enumerate(zip(pre,bresp_text)) if x!=y), min(len(pre),len(bresp_text)))
                print(f"{setup}: prompt_same={same_prompt} PREFIX diverges at char {k} before call seq={c['seq']} {c['request']} r{c['round']}t{c['turn']}: batch ...{bresp_text[max(0,k-60):k+60]!r} | stepped ...{pre[max(0,k-60):k+60]!r}")
                break
            # compare generated tokens with batch continuation tokens at that offset
            off = len(tok.encode(pre, add_special_tokens=False))
            # safer: find token index whose decoded prefix equals pre
            acc=""; idx=None
            for i,t in enumerate(bids):
                if acc==pre: idx=i; break
                acc+=tok.decode([t])
            if idx is None and acc==pre: idx=len(bids)
            if idx is None:
                print(f"{setup}: cannot align prefix at seq={c['seq']} (token boundary); off={off}"); 
                idx=off
            bseg=bids[idx:idx+len(cids)]; bseglp=blp[idx:idx+len(cids)]
            j=next((i for i,(x,y) in enumerate(zip(cids,bseg)) if x!=y), None)
            if j is not None:
                print(f"{setup}: prompt_same={same_prompt} first token divergence in call seq={c['seq']} {c['request']} r{c['round']}t{c['turn']} tok#{j}: batch {tok.decode([bseg[j]])!r} lp={bseglp[j]:.3f} | stepped {tok.decode([cids[j]])!r} lp={clp[j]:.3f} ; context {tok.decode(cids[:j])!r}")
                print(f"   batch line: {tok.decode(bseg)!r}\n   stepped   : {c['response']!r}")
                break
        else:
            print(f"{setup}: no token divergence in any call (prompt_same={same_prompt})")
