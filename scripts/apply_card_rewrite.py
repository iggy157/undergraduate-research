"""Apply the card rewrite drafts (DESIGN §9-9) to data/<domain>/instances.json.

Each draft is ``<draft_dir>/<instance_id>_draft.json`` with ``cards: [{card_id, title, text, changed, change}]``.
For every card: ``title`` is set, ``text`` is replaced, and the original text is kept in ``text_source``
(added once; a second run compares against ``text_source``). origin_seat / bearing are untouched.

usage: .venv/bin/python scripts/apply_card_rewrite.py <draft_dir> [--check]   (--check: report only, write nothing)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("candidate_selection", "shared_living")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    draft_dir = Path(sys.argv[1])
    check = "--check" in sys.argv
    total = changed = titled = 0
    for dom in DOMAINS:
        path = ROOT / "data" / dom / "instances.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for inst in data["instances"]:
            iid = inst["instance_id"]
            dp = draft_dir / f"{iid}_draft.json"
            if not dp.exists():
                print(f"ERROR: no draft for {iid}")
                return 1
            draft = json.loads(dp.read_text(encoding="utf-8"))
            cards = {c["card_id"]: c for c in draft["cards"]}
            if set(cards) != {c["card_id"] for c in inst["card_pool"]}:
                print(f"ERROR: {iid}: card ids differ")
                return 1
            for c in inst["card_pool"]:
                d = cards[c["card_id"]]
                title, text = str(d["title"]).strip(), str(d["text"]).strip()
                if not (3 <= len(title.split()) <= 7):
                    print(f"ERROR: {iid} {c['card_id']}: bad title {title!r}")
                    return 1
                source = c.get("text_source", c["text"])
                total += 1
                if text != source:
                    changed += 1
                if title:
                    titled += 1
                c["text_source"] = source
                c["text"] = text
                c["title"] = title
        titles_seen = {}
        for inst in data["instances"]:
            ts = [c["title"].lower() for c in inst["card_pool"]]
            if len(set(ts)) != len(ts):
                print(f"ERROR: duplicate titles in {inst['instance_id']}")
                return 1
            titles_seen[inst["instance_id"]] = ts
        data["note"] = ("card_pool[].title and text come from the §9-9 rewrite (third-person wording, titles); "
                        "text_source keeps the original text. Required for info_mode=dynamic.")
        if not check:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{'would apply' if check else 'applied'}: {total} cards, {changed} texts changed, {titled} titles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
