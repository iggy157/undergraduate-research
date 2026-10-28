"""python -m agent --url ws://127.0.0.1:10000 (--seat 3 | --seats all) --setup <setup_id> --log-dir log
                [--model default] [--fake] [--info-mode dynamic|fixed] [--reveal] [--writer] [--stepped] [--scenario auto|PATH]

Conditions (DESIGN §13): ``--reveal`` = M1 (all participants + hidden information in the system prompt),
``--writer`` = single-online (one writer LLM writes every seat's line from the shared writer view; needs
``--seats all``: the five seats run as threads of this process), ``--stepped`` = single-batch-stepped (the
single-batch prompt continued one line per call, ``--seats all``), ``--scenario`` = the ``## Plan`` block.
``--dump-prompts`` prints the system prompt and an example TALK message instead of connecting.
"""
from __future__ import annotations

import argparse
import sys
import threading

from agent.base import FakeLLM, OpenAILLM, load_model_config, make_agent, run_client
from agent.base.dump import dump_prompts
from agent.base.registry import make_game_agents
from common.scenario import DEFAULT_GRANULARITY, GRANULARITIES, load_scenario, resolve_scenario, scenario_view, validate_scenario
from common.setup import GameContext


def load_scenario_arg(ctx: GameContext, spec: str | None, granularity: str | None = None) -> dict | None:
    """The validated plan at ``granularity`` (default: the runners' default view, DEFAULT_GRANULARITY)."""
    if spec is None:
        return None
    path = resolve_scenario(ctx, spec)
    sc = load_scenario(path)
    errs = validate_scenario(sc, ctx)
    if errs:
        raise ValueError(f"scenario {path}: " + "; ".join(errs))
    return scenario_view(sc, granularity or DEFAULT_GRANULARITY)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m agent", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="ws://127.0.0.1:10000")
    ap.add_argument("--seat", type=int, default=None, choices=range(1, 6))
    ap.add_argument("--seats", default=None, choices=["all"], help="run the five seats in this process")
    ap.add_argument("--setup", required=True, help="setup_id or path")
    ap.add_argument("--log-dir", default="log")
    ap.add_argument("--model", default="default", help="entry under models: in config/models.yml")
    ap.add_argument("--fake", action="store_true", help="canned FakeLLM, no endpoint")
    ap.add_argument("--connect-timeout", type=float, default=60.0)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--dump-prompts", action="store_true")
    ap.add_argument("--temperature", type=float, default=None, help="override models.yml (0 = greedy)")
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"], default=None,
                    help="override the setup's info_mode (must match the server's --info-mode)")
    ap.add_argument("--reveal", action="store_true", help="M1: all participants + hidden information")
    ap.add_argument("--writer", action="store_true", help="single-online: one writer, shared writer view (needs --seats all)")
    ap.add_argument("--stepped", action="store_true",
                    help="single-batch-stepped: the batch prompt continued one line per call (needs --seats all)")
    ap.add_argument("--scenario", default=None, help="'auto' = scenarios/<domain>/<setup_id>.json, or a path")
    ap.add_argument("--plan-granularity", choices=list(GRANULARITIES), default=None,
                    help=f"view of the plan to show (default {DEFAULT_GRANULARITY})")
    a = ap.parse_args(argv)
    if (a.seat is None) == (a.seats is None):
        ap.error("give exactly one of --seat N / --seats all")
    if (a.writer or a.stepped) and a.seats != "all":
        ap.error("--writer / --stepped need --seats all (the seats share one view)")
    if a.writer and a.stepped:
        ap.error("--writer and --stepped are different conditions")

    ctx = GameContext.load(a.setup)
    if a.info_mode:
        ctx.setup.info_mode = a.info_mode
    try:
        scenario = load_scenario_arg(ctx, a.scenario, a.plan_granularity)
    except (OSError, ValueError) as e:
        print(f"[agent] {e}", file=sys.stderr)
        return 2
    if a.dump_prompts:
        print(dump_prompts(ctx, a.seat or 1, reveal=a.reveal, writer=a.writer, stepped=a.stepped, scenario=scenario))
        return 0
    if a.fake:
        cfg = None
        llm_factory = FakeLLM
        max_tokens, stop_talk = None, None
    else:
        cfg = load_model_config(a.model, temperature=a.temperature, top_p=a.top_p, top_k=a.top_k)
        llm_factory = lambda: OpenAILLM(cfg)  # noqa: E731
        max_tokens, stop_talk = cfg.max_tokens, list(cfg.stop_talk)
    try:
        if a.seats == "all":
            agents = make_game_agents(ctx, llm_factory, a.log_dir, max_tokens=max_tokens, stop_talk=stop_talk,
                                      reveal=a.reveal, writer=a.writer, stepped=a.stepped, scenario=scenario)
            rcs: dict[int, int] = {}

            def run(ag) -> None:
                try:
                    rcs[ag.seat] = run_client(a.url, ag, connect_timeout=a.connect_timeout, verbose=a.verbose)
                except Exception as e:  # noqa: BLE001
                    print(f"[agent seat{ag.seat}] fatal: {type(e).__name__}: {e}", file=sys.stderr)
                    rcs[ag.seat] = 1

            threads = [threading.Thread(target=run, args=(ag,), daemon=True) for ag in agents]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            return max(rcs.values()) if rcs else 1
        ag = make_agent(ctx, a.seat, llm_factory(), a.log_dir, max_tokens=max_tokens, stop_talk=stop_talk,
                        reveal=a.reveal, scenario=scenario)
        return run_client(a.url, ag, connect_timeout=a.connect_timeout, verbose=a.verbose)
    except Exception as e:  # noqa: BLE001
        print(f"[agent seat{a.seat}] fatal: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
