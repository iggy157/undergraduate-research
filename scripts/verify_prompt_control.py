"""Verify that the conditions share byte-identical common blocks and differ only where designed (DESIGN §6.3, §7.3, §13).

For each setup it renders the shared blocks directly and checks:
  (1) single-batch system == role(single) + blocks + ## Participants x5 (+ ## Hidden information)
  (2) multi-private system == role(multi, seat) + blocks + ## Your profile (own identity only; no other identity leaks)
  (3) multi-public system  == single-batch system with the role paragraph swapped for role(multi, seat)
  (4) single-online system == single-batch system with the role paragraph swapped for role(online);
      single-batch-stepped uses the single-batch system itself
  (5) with a plan (scenarios/<domain>/<setup_id>.json, when present), at every derivable granularity: the plan
      conditions all end with the same ## Plan block and the rest is as in (1) / (3) / (4); multi-private gets only
      a process plan, with its own part only and no outcome in it
  (6) the single-only text (user prompt minus the shared blocks and the identities) must not restate the rules
      (no sentence of vote_rule / end / action / schedule / private / role sentences; ``round N`` / ``day N`` only
      in the Markdown skeleton)

usage: .venv/bin/python scripts/verify_prompt_control.py [--setups a,b] [--all] [--info-mode fixed] [--dump DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import DOMAINS  # noqa: E402
from common.render import (PROFILE_HEADING, SHARED_BLOCKS, hidden_block, identity_block, make_env,  # noqa: E402
                           participants_block, role_block, scenario_block, shared_block, system_prompt)
from common.conditions import PRIVATE_SAFE_PLANS  # noqa: E402
from common.scenario import GRANULARITIES, load_scenario, scenario_path, scenario_view, validate_scenario  # noqa: E402
from common.setup import SETUPS, GameContext  # noqa: E402

SHARED = SHARED_BLOCKS
RULE_SENTENCES = ("vote_rule_sentence", "end_sentence", "action_rule_sentence")
_ROUND_REF = re.compile(r"\b(round|day) [0-9]\b", re.IGNORECASE)
_HEADING_REF = re.compile(r"#{1,6} (?:Round|Day) [0-9]")  # inline reference to a skeleton heading
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def single_only_text(user: str, blocks: dict[str, str], idents: dict[int, str]) -> str:
    rest = user
    for txt in list(blocks.values()) + list(idents.values()):
        rest = rest.replace(txt, "")
    return rest


def check_single_restatements(setup_id: str, ctx, rest: str) -> list[str]:
    """Rule sentences and round/day numbers must not appear outside the shared blocks (DESIGN §6.3)."""
    from common.render import rules_context
    problems: list[str] = []
    rc = rules_context(ctx)
    texts = [(key, str(rc[key])) for key in RULE_SENTENCES]
    texts += [("schedule_notes", n) for n in rc["schedule_notes"]]
    texts += [("private_sentence", rc["private_sentence"])] + [("role_sentences", r) for r in rc["role_sentences"]]
    texts += [("schedule_table", c) for row in rc["schedule_table"]["rows"] for c in row]
    for key, text in texts:
        for sent in _SENT_SPLIT.split(text.strip()):
            sent = sent.strip()
            if len(sent) >= 15 and sent in rest:
                problems.append(f"{setup_id}: single-only text restates {key}: {sent!r}")
    for line in rest.splitlines():
        if line.lstrip().startswith("#"):
            continue
        stripped = _HEADING_REF.sub("", line)
        m = _ROUND_REF.search(stripped)
        if m:
            problems.append(f"{setup_id}: single-only text mentions {m.group(0)!r} outside the skeleton: {line.strip()!r}")
    return problems


def _swap_role(text: str, old_role: str, new_role: str) -> str:
    assert text.startswith(old_role + "\n\n"), "system prompt must start with its role paragraph"
    return new_role + text[len(old_role):]


def check_setup(setup_id: str, dump: Path | None, info_mode: str | None) -> list[str]:
    from agent.base import build_system_prompt  # late import: implemented separately
    from single.base import build_messages

    ctx = GameContext.load(setup_id)
    if info_mode:
        ctx.setup.info_mode = info_mode
    env = make_env()
    blocks = {b: shared_block(env, ctx, b) for b in SHARED}
    idents = {seat: identity_block(env, ctx, seat) for seat in range(1, 6)}
    problems: list[str] = []
    role_single = role_block(env, ctx, "single")
    role_online = role_block(env, ctx, "online")

    # (1) S0
    single_msgs = build_messages(ctx)
    sys_single, user_single = single_msgs[0]["content"], single_msgs[1]["content"]
    expected_single = "\n\n".join([role_single] + [blocks[b] for b in SHARED] + [participants_block(env, ctx)]
                                  + ([hidden_block(env, ctx)] if hidden_block(env, ctx) else []))
    if sys_single != expected_single:
        problems.append(f"{setup_id}: single system prompt is not role + blocks + participants (+ hidden)")
    if sys_single != system_prompt(env, ctx, "single"):
        problems.append(f"{setup_id}: single system prompt differs from common.render.system_prompt")
    if any(blocks[b] in user_single for b in SHARED):
        problems.append(f"{setup_id}: single user prompt repeats a shared block")
    problems += check_single_restatements(setup_id, ctx, single_only_text(sys_single + "\n" + user_single, blocks, idents))

    # (2) M0, (3) M1, (4) S-online
    for seat in range(1, 6):
        role_multi = role_block(env, ctx, "multi", seat)
        m0 = build_system_prompt(ctx, seat)
        expected_m0 = "\n\n".join([role_multi] + [blocks[b] for b in SHARED] + [PROFILE_HEADING + "\n" + idents[seat]])
        if m0 != expected_m0:
            problems.append(f"{setup_id}: M0 system prompt (seat {seat}) is not role + blocks + own profile")
        for other, txt in idents.items():
            if other != seat and txt in m0:
                problems.append(f"{setup_id}: M0 system prompt (seat {seat}) leaks identity of seat {other}")
        m1 = build_system_prompt(ctx, seat, reveal=True)
        if m1 != _swap_role(sys_single, role_single, role_multi):
            problems.append(f"{setup_id}: M1 system prompt (seat {seat}) is not the single one with the participant role")
        on = build_system_prompt(ctx, seat, writer=True)
        if on != _swap_role(sys_single, role_single, role_online):
            problems.append(f"{setup_id}: single-online system prompt (seat {seat}) is not the single one with the online role")
        from single.base.prompt import build_messages as _bm
        if _bm(ctx)[0]["content"] != sys_single:
            problems.append(f"{setup_id}: single-batch-stepped system prompt differs from single-batch")

    # (5) plan conditions
    sp = scenario_path(ctx.domain, setup_id)
    if sp.is_file():
        sc = load_scenario(sp)
        errs = validate_scenario(sc, ctx)
        if errs:
            problems.append(f"{setup_id}: scenario invalid: {errs[0]}")
    else:  # no generated plan yet: check the plan conditions with the canned one
        from single.base.fake import canned_scenario
        sc = canned_scenario(ctx)
    if True:
        for g in GRANULARITIES:
            try:
                view = scenario_view(sc, g)
            except ValueError:
                continue
            plan = scenario_block(env, ctx, view)
            s1 = build_messages(ctx, scenario=view)[0]["content"]
            if s1 != sys_single + "\n\n" + plan:
                problems.append(f"{setup_id}: single-batch-{g} system prompt is not single-batch + the plan block")
            for seat in range(1, 6):
                m2 = build_system_prompt(ctx, seat, reveal=True, scenario=view)
                if m2 != build_system_prompt(ctx, seat, reveal=True) + "\n\n" + plan:
                    problems.append(f"{setup_id}: multi-public-{g} system prompt (seat {seat}) is not multi-public + the plan block")
                w = build_system_prompt(ctx, seat, writer=True, scenario=view)
                if w != build_system_prompt(ctx, seat, writer=True) + "\n\n" + plan:
                    problems.append(f"{setup_id}: single-online-{g} system prompt (seat {seat}) is not single-online + the plan block")
                if g in PRIVATE_SAFE_PLANS:
                    own = build_system_prompt(ctx, seat, scenario=view)
                    own_plan = scenario_block(env, ctx, view, seats=[seat])
                    if own != build_system_prompt(ctx, seat) + "\n\n" + own_plan:
                        problems.append(f"{setup_id}: multi-private-{g} system prompt (seat {seat}) is not multi-private + its own plan view")
                    if "Votes:" in own_plan or "Executed:" in own_plan or "Night:" in own_plan or "Outcome:" in own_plan:
                        problems.append(f"{setup_id}: the {g} plan given to multi-private names an outcome")

    if dump:
        dump.mkdir(parents=True, exist_ok=True)
        (dump / f"{setup_id}.single.json").write_text(json.dumps(single_msgs, ensure_ascii=False, indent=1))
        for seat in range(1, 6):
            (dump / f"{setup_id}.multi.seat{seat}.txt").write_text(build_system_prompt(ctx, seat))
            (dump / f"{setup_id}.reveal.seat{seat}.txt").write_text(build_system_prompt(ctx, seat, reveal=True))
        (dump / f"{setup_id}.online.txt").write_text(build_system_prompt(ctx, 1, writer=True))
    print(f"{setup_id}: {'OK' if not problems else 'PROBLEMS=' + str(len(problems))}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--setups")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"], default=None,
                    help="check the setups in this info mode (audit C6: fixed)")
    ap.add_argument("--dump", type=Path)
    a = ap.parse_args()
    if a.setups:
        ids = a.setups.split(",")
    elif a.all:
        ids = sorted(p.stem for d in DOMAINS for p in (SETUPS / d).glob("*.json"))
    else:
        ids = [f"{d}_0001" for d in DOMAINS]
    problems: list[str] = []
    for sid in ids:
        problems += check_setup(sid, a.dump, a.info_mode)
    for p in problems:
        print("PROBLEM:", p)
    print("all conditions consistent" if not problems else f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
