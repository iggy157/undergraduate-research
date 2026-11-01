import os, json, glob
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ["CUDA_VISIBLE_DEVICES"]=""
from transformers import AutoTokenizer
SNAP=os.path.expanduser("~/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475")
tok=AutoTokenizer.from_pretrained(SNAP)
ROOT="/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
def parts(msgs): return [{"role":m["role"],"content":[{"type":"text","text":m["content"]}]} for m in msgs]
ok=bad=0
for p in sorted(glob.glob(f"{ROOT}/log/*/*/*/*.jsonl")):
    if "_pilot1" in p: continue
    for l in open(p):
        r=json.loads(l)
        if r["kind"]!="llm_call": continue
        txt=tok.apply_chat_template(parts(r["messages"]),tokenize=False,add_generation_prompt=True)
        n=len(tok(txt,add_special_tokens=False)["input_ids"])
        if n==r["usage"]["prompt_tokens"]: ok+=1
        else: bad+=1; print("MISMATCH",p,r["seq"],n,r["usage"]["prompt_tokens"])
print("parts-format: match",ok,"mismatch",bad)
# where is the extra token?
p=sorted(glob.glob(f"{ROOT}/log/aiwolf/multi/*/*.jsonl"))[0]
r=[json.loads(l) for l in open(p) if '"llm_call"' in l][1]
a=tok.apply_chat_template(r["messages"],tokenize=False,add_generation_prompt=True)
b=tok.apply_chat_template(parts(r["messages"]),tokenize=False,add_generation_prompt=True)
i=next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)
print("first diff at char",i,"string-form:",repr(a[i-30:i+10]),"parts-form:",repr(b[i-30:i+10]))
ia=tok(a,add_special_tokens=False)["input_ids"]; ib=tok(b,add_special_tokens=False)["input_ids"]
j=next(j for j,(x,y) in enumerate(zip(ia,ib)) if x!=y)
print("token diff at",j, tok.convert_ids_to_tokens(ia[j-3:j+3]), tok.convert_ids_to_tokens(ib[j-3:j+4]))
# first-token form of multi responses vs single utterances
print("multi 'The fact that' ->", tok.convert_ids_to_tokens(tok("The fact that",add_special_tokens=False)["input_ids"]))
print("multi 'Skip' ->", tok.convert_ids_to_tokens(tok("Skip",add_special_tokens=False)["input_ids"]), tok("Skip",add_special_tokens=False)["input_ids"])
print("single '**: Skip' ->", tok.convert_ids_to_tokens(tok("**: Skip\n",add_special_tokens=False)["input_ids"]), tok("**: Skip\n",add_special_tokens=False)["input_ids"])
print("single '**: The fact that' ->", tok.convert_ids_to_tokens(tok("**: The fact that",add_special_tokens=False)["input_ids"]))
print("'Acknowledged.' ->", tok.convert_ids_to_tokens(tok("Acknowledged.",add_special_tokens=False)["input_ids"]))
print("special ids: <|turn>",tok.convert_tokens_to_ids("<|turn>"),"<turn|>",tok.convert_tokens_to_ids("<turn|>"),"<|channel>",tok.convert_tokens_to_ids("<|channel>"),"<channel|>",tok.convert_tokens_to_ids("<channel|>"))
