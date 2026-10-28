"""A canned, grammar-valid transcript for any setup (used by ``--fake`` and as a test fixture).

The content is deliberately bland; the point is that the converter accepts it with zero violations.
"""
from __future__ import annotations

from common.setup import GameContext


def _talk_rounds(ctx: GameContext, names: list[str], period: str, r: int, turns: int) -> list[str]:
    out = [f"## {period} {r}", "### Talk"]
    for t in range(1, turns + 1):
        out.append(f"#### Turn {t} of {turns}")
        for n in names:
            if t == turns:
                out.append(f"- **{n}**: {ctx.rules['pass_over']}")
            elif t == turns - 1 and n == names[-1]:
                out.append(f"- **{n}**: {ctx.rules['pass_skip']}")
            else:
                out.append(f"- **{n}**: I have a short point to make and will keep it brief.")
    return out


def canned_transcript(ctx: GameContext) -> str:
    rules = ctx.rules
    period = str(rules["period_name"]).capitalize()
    turns = int(rules["turns_per_round"])
    order = ctx.speaking_order_names
    lines = [f"# {ctx.setup.setup_id}", "## Participants"]
    if ctx.domain == "aiwolf":
        lines += ["| Seat | Name | Role |", "|---|---|---|"]
        for s in ctx.setup.seats:
            lines.append(f"| {s.seat} | {s.persona} | {s.role_slot.capitalize()} |")
        seer = next(n for n in ctx.names if ctx.role_of_name(n) == "SEER")
        wolf = next(n for n in ctx.names if ctx.role_of_name(n) == "WEREWOLF")
        other = next(n for n in order if n not in (seer, wolf))
        lines += _talk_rounds(ctx, order, period, 0, turns)
        lines += ["### Action", f"- divine: {seer} -> {other} (human)"]
        lines += _talk_rounds(ctx, order, period, 1, turns)
        lines += ["### Vote"] + [f"- {n} -> {wolf}" for n in order] + [f"- execution: {wolf}"]
        lines += ["## Result", "- winner: village"]
    else:
        lines += ["| Seat | Name |", "|---|---|"]
        for s in ctx.setup.seats:
            lines.append(f"| {s.seat} | {s.persona} |")
        first, total = int(rules["first_round"]), int(rules["rounds_total"])
        label = ctx.option_labels()[0]
        for r in range(first, total + 1):
            lines += _talk_rounds(ctx, order, period, r, turns)
            if r == first and ctx.setup.info_mode == "dynamic":
                titles = [c["title"] for c in ctx.card_pool()]
                lines.append("### Action")
                for i, n in enumerate(ctx.names):
                    a, b = titles[(2 * i) % len(titles)], titles[(2 * i + 1) % len(titles)]
                    lines.append(f"- investigate: {n} -> {a}; {b}")
            if r == total:
                lines += ["### Vote"] + [f"- {n} -> {label}" for n in order] + [f"- adopted: {label}"]
        lines += ["## Result", f"- adopted: {label}"]
    return "\n".join(lines) + "\n"


__all__ = ["canned_transcript"]


def canned_scenario(ctx) -> dict:
    """A valid plan for ``ctx`` (tests / ``gen_scenarios.py --fake``): aiwolf = the Seer divines the Werewolf on
    night 0 and everyone votes it out on day 1; discussion = everyone votes for the first option."""
    from common.protocol import Role
    names = list(ctx.names)
    seats = {n: f"{n} takes part, weighs what is said and makes up their own mind." for n in names}
    over = str(ctx.rules["pass_over"])

    def turns(alive: list[str]) -> list[dict]:
        return [{"turn": 1, "lines": {n: f"{n} says what they think so far." for n in alive}},
                {"turn": 2, "lines": {n: over for n in alive}}]

    if ctx.domain == "aiwolf":
        wolf = next(n for n in names if ctx.role_of_name(n) == Role.WEREWOLF)
        seer = next(n for n in names if ctx.role_of_name(n) == Role.SEER)
        return {"setup_id": ctx.setup.setup_id, "granularity": "turn",
                "periods": [{"period": 0, "public": "Everyone introduces themselves; nobody is suspected yet.",
                             "divine": wolf, "turns": turns(names)},
                            {"period": 1, "public": "The group weighs what was said on the first day and how much to trust each other.",
                             "votes": {n: wolf for n in names}, "executed": wolf, "turns": turns(names)}],
                "seats": seats, "final": {"winner": "VILLAGE"}}
    label = ctx.option_labels()[0]
    last = int(ctx.rules["rounds_total"])
    periods = [{"period": n, "public": f"Round {n}: the participants exchange what they know.", "turns": turns(names)}
               for n in range(1, last)]
    periods.append({"period": last, "public": "The choices are weighed against what was found out.",
                    "votes": {n: label for n in names}, "adopted": label, "turns": turns(names)})
    return {"setup_id": ctx.setup.setup_id, "granularity": "turn", "periods": periods, "seats": seats,
            "final": {"adopted": label}}


def canned_scenario_llm(ctx):
    import json as _json
    from .llm import FakeLLM
    return FakeLLM(_json.dumps(canned_scenario(ctx)))
