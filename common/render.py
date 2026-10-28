"""Jinja rendering of the shared prompt blocks (DESIGN §6.2) with variables from rules.yml + setup.

Both methods call ``shared_block(ctx, name, **kw)`` so the rendered text is byte-identical; the
verification script (scripts/verify_prompt_control.py) relies on this.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import ROOT
from .setup import GameContext

COMMON_PROMPTS = ROOT / "common" / "prompts"
# the shared blocks, in the order both system prompts use them (DESIGN §6.2); single source for
# agent/base/prompts.py, single/base/prompt.py, scripts/verify_prompt_control.py and the tests
SHARED_BLOCKS = ("setting", "structure", "schedule", "action")


def make_env(*extra_dirs: Path) -> Environment:
    dirs = [str(COMMON_PROMPTS)] + [str(d) for d in extra_dirs]
    env = Environment(loader=FileSystemLoader(dirs), undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=False,
                      autoescape=False)
    env.filters["join_names"] = join_names
    return env


def join_names(names: list[str]) -> str:
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def rules_context(ctx: GameContext) -> dict[str, Any]:
    """Variables available to every shared block. Pure function of rules.yml + setup + instance."""
    r = dict(ctx.rules)
    topic = ctx.instance["topic"] if ctx.instance else None
    v: dict[str, Any] = {
        **r,
        "domain": ctx.domain,
        "setup_id": ctx.setup.setup_id,
        "info_mode": ctx.setup.info_mode,
        "roster": join_names(ctx.names),
        "roster_list": ctx.names,
        "speaking_order_names": join_names(ctx.speaking_order_names),
        "speaking_order_list": ctx.speaking_order_names,
        "topic": topic,
        "options": ctx.options(),
        "option_labels": ctx.option_labels(),
        "n_options": len(ctx.options()),
        "card_titles": [c["title"] for c in ctx.card_pool()],
        "Period": str(r["period_name"]).capitalize(),
    }
    if ctx.setup.info_mode == "fixed":
        for k in ("schedule_table", "schedule_notes", "action_rule_sentence"):
            if f"{k}_fixed" in r:
                v[k] = r[f"{k}_fixed"]
    # sentences may themselves contain Jinja expressions (topic.title, option_noun, ...)
    env = Environment(undefined=StrictUndefined, autoescape=False)
    for k in ("setting_sentence", "private_sentence", "vote_rule_sentence", "end_sentence",
              "action_rule_sentence", "vote_request_sentence"):
        v[k] = env.from_string(str(v[k])).render(**v)
    v["role_sentences"] = [env.from_string(str(x)).render(**v) for x in list(v.get("role_sentences") or [])]
    t = dict(v["schedule_table"])
    v["schedule_table"] = {"columns": [str(c) for c in t["columns"]],
                           "rows": [[env.from_string(str(c)).render(**v) for c in row] for row in t["rows"]]}
    v["schedule_notes"] = [env.from_string(str(n)).render(**v) for n in list(v.get("schedule_notes") or [])]
    v["action_request_sentences"] = {kk: env.from_string(str(vv)).render(**v)
                                     for kk, vv in dict(r["action_request_sentences"]).items()}
    return v


def shared_block(env: Environment, ctx: GameContext, block: str, **kw: Any) -> str:
    """Render common/prompts/<block>.jinja. ``kw`` adds per-call variables (round_no, turn_no, ...)."""
    v = rules_context(ctx)
    v.update(kw)
    return env.get_template(f"{block}.jinja").render(**v).strip()


def notice_sentence(ctx: GameContext, key: str, **kw: Any) -> str:
    """rules.yml ``notice_sentences[key]`` rendered with the rules context plus ``kw`` (multi notices)."""
    v = rules_context(ctx)
    v.update(kw)
    env = Environment(undefined=StrictUndefined, autoescape=False)
    return env.from_string(str(ctx.rules["notice_sentences"][key])).render(**v).strip()


def role_block(env: Environment, ctx: GameContext, method: str, seat: int | None = None) -> str:
    """common/prompts/role.jinja: 'You are <name> / the writer ...' (first paragraph of both system prompts)."""
    name = ctx.name_of_seat(seat) if seat is not None else ""
    return shared_block(env, ctx, "role", method=method, name=name)


PROFILE_HEADING = "## Your profile"        # multi, own seat only
PARTICIPANTS_HEADING = "## Participants"   # single / reveal conditions: all five identities
ROLE_METHODS = ("multi", "online", "single")


def participants_block(env: Environment, ctx: GameContext) -> str:
    from .setup import N_SEATS
    return PARTICIPANTS_HEADING + "\n" + "\n\n".join(identity_block(env, ctx, s) for s in range(1, N_SEATS + 1))


def hidden_block(env: Environment, ctx: GameContext) -> str:
    """common/prompts/hidden.jinja: options + card texts (discussion domains; aiwolf has nothing hidden
    beyond the roles, which are in the identities)."""
    if ctx.domain == "aiwolf":
        return ""
    from .setup import N_SEATS
    v: dict[str, Any] = rules_context(ctx)
    fixed = ctx.setup.info_mode == "fixed"
    v.update(
        options=ctx.options(),
        cards=[{"title": c["title"], "text": c["text"]} for c in ctx.card_pool()],
        fixed_cards=[(ctx.name_of_seat(s), ctx.fixed_cards_of_seat(s)) for s in range(1, N_SEATS + 1)]
        if fixed else [],
    )
    return env.get_template("hidden.jinja").render(**v).strip()


def scenario_block(env: Environment, ctx: GameContext, scenario: dict[str, Any],
                   seats: list[int] | None = None) -> str:
    """common/prompts/scenario.jinja (the ``## Plan`` block). ``seats`` None = every participant's part."""
    from .scenario import scenario_context
    v: dict[str, Any] = rules_context(ctx)
    v.update(scenario_context(scenario, ctx, seats))
    return env.get_template("scenario.jinja").render(**v).strip()


def system_prompt(env: Environment, ctx: GameContext, method: str, seat: int | None = None,
                  reveal: bool = False, scenario: dict[str, Any] | None = None) -> str:
    """The whole system prompt of any condition (DESIGN §7.1 / §13):

    role (method: multi | online | single) + the shared blocks + (reveal: ## Participants x5 + ## Hidden
    information | own ## Your profile) + (scenario: ## Plan). ``single`` always reveals. The conditions
    differ only in the role paragraph and in reveal / scenario."""
    if method not in ROLE_METHODS:
        raise ValueError(f"method {method!r} not in {ROLE_METHODS}")
    if method == "single":
        reveal = True
    parts = [role_block(env, ctx, method, seat)] + [shared_block(env, ctx, b) for b in SHARED_BLOCKS]
    if reveal:
        parts.append(participants_block(env, ctx))
        h = hidden_block(env, ctx)
        if h:
            parts.append(h)
    else:
        if seat is None:
            raise ValueError("seat is required without reveal")
        parts.append(PROFILE_HEADING + "\n" + identity_block(env, ctx, seat))
    if scenario is not None:
        parts.append(scenario_block(env, ctx, scenario, None if reveal else [int(seat)]))
    return "\n\n".join(parts)


def identity_block(env: Environment, ctx: GameContext, seat: int) -> str:
    name = ctx.name_of_seat(seat)
    p = ctx.persona_of_name(name)
    role = ctx.role_of_seat(seat)
    if ctx.domain == "aiwolf":
        seed_text = role.capitalize()
    else:
        seed_text = ctx.problem_of_seat(seat)
    return shared_block(env, ctx, "identity", name=p.name, age=p.age, gender=p.gender,
                        personality=p.personality, private_seed_text=seed_text)
