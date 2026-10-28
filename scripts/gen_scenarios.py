"""Generate the plans (scenarios/<domain>/<setup_id>.json, DESIGN §13) with the same model as the games.

usage: .venv/bin/python scripts/gen_scenarios.py --setups aiwolf_0001,aiwolf_0002 | --domain aiwolf | --all
                                                [--model default] [--attempts 4] [--force] [--dry-run] [--fake]

For each setup the writer's system prompt of S0 (role + rules + participants + hidden information) is sent
with a planning request (scripts/prompts/scenario_request.jinja): the model returns one JSON object with the
public line of every period, the votes / night actions, and one line per participant. The plan is replayed
with the game rules (common.scenario.validate_scenario); invalid plans are retried with the problems quoted
(up to --attempts); mechanical slips (lines after Over, night actions after the game is over) are repaired
deterministically first (``common.scenario.repair_plan``, recorded in the file as ``repairs``), and the final file
records the attempts. Existing files are kept unless --force.
The plans are generated from the setup only, never from a played transcript. The finest level (turn) is generated;
the coarser views (outline, outcome) are derived from it at run time (--plan-granularity of the runners).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import DOMAINS  # noqa: E402
from common.render import make_env, rules_context, system_prompt  # noqa: E402
from common.llm_meta import code_tree_sha1, served_info  # noqa: E402
from common.scenario import GRANULARITIES, repair_plan, scenario_path, validate_scenario  # noqa: E402
from common.setup import SETUPS, GameContext  # noqa: E402

PROMPTS = ROOT / "scripts" / "prompts"
_JSON_RE = re.compile(r"\{.*\}", re.S)


def code_sha1() -> dict[str, str]:
    """sha1 of the files that determine a plan besides the model (audit 2026-10-28 C round 2)."""
    import hashlib
    files = {"gen_scenarios.py": Path(__file__), "scenario_request.jinja": PROMPTS / "scenario_request.jinja",
             "common/scenario.py": ROOT / "common" / "scenario.py", "common/prompts/scenario.jinja": ROOT / "common" / "prompts" / "scenario.jinja"}
    return {k: hashlib.sha1(p.read_bytes()).hexdigest() for k, p in files.items() if p.is_file()}


def request_text(ctx: GameContext, problems: list[str] | None = None, granularity: str = "turn") -> str:
    env = make_env(PROMPTS)
    v = rules_context(ctx)
    aiwolf = ctx.domain == "aiwolf"
    v.update(aiwolf=aiwolf, names=ctx.names, problems=problems or [], granularity=granularity,
             vote_periods=[n for n in range(int(v["first_round"]), int(v["rounds_total"]) + 1)
                           if (n >= 1 if aiwolf else n == int(v["rounds_total"]))])
    return env.get_template("scenario_request.jinja").render(**v).strip()


def parse_json(text: str) -> dict:
    m = _JSON_RE.search(text)
    if not m:
        raise ValueError("no JSON object in the reply")
    return json.loads(m.group(0))


def generate(ctx: GameContext, llm, attempts: int, max_tokens: int, granularity: str = "turn") -> tuple[dict | None, list[dict]]:
    env = make_env()
    system = system_prompt(env, ctx, "single")
    history: list[dict] = []
    problems: list[str] = []
    seen: list[str] = []  # every problem raised so far (a greedy model otherwise alternates between two slips)
    banned: list[str] = []  # words the validator flagged in the prose; a greedy model repeats them unless told
    for i in range(attempts):
        for pr in problems:
            if pr not in seen:
                seen.append(pr)
            for w in re.findall(r"\('([^']+)'\)", pr):
                if w not in banned:
                    banned.append(w)
        extra = [f"Do not use these words anywhere in \"public\" or \"seats\": {', '.join(banned)}"] if banned else []
        user = request_text(ctx, seen + extra, granularity)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        text, meta = llm.complete(messages, max_tokens)
        rec = {"attempt": i + 1, "messages": messages, "response": text, "usage": meta.get("usage"),
               "finish_reason": meta.get("finish_reason"), "error": meta.get("error"),
               "sampling": llm.sampling() if hasattr(llm, "sampling") else None}
        for k in ("tokens", "prompt_token_ids", "model"):
            if meta.get(k) is not None:
                rec[k] = meta[k]
        try:
            sc = parse_json(text)
            sc["setup_id"] = ctx.setup.setup_id
            sc["granularity"] = granularity
            repairs = repair_plan(sc, ctx)
            problems = validate_scenario(sc, ctx)
        except (ValueError, TypeError, KeyError) as e:
            sc, problems, repairs = None, [f"{type(e).__name__}: {e}"], []
        rec["problems"] = list(problems)
        rec["repairs"] = list(repairs)
        if sc is not None:
            sc["repairs"] = list(repairs)
        history.append(rec)
        if sc is not None and not problems:
            return sc, history
    return None, history


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setups")
    ap.add_argument("--domain", choices=list(DOMAINS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model", default="default")
    ap.add_argument("--attempts", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the request for the first setup and exit")
    ap.add_argument("--fake", action="store_true", help="use a canned valid plan (tests)")
    ap.add_argument("--out-dir", type=Path, default=None, help="write under this directory instead of scenarios/")
    ap.add_argument("--granularity", choices=list(GRANULARITIES), default="turn",
                    help="the level to generate (the finest, 'turn', by default; coarser views are derived at run time)")
    a = ap.parse_args(argv)
    if a.setups:
        ids = a.setups.split(",")
    elif a.domain:
        ids = sorted(p.stem for p in (SETUPS / a.domain).glob("*.json"))
    elif a.all:
        ids = sorted(p.stem for d in DOMAINS for p in (SETUPS / d).glob("*.json"))
    else:
        ap.error("give --setups, --domain or --all")

    if a.dry_run:
        ctx = GameContext.load(ids[0])
        print("=== system ===")
        print(system_prompt(make_env(), ctx, "single"))
        print("=== user ===")
        print(request_text(ctx, granularity=a.granularity))
        return 0
    if a.fake:
        from single.base.fake import canned_scenario_llm
        llm = canned_scenario_llm
    else:
        from single.base.llm import OpenAIClient
        llm = OpenAIClient.from_config(a.model, temperature=a.temperature)
    failed = 0
    for sid in ids:
        ctx = GameContext.load(sid)
        out = scenario_path(ctx.domain, sid)
        if a.out_dir is not None:
            out = a.out_dir / ctx.domain / f"{sid}.json"
        if out.is_file() and not a.force:
            print(f"{sid}: exists, skipped")
            continue
        sc, history = generate(ctx, llm(ctx) if a.fake else llm, a.attempts, a.max_tokens, a.granularity)
        if sc is None:
            failed += 1
            print(f"{sid}: FAILED after {len(history)} attempts: {history[-1]['problems'][:3]}")
            (out.parent).mkdir(parents=True, exist_ok=True)
            (out.parent / f"{sid}.failed.json").write_text(json.dumps(history, ensure_ascii=False, indent=1))
            continue
        sc["source"] = {"generated_by": "scripts/gen_scenarios.py", "model": getattr(llm, "model", "fake"),
                        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "attempts": len(history), "max_attempts": a.attempts, "max_tokens": a.max_tokens,
                        "granularity": a.granularity,
                        "sampling": llm.sampling() if hasattr(llm, "sampling") else None,
                        "served": served_info(llm.base_url, llm.model, llm.api_key) if hasattr(llm, "base_url") else None,
                        "code_sha1": code_sha1(), "code_tree": code_tree_sha1()}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(sc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out.parent / f"{sid}.attempts.json").write_text(json.dumps(history, ensure_ascii=False, indent=1))
        try:
            shown = out.relative_to(ROOT)
        except ValueError:
            shown = out
        print(f"{sid}: ok ({len(history)} attempt(s)) -> {shown}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
