"""Prompt assembly for the single method (DESIGN §7.2 / §13, IMPLEMENTATION_NOTES §5).

Same system/user split as the multi agent (control, 2026-10-27 audit A3):
system = common.render.system_prompt(method="single"): role (writer) + setting / structure / schedule / action
         (shared blocks, byte-identical to the multi agent's) + ## Participants (identities x5) + ## Hidden
         information (discussion domains) + ## Plan (S1 only)
user   = single/prompts/user.jinja: the writing request + format_spec
"""
from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

from jinja2 import Environment

from common import ROOT
from common.render import SHARED_BLOCKS, hidden_block, make_env, rules_context, system_prompt
from common.setup import GameContext

SINGLE_PROMPTS = ROOT / "single" / "prompts"


def make_single_env() -> Environment:
    return make_env(SINGLE_PROMPTS)


def domain_spec(domain: str) -> ModuleType:
    """single.<domain>: FORMAT_TEMPLATE and HAS_DISCLOSURE."""
    return importlib.import_module(f"single.{domain}")


def disclosure_block(env: Environment, ctx: GameContext) -> str:
    """The ``## Hidden information`` block (common/prompts/hidden.jinja); '' for aiwolf."""
    return hidden_block(env, ctx)


def format_block(env: Environment, ctx: GameContext) -> str:
    spec = domain_spec(ctx.domain)
    v: dict[str, Any] = rules_context(ctx)
    seats = [{"seat": s.seat, "name": s.persona, "role": s.role_slot.capitalize()} for s in ctx.setup.seats]
    v.update(seats=seats, setup_id=ctx.setup.setup_id)
    return env.get_template(spec.FORMAT_TEMPLATE).render(**v).strip()


def build_messages(ctx: GameContext, env: Environment | None = None,
                   scenario: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """[system, user] chat messages for one FULL call. Used by the run and by verify_prompt_control."""
    env = env or make_single_env()
    system = system_prompt(env, ctx, "single", scenario=scenario)
    user = env.get_template("user.jinja").render(format_spec=format_block(env, ctx)).strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


__all__ = [
    "SHARED_BLOCKS",
    "SINGLE_PROMPTS",
    "build_messages",
    "disclosure_block",
    "domain_spec",
    "format_block",
    "make_single_env",
]
