"""CLI: python -m single --setup <id> --log-dir log [--model default] [--dry-run] [--fake] [--info-mode M] [--scenario auto|PATH]

--dry-run   write raw/prompt.json only and print the prompt (no LLM call)
--fake      use FakeLLM with a canned valid transcript (no LLM call; model tag "fake")
--info-mode override the setup's info_mode (smoke tests of fixed mode while card titles are empty)
Exit code 0 on a completed run; prints one line: game_id and the outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common.scenario import (DEFAULT_GRANULARITY, GRANULARITIES, load_scenario, resolve_scenario, scenario_header,
                             scenario_view, validate_scenario)
from common.llm_meta import code_tree_sha1, served_info
from common.setup import GameContext

from .base import FakeLLM, OpenAIClient, canned_transcript, model_config, model_tag, run_single


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m single", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", required=True, help="setup_id or path to setups/<domain>/<id>.json")
    ap.add_argument("--log-dir", default="log")
    ap.add_argument("--model", default="default", help="entry under models: in config/models.yml")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"])
    ap.add_argument("--temperature", type=float, default=None, help="override models.yml (0 = greedy)")
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--scenario", default=None, help="S1: 'auto' = scenarios/<domain>/<setup_id>.json, or a path")
    ap.add_argument("--plan-granularity", choices=list(GRANULARITIES), default=None,
                    help=f"view of the plan to show (default {DEFAULT_GRANULARITY})")
    a = ap.parse_args(argv)

    ctx = GameContext.load(a.setup)
    if a.info_mode:
        ctx.setup.info_mode = a.info_mode
    ctx.check_dynamic_ready()  # dry-run / fake / real alike: empty card titles are reported, not rendered
    scenario = scenario_info = None
    if a.scenario is not None:
        sp = resolve_scenario(ctx, a.scenario)
        scenario = load_scenario(sp)
        errs = validate_scenario(scenario, ctx)
        if errs:
            print(f"scenario {sp}: " + "; ".join(errs), file=sys.stderr)
            return 2
        scenario = scenario_view(scenario, a.plan_granularity or DEFAULT_GRANULARITY)
        scenario_info = scenario_header(sp, scenario)
    mcfg, _ = model_config(a.model)
    max_tokens = int(mcfg["max_tokens"]["single_full"])

    if a.dry_run:
        run = run_single(ctx, None, Path(a.log_dir), model=str(mcfg["model"]), model_tag="dryrun",
                         max_tokens=max_tokens, dry_run=True, scenario=scenario, scenario_info=scenario_info)
        for m in run.messages:
            print(f"=== {m['role']} ===")
            print(m["content"])
        print(f"{run.game_id} prompt -> {run.game_dir / 'raw' / 'prompt.json'}", file=sys.stderr)
        return 0

    extra: dict = {}
    if a.fake:
        llm, model, tag = FakeLLM(canned_transcript(ctx)), "fake", "fake"
    else:
        llm = OpenAIClient.from_config(a.model, temperature=a.temperature, top_p=a.top_p, top_k=a.top_k)
        model, tag = llm.model, model_tag(llm.model)
        extra = {"sampling": llm.sampling(), **served_info(llm.base_url, llm.model, llm.api_key), "endpoint": llm.base_url,
                 "code_tree": code_tree_sha1()}
    run = run_single(ctx, llm, Path(a.log_dir), model=model, model_tag=tag, max_tokens=max_tokens,
                     header_extra=extra, scenario=scenario, scenario_info=scenario_info)
    print(f"{run.game_id} {json.dumps(run.outcome, ensure_ascii=False)} "
          f"violations={len(run.violations)} rows={len(run.rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
