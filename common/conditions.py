"""Condition names (DESIGN §13). One tag per condition, used in game ids, log directories and headers.

Axes:
  method       single (one LLM) | multi (one LLM per seat)
  generation   single only: batch (the whole transcript in one call) | batch-stepped (the batch prompt, continued one
               line per call as the writer's own output, outcomes decided by the server) | online (one line per call,
               the transcript so far given in the user message)
  information  multi only: private (own secret only) | public (every participant's secrets shown to every seat)
  plan         none | process | outcome | outline | turn   (the ## Plan block and its granularity; all but process imply public)

Tags: ``single-batch``, ``single-batch-stepped``, ``single-online``, ``multi-private``, ``multi-public``, each optionally
``-<plan>``.
Logs live in ``log/<domain>/<tag without plan>/<game_id>`` with ``game_id = <setup>__<tag>__<model_tag>__<ts>``.
The *pipeline* (which code runs the game) is a separate header field: ``batch`` (single/) or ``server`` (server/ + agent/);
single-online runs on the server pipeline.
"""
from __future__ import annotations

from typing import Any

METHODS = ("single", "multi")
GENERATIONS = ("batch", "batch-stepped", "online")
INFORMATIONS = ("private", "public")
PLANS = ("process", "outcome", "outline", "turn")
PRIVATE_SAFE_PLANS = ("process",)   # no outcomes, no secrets: may be given to multi-private too
BASE_TAGS = ("single-batch", "single-batch-stepped", "single-online", "multi-private", "multi-public")
LEGACY_DIRS = ("single", "multi")  # log directories of runs before 2026-10-28


def condition_tag(method: str, *, generation: str | None = None, information: str | None = None,
                  plan: str | None = None) -> str:
    if method == "single":
        g = generation or "batch"
        if g not in GENERATIONS:
            raise ValueError(f"generation {g!r} not in {GENERATIONS}")
        base = f"single-{g}"
    elif method == "multi":
        i = information or "private"
        if i not in INFORMATIONS:
            raise ValueError(f"information {i!r} not in {INFORMATIONS}")
        if plan and i != "public" and plan not in PRIVATE_SAFE_PLANS:
            raise ValueError(f"plan {plan!r} implies public information (it names the outcome)")
        base = f"multi-{i}"
    else:
        raise ValueError(f"method {method!r} not in {METHODS}")
    if plan:
        if plan not in PLANS:
            raise ValueError(f"plan {plan!r} not in {PLANS}")
        return f"{base}-{plan}"
    return base


def parse_condition(tag: str) -> dict[str, Any]:
    """{'tag', 'method', 'generation'|'information', 'plan', 'dir'} of a tag (ValueError when malformed)."""
    parts = str(tag).split("-")
    if len(parts) < 2 or parts[0] not in METHODS:
        raise ValueError(f"bad condition tag {tag!r}")
    method = parts[0]
    axes: dict[str, Any] = {"tag": tag, "method": method, "plan": None}
    if method == "single":
        if parts[1:3] == ["batch", "stepped"]:
            axes["generation"], rest = "batch-stepped", parts[3:]
        elif parts[1] in GENERATIONS:
            axes["generation"], rest = parts[1], parts[2:]
        else:
            raise ValueError(f"bad condition tag {tag!r}")
        axes["information"] = "public"  # the writer necessarily knows everything
        base = f"single-{axes['generation']}"
    else:
        if parts[1] not in INFORMATIONS:
            raise ValueError(f"bad condition tag {tag!r}")
        axes["information"] = parts[1]
        axes["generation"] = "online"   # one line per call
        rest = parts[2:]
        base = f"multi-{parts[1]}"
    if len(rest) == 1:
        if rest[0] not in PLANS:
            raise ValueError(f"bad condition tag {tag!r}")
        axes["plan"] = rest[0]
    elif rest:
        raise ValueError(f"bad condition tag {tag!r}")
    axes["dir"] = base
    return axes


def condition_dir(tag: str) -> str:
    """The log directory of a condition: the tag without its plan suffix."""
    return parse_condition(tag)["dir"]


def multi_tag(*, reveal: bool = False, writer: bool = False, stepped: bool = False, plan: str | None = None) -> str:
    """The tag of a server-pipeline run from the agent flags."""
    if stepped:
        return condition_tag("single", generation="batch-stepped", plan=plan)
    if writer:
        return condition_tag("single", generation="online", plan=plan)
    public = reveal or (plan is not None and plan not in PRIVATE_SAFE_PLANS)
    return condition_tag("multi", information="public" if public else "private", plan=plan)


__all__ = ["BASE_TAGS", "GENERATIONS", "INFORMATIONS", "LEGACY_DIRS", "METHODS", "PLANS", "PRIVATE_SAFE_PLANS", "condition_dir",
           "condition_tag", "multi_tag", "parse_condition"]
