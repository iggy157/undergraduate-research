"""Prompt assembly for the multi-agent client (DESIGN §7.1 / §7.4 / §13).

system = common.render.system_prompt: role + the shared blocks + (own profile | all participants + hidden
information in the reveal conditions) + (the plan). Byte-identical blocks with the single writer.
user = the seat view (or, for the online writer, the writer view) of the transcript so far continued with
the line to write; VOTE / action requests put their request sentence and candidates first.
"""
from __future__ import annotations

from typing import Any

from jinja2 import Environment

from common import ROOT
from common.render import PARTICIPANTS_HEADING, PROFILE_HEADING, SHARED_BLOCKS, make_env, rules_context, system_prompt
from common.setup import GameContext

AGENT_PROMPTS = ROOT / "agent" / "prompts"
SYSTEM_BLOCKS = SHARED_BLOCKS


def make_agent_env() -> Environment:
    """Jinja environment that sees both common/prompts and agent/prompts."""
    return make_env(AGENT_PROMPTS)


def build_system_prompt(ctx: GameContext, seat: int, env: Environment | None = None, *, reveal: bool = False,
                        writer: bool = False, scenario: dict[str, Any] | None = None) -> str:
    """M0: role(multi) + blocks + ## Your profile. M1 (reveal): ... + ## Participants x5 + ## Hidden information.
    S-online (writer): role(online) + the M1 tail. Any of them + ## Plan when a scenario is given."""
    env = env or make_agent_env()
    return system_prompt(env, ctx, "online" if writer else "multi", seat, reveal=reveal or writer, scenario=scenario)


def build_talk_message(transcript: str, name: str) -> str:
    """The view so far, continued with the talk label (the model writes the utterance)."""
    return f"{transcript}\n- **{name}**:"


def build_vote_message(ctx: GameContext, transcript: str, name: str, candidates: list[str],
                       env: Environment | None = None, section_open: bool = False) -> str:
    """``section_open``: the view already ends with this period's ``### Vote`` lines (writer view), so the
    label continues the section instead of opening it."""
    env = env or make_agent_env()
    v = rules_context(ctx)
    head = env.get_template("vote_request.jinja").render(
        vote_request_sentence=v["vote_request_sentence"], candidates=list(candidates)).strip()
    return f"{head}\n\n{transcript}\n" + ("" if section_open else "### Vote\n") + f"- {name} ->"


def build_action_message(ctx: GameContext, transcript: str, label: str, request: str, candidates: list[str],
                         env: Environment | None = None, section_open: bool = False) -> str:
    """``label`` is the action line without its target, e.g. ``- divine: Benjamin ->``."""
    env = env or make_agent_env()
    sentence = rules_context(ctx)["action_request_sentences"][str(request)]
    head = env.get_template("action_request.jinja").render(
        action_request_sentence=sentence, candidates=list(candidates)).strip()
    return f"{head}\n\n{transcript}\n" + ("" if section_open else "### Action\n") + label


def rules_of(ctx: GameContext) -> dict[str, Any]:
    return rules_context(ctx)


__all__ = ["AGENT_PROMPTS", "PARTICIPANTS_HEADING", "PROFILE_HEADING", "SYSTEM_BLOCKS", "build_action_message",
           "build_system_prompt", "build_talk_message", "build_vote_message", "make_agent_env", "rules_of"]
