"""One single-method run: prompt -> one LLM call -> raw files -> convert -> <game_id>.log / .jsonl.

Layout (IMPLEMENTATION_NOTES §2): ``<log_dir>/<domain>/single/<game_id>/`` with ``raw/prompt.json``,
``raw/transcript.md``, ``<game_id>.log``, ``<game_id>.jsonl``.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.convert.single_markdown import ConvertResult, convert
from common.logwriter import GameLogWriter, write_rows
from common.schema import LogRow
from common import ROOT
from common.conditions import condition_tag, parse_condition
from common.scenario import DEFAULT_GRANULARITY, find_scenario_deviations
from common.setup import DATA, GameContext
from common.violations import find_truncations, find_violations, merge_violations

from .llm import LLMClient
from .prompt import build_messages

METHOD = "single"
PIPELINE = "batch"


@dataclass
class SingleRun:
    game_id: str
    game_dir: Path
    messages: list[dict[str, str]]
    response: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    rows: list[LogRow] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)
    outcome: dict[str, Any] = field(default_factory=dict)


def make_game_id(setup_id: str, model_tag: str, when: datetime | None = None, condition: str = "single-batch") -> str:
    when = (when or datetime.now()).astimezone()  # local wall clock in the id, like the server
    parse_condition(condition)
    return f"{setup_id}__{condition}__{model_tag}__{when:%Y%m%dT%H%M%S}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def rules_hash(domain: str) -> str:
    return hashlib.sha1((DATA / domain / "rules.yml").read_bytes()).hexdigest()


def models_yml_sha1() -> str:
    p = ROOT / "config" / "models.yml"
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else ""


def header_payload(ctx: GameContext, model: str, model_tag: str, started_at: str, finished_at: str | None,
                   outcome: dict[str, Any], rows: list[LogRow], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    participants = []
    for s in ctx.setup.seats:
        p = ctx.persona_of_name(s.persona)
        seed = s.role_slot if ctx.domain == "aiwolf" else ctx.problem_of_seat(s.seat)
        participants.append({"seat": s.seat, "name": s.persona, "role_slot": s.role_slot,
                             "persona": {"name": p.name, "age": p.age, "gender": p.gender,
                                         "personality": p.personality},
                             "private_seed": seed})
    cards: set[str] = set()
    for r in rows:
        if r.type == "action" and r.extra.get("action") == "investigate":
            cards.update(r.extra.get("cards", []))
    return {
        "setup_id": ctx.setup.setup_id, "domain": ctx.domain, "method": METHOD, "model": model,
        "model_tag": model_tag, "info_mode": ctx.setup.info_mode,
        "setup_path": ctx.setup_path_str(), "setup_sha1": ctx.setup_sha1(),
        "started_at": started_at, "finished_at": finished_at,
        "participants": participants, "speaking_order": list(ctx.setup.speaking_order),
        "option_perm": list(ctx.setup.option_perm) if ctx.setup.option_perm else None,
        "card_pool": [{"card_id": c["card_id"], "title": c.get("title", ""), "origin_seat": c.get("origin_seat")}
                      for c in ctx.card_pool()] if ctx.domain != "aiwolf" else [],
        "n_options": len(ctx.options()), "n_unique_cards": len(cards), "outcome": outcome,
        "rules_hash": rules_hash(ctx.domain), "models_yml_sha1": models_yml_sha1(),
        **(extra or {}),
    }


def write_game(game_dir: Path, game_id: str, ctx: GameContext, messages: list[dict[str, str]],
               response: str, meta: dict[str, Any], conv: ConvertResult, model: str, model_tag: str,
               started_at: str, finished_at: str, header_extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Write header / llm_call / violations to the jsonl and the rows to the log; returns the violation items."""
    w = GameLogWriter(game_dir, game_id, ctx.names)
    call = dict(seq=0, seat="writer", request="FULL", round=None, turn=None, ts=started_at, messages=messages,
                response=response, usage=meta.get("usage"), finish_reason=meta.get("finish_reason"),
                error=meta.get("error"), truncated=(meta.get("finish_reason") == "length"),
                latency_ms=meta.get("latency_ms"), model=model)
    for k in ("tokens", "prompt_token_ids", "prompt_token_ids_error", "logprobs_error"):
        if meta.get(k) is not None:
            call[k] = meta[k]
    try:
        w.header(**header_payload(ctx, model, model_tag, started_at, finished_at, conv.outcome, conv.rows,
                                  header_extra))
        w.llm_call(**call)
        # one record: the converter's structural items + the common codes (DESIGN §8) + truncation
        items = merge_violations(conv.violations,
                                 find_violations(conv.rows, ctx) + find_truncations([{"kind": "llm_call", **call}]))
        w.record("violations", items=items)
    finally:
        w.close()
    write_rows(game_dir / f"{game_id}.log", conv.rows)
    return items


def run_single(ctx: GameContext, llm: LLMClient | None, log_dir: Path, *, model: str, model_tag: str,
               max_tokens: int, dry_run: bool = False, game_id: str | None = None,
               header_extra: dict[str, Any] | None = None, scenario: dict[str, Any] | None = None,
               scenario_info: dict[str, Any] | None = None) -> SingleRun:
    """Build the prompt, save it, call ``llm`` once (unless dry_run), convert and write the logs.
    ``scenario``: the plan (S1); its deviations are recorded with the violations (DESIGN §13)."""
    started = now_utc()
    condition = condition_tag("single", generation="batch",
                              plan=scenario.get("granularity", DEFAULT_GRANULARITY) if scenario is not None else None)
    axes = parse_condition(condition)
    game_id = game_id or make_game_id(ctx.setup.setup_id, model_tag, started, condition)
    game_dir = Path(log_dir) / ctx.domain / axes["dir"] / game_id
    raw = game_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    messages = build_messages(ctx, scenario=scenario)
    header_extra = {**(header_extra or {}), "pipeline": PIPELINE, "condition": condition,
                    "axes": {k: v for k, v in axes.items() if k in ("method", "generation", "information", "plan")},
                    "scenario": scenario_info or None}
    (raw / "prompt.json").write_text(json.dumps(messages, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    run = SingleRun(game_id, game_dir, messages)
    if dry_run:
        return run
    if llm is None:
        raise ValueError("llm is required unless dry_run")
    text, meta = llm.complete(messages, max_tokens)
    (raw / "transcript.md").write_text(text, encoding="utf-8")
    conv = convert(text, ctx, game_id)
    if scenario is not None:
        conv.violations.extend(find_scenario_deviations(conv.rows, ctx, scenario))
    if meta.get("error"):
        conv.violations.append({"seq": None, "line": None, "code": "llm_error", "detail": meta["error"]})
    finished = now_utc()
    items = write_game(game_dir, game_id, ctx, messages, text, meta, conv, model, model_tag,
                       started.isoformat(timespec="seconds"), finished.isoformat(timespec="seconds"), header_extra)
    run.response, run.meta = text, meta
    run.rows, run.violations, run.outcome = conv.rows, items, conv.outcome
    return run


__all__ = ["METHOD", "SingleRun", "header_payload", "make_game_id", "now_utc", "rules_hash", "run_single",
           "write_game"]
