import json, sys, pathlib
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
calls = [json.loads(l) for l in open(sys.argv[1]) if '"llm_call"' in l]
calls = [c for c in calls if c.get("kind") == "llm_call"]
print("n calls", len(calls), "keys", sorted(calls[0].keys()))
def fmt(c):
    s = [f"### call seq={c.get('seq')} request={c.get('request')} seat={c.get('seat')} agent={c.get('agent')} round={c.get('round')} turn={c.get('turn')} finish={c.get('finish_reason')} params={ {k:c.get(k) for k in ('temperature','max_tokens','top_p','model') } }"]
    for m in c["messages"]:
        s.append(f"--- [{m['role']}]\n{m['content']}")
    s.append(f"--- [RESPONSE]\n{c.get('response')}")
    return "\n".join(s)
if len(calls) == 1:
    (out / "single_FULL.txt").write_text(fmt(calls[0]))
    return_ = None
else:
    # per agent: first TALK, first TALK that contains a notice (Round/Day N has started after the first), vote, action
    by_agent = {}
    for c in calls:
        by_agent.setdefault(c.get("agent") or c.get("seat"), []).append(c)
    for ag, cs in by_agent.items():
        talks = [c for c in cs if c["request"] == "TALK"]
        picks = {"first_TALK": talks[0], "last_TALK": talks[-1]}
        for c in cs:
            if c["request"] != "TALK":
                picks.setdefault(c["request"], c)
        for k, c in picks.items():
            (out / f"multi_{ag}_{k}.txt").write_text(fmt(c))
    # summary: sequence of (seq, agent, request, n_messages)
    with open(out / "multi_index.txt", "w") as f:
        for c in calls:
            f.write(f"{c.get('seq')}\t{c.get('agent')}\t{c['request']}\t{c.get('round')}\t{c.get('turn')}\tnmsg={len(c['messages'])}\tresp={str(c.get('response'))[:60]!r}\n")
