"""Start the server and the agents for one setup, wait for the game to end.

usage: .venv/bin/python scripts/run_multi.py --setup <setup_id> [--port 10000] [--model default] [--log-dir log] [--fake]
                                            [--info-mode dynamic|fixed] [--reveal] [--writer] [--stepped] [--scenario auto|PATH] [--plan-granularity process|outcome|outline|turn]
                                            [--temperature T] [--top-p P] [--top-k K]

Conditions (DESIGN §13 / common.conditions): none = multi-private; ``--reveal`` = multi-public; ``--scenario auto`` =
+ plan (process may go with private; the others need ``--reveal``); ``--writer`` = single-online; ``--stepped`` =
single-batch-stepped (both: one agent process runs the five seats as threads sharing the writer view). ``--info-mode`` is forwarded to
the server and to the agents. The server gets ``--model-tag`` / ``--model`` (for the jsonl header), ``--condition``
and ``--scenario`` (deviations are recorded in the violations record).

Exits with the server's exit code; the server's stdout (the game_id / result line) is relayed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.base.llm import ModelConfig, load_model_config, timeout_for
from common.llm_meta import code_tree_sha1, served_info
from common.conditions import PRIVATE_SAFE_PLANS, multi_tag
from common.scenario import DEFAULT_GRANULARITY, GRANULARITIES


def models_yml_sha1() -> str:
    import hashlib
    p = ROOT / "config" / "models.yml"
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else ""


def served_model_info(cfg: ModelConfig) -> dict | None:
    """``GET /v1/models`` entry of the served model (id, root, max_model_len ...), best effort."""
    try:
        from openai import OpenAI
        client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=10, max_retries=0)
        for m in client.models.list().data:
            if getattr(m, "id", None) == cfg.model:
                return m.model_dump() if hasattr(m, "model_dump") else dict(m)
    except Exception:  # noqa: BLE001 - informational only
        return None
    return None


def condition_of(reveal: bool, writer: bool, stepped: bool, scenario: bool, granularity: str = DEFAULT_GRANULARITY) -> str:
    return multi_tag(reveal=reveal, writer=writer, stepped=stepped, plan=granularity if scenario else None)


def _relay(proc: subprocess.Popen, lines: list[str]) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        lines.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--setup", required=True)
    ap.add_argument("--port", type=int, default=10000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--model", default="default")
    ap.add_argument("--log-dir", default="log")
    ap.add_argument("--fake", action="store_true", help="agents use the canned FakeLLM")
    ap.add_argument("--timeout", type=int, default=None, help="server --timeout seconds")
    ap.add_argument("--server-start-delay", type=float, default=1.0)
    ap.add_argument("--temperature", type=float, default=None, help="override models.yml for the agents (0 = greedy)")
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--info-mode", choices=["dynamic", "fixed"], default=None,
                    help="override the setup's info_mode for the server and the agents")
    ap.add_argument("--reveal", action="store_true", help="M1: every seat sees all participants + hidden information")
    ap.add_argument("--writer", action="store_true", help="S-online: one writer LLM writes every seat's line")
    ap.add_argument("--stepped", action="store_true", help="single-batch-stepped: the batch prompt continued one line per call")
    ap.add_argument("--scenario", default=None, help="'auto' or a path: give the plan (all but process imply reveal)")
    ap.add_argument("--plan-granularity", choices=list(GRANULARITIES), default=DEFAULT_GRANULARITY,
                    help="view of the plan: process | outcome | outline | turn")
    a = ap.parse_args(argv)
    if a.scenario is not None and a.plan_granularity not in PRIVATE_SAFE_PLANS and not (a.reveal or a.writer or a.stepped):
        ap.error(f"a {a.plan_granularity} plan names the outcome: add --reveal (multi-public) or use --plan-granularity process")
    if a.writer and a.stepped:
        ap.error("--writer and --stepped are different conditions")

    py = sys.executable
    header_extra: dict = {}
    if a.fake:
        model_tag = model_name = "fake"
    else:
        mcfg = load_model_config(a.model, temperature=a.temperature, top_p=a.top_p, top_k=a.top_k)
        model_tag, model_name = mcfg.model_tag, mcfg.model
        header_extra = {"sampling": mcfg.sampling(), **served_info(mcfg.base_url, mcfg.model, mcfg.api_key),
                        "endpoint": mcfg.base_url, "models_yml_sha1": models_yml_sha1(), "code_tree": code_tree_sha1()}
    condition = condition_of(a.reveal, a.writer, a.stepped, a.scenario is not None, a.plan_granularity)
    server_cmd = [py, "-m", "server", "--setup", a.setup, "--port", str(a.port), "--log-dir", a.log_dir,
                  "--model-tag", model_tag, "--model", model_name]
    if header_extra:
        server_cmd += ["--header-extra", json.dumps(header_extra, ensure_ascii=False)]
    if a.info_mode:
        server_cmd += ["--info-mode", a.info_mode]
    server_cmd += ["--condition", condition]
    if a.scenario is not None:
        server_cmd += ["--scenario", a.scenario, "--plan-granularity", a.plan_granularity]
    # The server's per-request timeout must exceed the agent's LLM timeout, otherwise a late LLM reply
    # would be consumed as the answer to the next request (the protocol is strictly request/response).
    timeout = a.timeout if a.timeout is not None else int(
        (30 if a.fake else timeout_for(_model_entry(a.model), "multi")) + 60)
    server_cmd += ["--timeout", str(timeout)]
    if header_extra:
        header_extra["server_timeout_s"] = timeout
        server_cmd[server_cmd.index("--header-extra") + 1] = json.dumps(header_extra, ensure_ascii=False)
    server = subprocess.Popen(server_cmd, cwd=ROOT, stdout=subprocess.PIPE, text=True, bufsize=1)
    out_lines: list[str] = []
    th = threading.Thread(target=_relay, args=(server, out_lines), daemon=True)
    th.start()
    time.sleep(a.server_start_delay)

    url = f"ws://{a.host}:{a.port}"
    common = ["--setup", a.setup, "--log-dir", a.log_dir, "--model", a.model, "--url", url]
    if a.fake:
        common.append("--fake")
    if a.info_mode:
        common += ["--info-mode", a.info_mode]
    if a.temperature is not None:
        common += ["--temperature", str(a.temperature)]
    if a.top_p is not None:
        common += ["--top-p", str(a.top_p)]
    if a.top_k is not None:
        common += ["--top-k", str(a.top_k)]
    if a.scenario is not None:
        common += ["--scenario", a.scenario, "--plan-granularity", a.plan_granularity]
    agents: list[subprocess.Popen] = []
    if a.writer or a.stepped:
        flag = "--writer" if a.writer else "--stepped"
        agents.append(subprocess.Popen([py, "-m", "agent", "--seats", "all", flag, *common], cwd=ROOT))
    else:
        for seat in range(1, 6):
            cmd = [py, "-m", "agent", "--seat", str(seat), *common]
            if a.reveal:
                cmd.append("--reveal")
            agents.append(subprocess.Popen(cmd, cwd=ROOT))

    try:
        rc = server.wait()
        for p in agents:
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill()
    except KeyboardInterrupt:
        for p in [server] + agents:
            p.terminate()
        rc = 130
    th.join(timeout=5)
    game_lines = [ln for ln in out_lines if f"__{condition}__" in ln]
    if game_lines:
        sys.stderr.write(f"run_multi: {game_lines[-1].strip()}\n")
    agent_rcs = [p.returncode for p in agents]
    if any(r not in (0, None) for r in agent_rcs):
        sys.stderr.write(f"run_multi: agent exit codes {agent_rcs}\n")
    return rc


def _model_entry(name: str) -> dict:
    from common.setup import load_models
    return dict(load_models()["models"][name])


if __name__ == "__main__":
    raise SystemExit(main())
