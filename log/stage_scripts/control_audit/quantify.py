"""Rough composition of the context before an utterance: multi (last TALK call of each seat) vs single (transcript prefix)."""
import json, re, sys, glob
ROOT = "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research/log"
def calls(path):
    return [json.loads(l) for l in open(path) if '"llm_call"' in l and json.loads(l).get("kind") == "llm_call"]
for dom in ("aiwolf", "candidate_selection", "shared_living"):
    mp = glob.glob(f"{ROOT}/{dom}/multi/{dom}_0001__*/{dom}_0001__*.jsonl")[0]
    sp = glob.glob(f"{ROOT}/{dom}/single/{dom}_0001__*/{dom}_0001__*.jsonl")[0]
    mc = calls(mp); sc = calls(sp)[0]
    talks = [c for c in mc if c["request"] == "TALK"]
    last = talks[-1]
    cat = {"system": 0, "notice_frame": 0, "notice_payload": 0, "ack": 0, "name_labels": 0, "utterances": 0, "position+output_rules": 0}
    for m in last["messages"]:
        t = m["content"]
        if m["role"] == "system":
            cat["system"] += len(t); continue
        if m["role"] == "assistant":
            if t == "Acknowledged.": cat["ack"] += len(t)
            else: cat["utterances"] += len(t)
            continue
        lines = t.split("\n")
        for ln in lines:
            if ln.startswith("This is a notice.") or re.match(r"^(Day|Round) \d has (started|ended)\.$", ln) or ln == "The discussion is about to begin.":
                cat["notice_frame"] += len(ln) + 1
            elif re.match(r"^(Day|Round) \d, Turn \d of \d\.$", ln) or ln.startswith("Output only the utterance"):
                cat["position+output_rules"] += len(ln) + 1
            elif re.match(r"^[A-Z][a-z]+: ", ln) and not ln.startswith("Divine result") and not ln.startswith("Votes:"):
                name = ln.split(": ", 1)[0]; cat["name_labels"] += len(name) + 2; cat["utterances"] += len(ln) - len(name) - 2 + 1
            elif ln.strip() == "": pass
            else: cat["notice_payload"] += len(ln) + 1
    tot = sum(cat.values())
    n_utt = sum(1 for m in last["messages"] if m["role"] == "assistant" and m["content"] != "Acknowledged.")
    print(f"[{dom}] MULTI seat{last['seat']} before its last TALK (round {last['round']} turn {last['turn']}): total {tot} chars, {len(last['messages'])} msgs")
    for k, v in cat.items(): print(f"   {k:24s} {v:6d} ({100*v/tot:4.1f}%)")
    # single
    sysm = sc["messages"][0]["content"]; user = sc["messages"][1]["content"]; resp = sc["response"]
    cat2 = {"system": len(sysm), "user_prompt": len(user), "headings": 0, "name_labels": 0, "utterances": 0, "vote/action/table": 0}
    for ln in resp.split("\n"):
        if ln.startswith("#"): cat2["headings"] += len(ln) + 1
        elif ln.startswith("- **"):
            m = re.match(r"- \*\*([^*]+)\*\*: ?(.*)", ln)
            cat2["name_labels"] += len(ln) - len(m.group(2)); cat2["utterances"] += len(m.group(2)) + 1
        elif ln.strip() == "": pass
        else: cat2["vote/action/table"] += len(ln) + 1
    tot2 = sum(cat2.values())
    print(f"[{dom}] SINGLE prompt+full transcript: total {tot2} chars")
    for k, v in cat2.items(): print(f"   {k:24s} {v:6d} ({100*v/tot2:4.1f}%)")
    print(f"   single user prompt sections: identities+disclosure+format = {len(user) - user.index('Participants. Each participant')} chars; shared blocks = {user.index('Participants. Each participant')} chars")
