"""CLI: python -m server --setup <setup_id|path> --port 10000 --log-dir log [--timeout 600] [--model-tag scripted]
                        [--model <full model name>] [--info-mode dynamic|fixed] [--condition TAG] [--scenario auto|PATH]

Exit code 0 = the game reached a result (NONE included), 1 = aborted (disconnect / notice timeout /
nobody connected), 2 = setup error (unknown setup, dynamic mode without card titles).
Prints one line ``<game_id>\t<outcome json>`` to stdout.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys

from common.scenario import (DEFAULT_GRANULARITY, GRANULARITIES, load_scenario, resolve_scenario, scenario_header,
                             scenario_view, validate_scenario)
from common.setup import GameContext

from .base.runner import run_game


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m server", description=__doc__.splitlines()[0])
    ap.add_argument("--setup", default=os.environ.get("AIWOLF_SETUP_FILE"),
                    help="setup id (e.g. aiwolf_0001) or path to setups/<domain>/<id>.json "
                         "(default: $AIWOLF_SETUP_FILE)")
    ap.add_argument("--port", type=int, default=10000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--log-dir", default="log")
    ap.add_argument("--timeout", type=float, default=600.0, help="seconds to wait for each reply")
    ap.add_argument("--model-tag", default="scripted")
    ap.add_argument("--model", default=None,
                    help="full model name as in config/models.yml, for the jsonl header (default: --model-tag)")
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"], default=None,
                    help="override the setup's info_mode (the agents must be started with the same value)")
    ap.add_argument("--connect-timeout", type=float, default=None,
                    help="seconds to wait for all five seats to connect (default: forever)")
    ap.add_argument("--header-extra", default=None,
                    help="JSON object merged into the jsonl header (run_multi.py passes sampling / model_info)")
    ap.add_argument("--condition", default="multi-private",
                    help="condition tag (common.conditions): multi-private | multi-public | single-online [-outcome|-outline|-turn]")
    ap.add_argument("--scenario", default=None, help="'auto' or a path: the plan the agents were given (deviations recorded)")
    ap.add_argument("--plan-granularity", choices=list(GRANULARITIES), default=None)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    try:
        header_extra = json.loads(args.header_extra) if args.header_extra else None
    except json.JSONDecodeError as e:
        print(f"--header-extra is not JSON: {e}", file=sys.stderr)
        return 2
    if not args.setup:
        ap.error("--setup is required (or set AIWOLF_SETUP_FILE)")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s", stream=sys.stderr)
    try:
        ctx = GameContext.load(args.setup)
        if args.info_mode:
            ctx.setup.info_mode = args.info_mode
        ctx.check_dynamic_ready()
        scenario = scenario_info = None
        if args.scenario is not None:
            sp = resolve_scenario(ctx, args.scenario)
            scenario = load_scenario(sp)
            errs = validate_scenario(scenario, ctx)
            if errs:
                raise ValueError(f"scenario {sp}: " + "; ".join(errs))
            scenario = scenario_view(scenario, args.plan_granularity or DEFAULT_GRANULARITY)
            scenario_info = scenario_header(sp, scenario)
    except (OSError, ValueError, KeyError) as e:
        print(f"setup error: {e}", file=sys.stderr)
        return 2
    try:
        game = asyncio.run(run_game(ctx, args.port, args.log_dir, timeout=args.timeout,
                                    model_tag=args.model_tag, host=args.host,
                                    connect_timeout=args.connect_timeout, model=args.model,
                                    header_extra=header_extra, condition=args.condition, scenario=scenario,
                                    scenario_info=scenario_info))
    except TimeoutError:
        print("aborted: not all seats connected", file=sys.stderr)
        return 1
    print(f"{game.game_id}\t{json.dumps(game.outcome, ensure_ascii=False)}")
    return 1 if game.aborted else 0


if __name__ == "__main__":
    sys.exit(main())
