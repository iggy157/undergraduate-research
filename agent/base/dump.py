"""Print the system prompt and an example TALK message for a setup/seat (no server, no LLM)."""
from __future__ import annotations

from typing import Any

from common.setup import GameContext
from common.transcript import SeatTranscript

from .prompts import build_system_prompt, build_talk_message, make_agent_env, rules_of


def dump_prompts(ctx: GameContext, seat: int, *, reveal: bool = False, writer: bool = False, stepped: bool = False,
                 scenario: dict[str, Any] | None = None) -> str:
    ctx.check_dynamic_ready()  # same gate as a real run: empty card titles are an error, not empty bullets
    env = make_agent_env()
    rules = rules_of(ctx)
    first_round = int(rules["first_round"])
    name = ctx.name_of_seat(seat)
    others = [n for n in ctx.speaking_order_names if n != name]
    view = SeatTranscript(ctx, None if (writer or stepped) else seat)
    view.period(first_round)
    view.ensure_turn(first_round, 1)
    view.add_talk(first_round, 0, 1, others[0], "Good morning, everyone.")
    view.add_talk(first_round, 1, 1, others[1], str(rules["pass_skip"]), skip=True)
    if stepped:
        from single.base.prompt import build_messages
        sys_msg, user_msg = build_messages(ctx, scenario=scenario)
        out = ["=== system", sys_msg["content"], "", "=== user", user_msg["content"], "",
               f"=== TALK (assistant, continued), {rules['Period']} {first_round}, turn 1, after two example talks",
               build_talk_message(view.render(), name)]
        return "\n".join(out)
    out = ["=== system", build_system_prompt(ctx, seat, env, reveal=reveal, writer=writer, scenario=scenario), "",
           f"=== TALK (user), {rules['Period']} {first_round}, turn 1, after two example talks",
           build_talk_message(view.render(), name)]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--seat", type=int, required=True)
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"])
    ap.add_argument("--reveal", action="store_true")
    ap.add_argument("--writer", action="store_true")
    a = ap.parse_args(argv)
    ctx = GameContext.load(a.setup)
    if a.info_mode:
        ctx.setup.info_mode = a.info_mode
    print(dump_prompts(ctx, a.seat, reveal=a.reveal, writer=a.writer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
