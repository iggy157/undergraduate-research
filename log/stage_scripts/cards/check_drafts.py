"""Mechanical checks of card rewrite drafts against data/<domain>/instances.json.
usage: python check_drafts.py <draft_dir>   (reads the repo's instances.json for originals)"""
import json, re, sys, glob, os
ROOT = "/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research"
FIRST = re.compile(r"\b(I|we|our|us|my|me|ours|I'm|I've|we've|we're|I'd|we'd|I'll|we'll)\b")
NUM = re.compile(r"\b(?:\d[\d,.%]*|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half|third|quarter|dozen|twice|thrice|once)\b", re.I)
LABEL = re.compile(r"(?:\b(?:option|candidate|proposal|label)\s+[A-D]\b|\b[A-D]:|\b[B-D]\b)")  # a bare "A" is the article
STOP = {"the","a","an","of","and","for","in","on","at","to","with","by","from","as","or"}
def words(s): return re.findall(r"[A-Za-z][A-Za-z'-]*", s.lower())
problems = []; stats = {"cards":0,"changed":0}
draft_dir = sys.argv[1]
for dom in ("candidate_selection","shared_living"):
    data = json.load(open(f"{ROOT}/data/{dom}/instances.json"))
    for inst in data["instances"]:
        iid = inst["instance_id"]; path = f"{draft_dir}/{iid}_draft.json"
        if not os.path.exists(path): problems.append(f"{iid}: draft missing"); continue
        d = json.load(open(path))
        if d.get("instance_id") != iid: problems.append(f"{iid}: instance_id mismatch")
        orig = {c["card_id"]: c for c in inst["card_pool"]}
        cards = d.get("cards", [])
        if [c["card_id"] for c in cards] != list(orig): problems.append(f"{iid}: card ids/order differ")
        opt_words = set()
        for o in inst["topic"]["options"]:
            opt_words |= {w for w in words(o["name"]) if w not in STOP}
        titles = []
        for c in cards:
            stats["cards"] += 1
            o = orig.get(c["card_id"]); 
            if o is None: continue
            t, x = c.get("title","").strip(), c.get("text","").strip()
            tw = words(t)
            if not (3 <= len(tw) <= 7): problems.append(f"{iid} {c['card_id']}: title has {len(tw)} words: {t!r}")
            if t.lower() in titles: problems.append(f"{iid} {c['card_id']}: duplicate title {t!r}")
            titles.append(t.lower())
            hit = set(tw) & opt_words
            if hit: problems.append(f"{iid} {c['card_id']}: title contains option word(s) {sorted(hit)}: {t!r}")
            if LABEL.search(t): problems.append(f"{iid} {c['card_id']}: title contains a label: {t!r}")
            if FIRST.search(x): problems.append(f"{iid} {c['card_id']}: first person remains: {FIRST.findall(x)}")
            if FIRST.search(t): problems.append(f"{iid} {c['card_id']}: first person in title: {t!r}")
            n0, n1 = sorted(w.lower() for w in NUM.findall(o["text"])), sorted(w.lower() for w in NUM.findall(x))
            if n0 != n1: problems.append(f"{iid} {c['card_id']}: numbers differ {n0} -> {n1}")
            r = len(x) / max(1, len(o["text"]))
            if not (0.8 <= r <= 1.2): problems.append(f"{iid} {c['card_id']}: length ratio {r:.2f}")
            changed = (x != o["text"].strip())
            if changed != bool(c.get("changed")): problems.append(f"{iid} {c['card_id']}: changed flag {c.get('changed')} but text {'differs' if changed else 'is identical'}")
            if changed: stats["changed"] += 1
            if LABEL.search(x) and not LABEL.search(o["text"]): problems.append(f"{iid} {c['card_id']}: label added to text")
            for o2 in inst["topic"]["options"]:
                if o2["name"].lower() in x.lower() and o2["name"].lower() not in o["text"].lower():
                    problems.append(f"{iid} {c['card_id']}: option name {o2['name']!r} added to text")
print(json.dumps(stats))
for p in problems: print("PROBLEM:", p)
print("OK" if not problems else f"{len(problems)} problems")
