"""Run a batch of games (setups x conditions) over several vLLM instances with a shared job queue.

usage: .venv/bin/python scripts/run_queue.py --log-dir log/main_gemma31b --models default,default_b,default_c
           [--per-model 4] [--setups all | aiwolf | aiwolf_0004,...] [--conditions single-batch,...]
           [--port-base 20000] [--out-dir <dir for per-job stdout>] [--dry-run]

Jobs are (setup, condition) pairs; a job is skipped when <log-dir>/<domain>/*/<setup>__<condition>__*/*.log
already exists (completed or partial: remove the directory to rerun). Core conditions are queued first, plan
conditions (single-batch-process, multi-private-process) last; a plan job whose scenario file is missing is put back
at the end of the queue (scripts/gen_scenarios.py can run in parallel). Each model (= vLLM instance, config/models.yml)
gets --per-model worker threads; every worker uses its own game-server port. Progress goes to <out-dir>/progress.txt.
"""
from __future__ import annotations

import argparse
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common.setup import SETUPS  # noqa: E402

PY = str(ROOT / ".venv" / "bin" / "python")
CORE = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private"]
PLAN = ["single-batch-process", "multi-private-process"]
DOMAINS = ["aiwolf", "candidate_selection", "shared_living"]


def command(setup: str, cond: str, model: str, log_dir: str, port: int) -> list[str]:
    single = [PY, "scripts/run_single.py", "--setup", setup, "--log-dir", log_dir, "--model", model]
    multi = [PY, "scripts/run_multi.py", "--setup", setup, "--log-dir", log_dir, "--model", model, "--port", str(port)]
    return {
        "single-batch": single,
        "single-batch-stepped": multi + ["--stepped"],
        "single-online": multi + ["--writer"],
        "multi-public": multi + ["--reveal"],
        "multi-private": multi,
        "single-batch-process": single + ["--scenario", "auto", "--plan-granularity", "process"],
        "multi-private-process": multi + ["--scenario", "auto", "--plan-granularity", "process"],
    }[cond]


def done(log_dir: Path, setup: str, cond: str) -> bool:
    domain = setup.rsplit("_", 1)[0]
    for gd in (log_dir / domain).glob(f"*/{setup}__{cond}__*"):  # plan runs sit under the base condition's dir
        try:  # NFS: a directory listing can lag behind; creating and removing a file refreshes it
            (gd / ".refresh").touch()
            (gd / ".refresh").unlink()
        except OSError:
            pass
        if any(gd.glob("*.log")):
            return True
    return False


def scenario_ready(setup: str) -> bool:
    domain = setup.rsplit("_", 1)[0]
    return (ROOT / "scenarios" / domain / f"{setup}.json").exists()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--models", required=True, help="comma list of model names in config/models.yml")
    ap.add_argument("--per-model", type=int, default=4)
    ap.add_argument("--setups", default="all")
    ap.add_argument("--conditions", default=",".join(CORE + PLAN))
    ap.add_argument("--port-base", type=int, default=20000)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    log_dir = Path(a.log_dir)
    out_dir = Path(a.out_dir or (log_dir / "_queue"))
    out_dir.mkdir(parents=True, exist_ok=True)
    progress = out_dir / "progress.txt"

    if a.setups == "all":
        setups = [p.stem for d in DOMAINS for p in sorted((SETUPS / d).glob("*.json"))]
    elif a.setups in DOMAINS:
        setups = [p.stem for p in sorted((SETUPS / a.setups).glob("*.json"))]
    else:
        setups = a.setups.split(",")
    conds = a.conditions.split(",")
    jobs = [(s, c) for c in conds if c in CORE for s in setups] + [(s, c) for c in conds if c in PLAN for s in setups]
    jobs = [(s, c) for s, c in jobs if not done(log_dir, s, c)]
    print(f"{len(jobs)} jobs to run ({len(setups)} setups x {len(conds)} conditions, completed ones skipped)")
    if a.dry_run:
        for s, c in jobs[:10]:
            print("  ", s, c)
        return 0

    q: queue.Queue = queue.Queue()
    for j in jobs:
        q.put(j)
    lock = threading.Lock()
    remaining = [len(jobs)]

    def log(msg: str) -> None:
        with lock:
            with progress.open("a") as f:
                f.write(f"{datetime.now():%H:%M:%S} {msg}\n")

    def worker(model: str, idx: int, port: int) -> None:
        while True:
            try:
                setup, cond = q.get_nowait()
            except queue.Empty:
                return
            if cond in PLAN and not scenario_ready(setup):
                q.put((setup, cond))
                if q.qsize() <= 1:
                    time.sleep(60)  # nothing else to do: wait for the scenario generator
                else:
                    time.sleep(2)
                continue
            if done(log_dir, setup, cond):
                remaining[0] -= 1
                continue
            cmd = command(setup, cond, model, str(log_dir), port)
            t0 = time.time()
            with (out_dir / f"{setup}__{cond}.out").open("w") as f:
                rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
            with lock:
                remaining[0] -= 1
                left = remaining[0]
            log(f"{cond} {setup} rc={rc} {time.time() - t0:.0f}s [{model}#{idx}] left={left}")

    log(f"start: {len(jobs)} jobs, models={a.models}, per_model={a.per_model}")
    threads = []
    k = 0
    for model in a.models.split(","):
        for i in range(a.per_model):
            t = threading.Thread(target=worker, args=(model, i, a.port_base + k), daemon=True)
            t.start()
            threads.append(t)
            k += 1
            time.sleep(1)
    for t in threads:
        t.join()
    log("all done")
    (out_dir / "queue.done").touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
