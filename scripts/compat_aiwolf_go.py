"""Compatibility check: Go aiwolf-nlp-server vs the Python server, same scripted agents (DESIGN §4.5-8).

usage: .venv/bin/python scripts/compat_aiwolf_go.py [--go-only | --py-only] [--work-dir DIR]
           [--go-bin PATH] [--go-base-config PATH] [--go-port 18081] [--py-port 18000]
           [--setup aiwolf_0001] [--seed 20261027] [--timeout 120]

What it does
  (a) Go side: derives a 5-player config from the manyshot-ablation ``server_en_scaf_base.yml``
      (max_day 3, 4 talks per agent per day, length limits 10000, max_skip 100, custom_profile on,
      self_match with team_count 5 / game_count 1, loggers into <work-dir>/go), starts the Go binary
      with ``AIWOLF_SEED`` fixed, connects five ``tests/scripted_agent.py`` agents named
      ``scripted1..5`` (the Go server strips trailing digits -> one team, self-matched) and waits for
      the game log + json. The agents stay silent on notices for Go (it never reads those replies),
      while the Python server gets the usual "Acknowledged.".
  (b) Python side: ``python -m server --setup <setup> --port <py-port> --log-dir <work-dir>/py`` with
      the same five scripted agents (names ``seat1..5``).
  (c) Converts the Go logs with ``common.convert.aiwolf_go.convert`` (context built from the Go
      status lines, since Go shuffles roles / personas) and compares them with the Python ``.log``
      *structurally*: per day and turn the number of talk rows and the pass tokens, the number of
      valid / invalid votes per day, the action kinds per day (divine / execute / attack), the alive
      counts per status block and the winner. Talk texts are compared per (day, turn) as multisets
      after masking persona names and normalising the whitespace around ``@mentions`` (Go's
      ``processText`` re-spaces them). Seat / persona assignment differences are ignored by design.

Known, expected differences (printed as such, not counted as failures):
  * ``skip.`` / ``Over.`` (case / punctuation variants) are *talk* rows for Go and *pass* rows for
    the Python server (DESIGN §4.5-5 normalises them; the violation code ``pass_punct`` records it).
  * Go keeps asking a seat after ``Over.`` (a talk for Go) and after an empty reply (Go logs
    ``Over`` but zeroes the remain count only for a literal ``Over``, see ``processSkipOver`` vs
    ``processText``); the Python server ends that seat's round. The extra Go talk rows on later
    turns are annotated.
  * Go writes nothing for an invalid vote; the invalid rows on the Go side are recovered from the
    JSON log, so the counts are comparable only when the JSON log exists.
  * Unless ``--setup`` is given, the Python side plays a setup derived from the Go assignment
    (``<work-dir>/aiwolf_9999.json``: idx -> persona / role, day-0 talk order), so that the scripted
    votes / divines / attacks produce the same trajectory and the winner / alive counts / night
    actions are comparable. With an explicit ``--setup`` those are tagged ``(assignment-dependent)``.

Exit codes: 0 = no unexpected difference, 2 = differences found, 1 = a server could not be run
(the Go binary not starting is reported, not treated as a code failure). ``--go-only`` /
``--py-only`` run one side and print its structure summary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from scripted_agent import NO_REPLY, ScriptedAgent

from common.convert import aiwolf_go
from common.logwriter import read_log
from common.protocol import NOTICE_REQUESTS
from common.schema import LogRow
from common.setup import GameContext

GO_BIN = Path("/diskthalys/ssd14ta/yharada/inlg/discussion-bench/server/aiwolf/aiwolf-server")
GO_BASE = Path("/diskthalys/ssd14ta/yharada/aiwolf/naacl/2027/manyshot-ablation/config/factor/server_en_scaf_base.yml")
EXPECTED_PASS_VARIANTS = ("skip.", "Over.")


# ---- scripted agents ---------------------------------------------------------------------------
class GoScriptedAgent(ScriptedAgent):
    """Same behaviour, but no reply to notices (the Go server does not read them)."""

    def handle(self, d: dict[str, Any]) -> Any:
        out = super().handle(d)
        if d["request"] in NOTICE_REQUESTS:
            return NO_REPLY
        return out

    def run(self) -> GoScriptedAgent:
        super().run()
        # Go closes the socket right after FINISH; the resulting recv error is not a failure
        if self.error is not None and self.packets and self.packets[-1].get("request") == "FINISH":
            self.error = None
        return self


def setup_from_go_log(csv_text: str, path: Path, setup_id: str = "aiwolf_9999") -> Path:
    """Write a Python setup mirroring the Go assignment (idx -> persona, role; day-0 talk order)."""
    days = aiwolf_go.parse_csv(csv_text)
    order: list[int] = []
    for cols in days[min(days)].talks:
        idx = int(cols[4])
        if idx not in order:
            order.append(idx)
    order += [i for i in range(1, 6) if i not in order]
    ctx = aiwolf_go.context_from_log(csv_text, setup_id=setup_id, speaking_order=order)
    path.write_text(json.dumps(ctx.setup.to_dict(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def run_agents(url: str, cls: type[ScriptedAgent], names: dict[int, str], join_timeout: float,
               log_dir: Path | None = None) -> list[ScriptedAgent]:
    agents = [cls(url, s, name=names[s], log_dir=log_dir, recv_timeout=join_timeout) for s in range(1, 6)]
    threads = [threading.Thread(target=a.run, daemon=True) for a in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join(join_timeout)
    return agents


# ---- Go side -----------------------------------------------------------------------------------
def go_config(base: Path, port: int, out_dir: Path) -> dict[str, Any]:
    c = yaml.safe_load(base.read_text(encoding="utf-8"))
    c["server"]["web_socket"] = {"host": "127.0.0.1", "port": port}
    c["server"]["authentication"] = {"enable": False}
    c["server"]["timeout"] = {"action": "60s", "response": "90s", "acceptable": "5s"}
    g = c["game"]
    g["agent_count"] = 5
    g["max_day"] = 3
    g["talk"]["max_count"] = {"per_agent": 4, "per_day": 20}
    g["talk"]["max_length"] = {"count_in_word": True, "count_spaces": False, "per_talk": 10000,
                               "mention_length": 10000, "per_agent": 100000, "base_length": 10000}
    g["talk"]["max_skip"] = 100
    g["vote"] = {"max_count": 1, "allow_self_vote": True}
    g["attack_vote"] = {"max_count": 1, "allow_self_vote": True, "allow_no_target": False}
    c["matching"] = {"self_match": True, "is_optimize": False, "team_count": 5, "game_count": 1,
                     "output_path": str(out_dir / "match_optimizer.json"), "infinite_loop": False}
    c["custom_profile"]["enable"] = True
    c["custom_profile"]["dynamic_profile"]["enable"] = False
    c["json_logger"] = {"enable": True, "output_dir": str(out_dir / "json"), "filename": "{timestamp}_{teams}"}
    c["game_logger"] = {"enable": True, "output_dir": str(out_dir / "log"), "filename": "{timestamp}_{teams}"}
    c["realtime_broadcaster"]["enable"] = False
    c["tts_broadcaster"]["enable"] = False
    return c


def run_go(go_bin: Path, base: Path, port: int, work: Path, seed: int, timeout: float,
           ) -> tuple[Path, Path | None] | None:
    out = work / "go"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cfg = out / "server.yml"
    cfg.write_text(yaml.safe_dump(go_config(base, port, out), allow_unicode=True, sort_keys=False), encoding="utf-8")
    env = {**os.environ, "AIWOLF_SEED": str(seed)}
    env.pop("LOG_ROOT", None)
    with open(out / "server.stderr", "w", encoding="utf-8") as stderr:
        proc = subprocess.Popen([str(go_bin), "-c", str(cfg)], cwd=str(out), env=env,
                                stdout=stderr, stderr=subprocess.STDOUT)
        return _drive_go(proc, out, port, timeout)


def _drive_go(proc: subprocess.Popen, out: Path, port: int, timeout: float) -> tuple[Path, Path | None] | None:
    try:
        time.sleep(1.0)
        if proc.poll() is not None:
            print(f"[go] server exited immediately with code {proc.returncode}; see {out / 'server.stderr'}")
            return None
        names = {s: f"scripted{s}" for s in range(1, 6)}
        agents = run_agents(f"ws://127.0.0.1:{port}/ws", GoScriptedAgent, names, timeout)
        errs = [(a.seat, a.error) for a in agents if a.error]
        if errs:
            print(f"[go] agent errors: {errs}")
        deadline = time.monotonic() + 30
        log = js = None
        while time.monotonic() < deadline:
            logs = sorted((out / "log").glob("*.log")) if (out / "log").exists() else []
            if logs and "result" in logs[-1].read_text(encoding="utf-8"):
                log = logs[-1]
                jss = sorted((out / "json").glob("*.json")) if (out / "json").exists() else []
                js = jss[-1] if jss else None
                break
            time.sleep(0.5)
        if log is None:
            print(f"[go] no finished game log under {out / 'log'}; see {out / 'server.stderr'}")
            return None
        return log, js
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()


# ---- Python side ---------------------------------------------------------------------------------
def run_py(setup: str, port: int, work: Path, timeout: float) -> Path | None:
    out = work / "py"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    with open(out / "server.stderr", "w", encoding="utf-8") as stderr:
        proc = subprocess.Popen([sys.executable, "-m", "server", "--setup", setup, "--port", str(port),
                                 "--log-dir", str(out), "--timeout", str(int(timeout)), "--model-tag", "scripted"],
                                cwd=str(ROOT), stdout=subprocess.PIPE, stderr=stderr, text=True)
        return _drive_py(proc, out, port, timeout)


def _drive_py(proc: subprocess.Popen, out: Path, port: int, timeout: float) -> Path | None:
    try:
        time.sleep(1.0)
        if proc.poll() is not None:
            print(f"[py] server exited immediately with code {proc.returncode}; see {out / 'server.stderr'}")
            return None
        names = {s: f"seat{s}" for s in range(1, 6)}
        agents = run_agents(f"ws://127.0.0.1:{port}", ScriptedAgent, names, timeout, log_dir=out)
        errs = [(a.seat, a.error) for a in agents if a.error]
        if errs:
            print(f"[py] agent errors: {errs}")
        try:
            stdout, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()
        print(f"[py] server exit {proc.returncode}: {stdout.strip()}")
        logs = sorted(out.glob("aiwolf/multi/*/*.log"))
        if not logs:
            print(f"[py] no .log under {out}; see {out / 'server.stderr'}")
            return None
        return logs[-1]
    finally:
        if proc.poll() is None:
            proc.kill()


# ---- structure summary and comparison -------------------------------------------------------------
def mask(text: str, names: list[str]) -> str:
    for n in sorted(names, key=len, reverse=True):
        text = re.sub(r"\s*@" + re.escape(n) + r"\b\s*", " @NAME ", text)
        text = re.sub(r"\b" + re.escape(n) + r"\b", "NAME", text)
    return " ".join(text.split())


def summarize(rows: list[LogRow], names: list[str]) -> dict[str, Any]:
    s: dict[str, Any] = {"talks": Counter(), "passes": defaultdict(Counter), "votes": defaultdict(Counter),
                         "actions": defaultdict(list), "alive": {}, "texts": defaultdict(Counter),
                         "winner": None, "pass_variants": Counter(), "quirk_talks": Counter()}
    # Go quirk: a seat that answered "Over." (a talk for Go) or "" (logged Over, but the remain count
    # is not zeroed) is asked again on later turns; Python ends that seat's round. (day, agent) -> turn
    quirk_since: dict[tuple[int, str], int] = {}
    for r in rows:
        if r.type == "talk":
            s["talks"][(r.round, r.turn)] += 1
            key = (r.round, r.agent)
            if key in quirk_since and quirk_since[key] < (r.turn or 0):
                s["quirk_talks"][(r.round, r.turn)] += 1
            else:
                s["texts"][(r.round, r.turn)][mask(r.text, names)] += 1
            if r.text.strip() in EXPECTED_PASS_VARIANTS:
                s["pass_variants"][(r.round, r.turn, r.text.strip())] += 1
                if r.text.strip().lower().startswith("over"):
                    quirk_since.setdefault(key, r.turn or 0)
        elif r.type == "pass":
            s["passes"][(r.round, r.turn)][r.text] += 1
            if r.extra.get("raw") in EXPECTED_PASS_VARIANTS:
                s["pass_variants"][(r.round, r.turn, r.extra["raw"])] += 1
            if r.text == "Over" and r.extra.get("empty"):
                quirk_since.setdefault((r.round, r.agent), r.turn or 0)
        elif r.type == "vote":
            s["votes"][r.round]["valid" if r.extra.get("valid") else "invalid"] += 1
        elif r.type == "action":
            s["actions"][r.round].append(r.extra.get("action"))
        elif r.type == "status":
            s["alive"].setdefault(r.round, 0)
            s["alive"][r.round] += int(bool(r.extra.get("alive")))
        elif r.type == "result":
            s["winner"] = r.text
    return s


def print_summary(tag: str, s: dict[str, Any]) -> None:
    print(f"--- {tag}")
    days = sorted({k[0] for k in s["talks"]} | set(s["votes"]) | set(s["actions"]) | set(s["alive"]))
    for d in days:
        talks = {t: s["talks"][(d, t)] for t in range(1, 5) if s["talks"][(d, t)]}
        passes = {t: dict(s["passes"][(d, t)]) for t in range(1, 5) if s["passes"][(d, t)]}
        print(f"day {d}: alive={s['alive'].get(d)} talks/turn={talks} passes/turn={passes} "
              f"votes={dict(s['votes'][d])} actions={s['actions'][d]}")
    print(f"winner={s['winner']}  expected pass variants seen as: {dict(s['pass_variants'])}")


def compare(go: dict[str, Any], py: dict[str, Any], same_assignment: bool = True) -> list[str]:
    diffs: list[str] = []
    keys = set(go["talks"]) | set(py["talks"]) | set(go["passes"]) | set(py["passes"])
    for k in sorted(keys):
        gt, pt = go["talks"][k], py["talks"][k]
        gp, pp = go["passes"][k], py["passes"][k]
        if gt != pt or gp != pp:
            # expected: Go keeps "skip." / "Over." as talk rows (Python: pass rows), and keeps asking a
            # seat after "Over." / an empty reply (Python: that seat's round is over)
            exp = sum(v for (d, t, _), v in go["pass_variants"].items() if (d, t) == k)
            quirk = go["quirk_talks"][k]
            if gt - exp - quirk == pt and sum(gp.values()) + exp == sum(pp.values()):
                diffs.append(f"(expected) day {k[0]} turn {k[1]}: {exp} punctuated pass token(s) are talk rows in Go"
                             f"{f', {quirk} extra Go talk(s) after Over./empty' if quirk else ''}")
            else:
                diffs.append(f"day {k[0]} turn {k[1]}: talks go={gt} py={pt}; passes go={dict(gp)} py={dict(pp)}")
        gtexts = Counter({t: n for t, n in go["texts"][k].items() if t not in EXPECTED_PASS_VARIANTS})
        ptexts = Counter({t: n for t, n in py["texts"][k].items() if t not in EXPECTED_PASS_VARIANTS})
        if gtexts != ptexts:
            only_go = list((gtexts - ptexts).elements())[:3]
            only_py = list((ptexts - gtexts).elements())[:3]
            diffs.append(f"day {k[0]} turn {k[1]}: talk texts differ; only go={only_go} only py={only_py}")
    for d in sorted(set(go["votes"]) | set(py["votes"])):
        if go["votes"][d] != py["votes"][d]:
            diffs.append(f"day {d}: votes go={dict(go['votes'][d])} py={dict(py['votes'][d])}")
    # the rest depends on who holds which role; identical only when the Python setup mirrors Go's
    tag = "" if same_assignment else "(assignment-dependent) "
    for d in sorted(set(go["actions"]) | set(py["actions"])):
        if sorted(go["actions"][d]) != sorted(py["actions"][d]):
            diffs.append(f"{tag}day {d}: actions go={go['actions'][d]} py={py['actions'][d]}")
    for d in sorted(set(go["alive"]) | set(py["alive"])):
        if go["alive"].get(d) != py["alive"].get(d):
            diffs.append(f"{tag}day {d}: alive go={go['alive'].get(d)} py={py['alive'].get(d)}")
    if go["winner"] != py["winner"]:
        diffs.append(f"{tag}winner go={go['winner']} py={py['winner']}")
    return diffs


# ---- main --------------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--go-only", action="store_true")
    g.add_argument("--py-only", action="store_true")
    ap.add_argument("--work-dir", default=None, help="default: $TMPDIR-like scratch under log/_compat")
    ap.add_argument("--go-bin", default=str(GO_BIN))
    ap.add_argument("--go-base-config", default=str(GO_BASE))
    ap.add_argument("--go-port", type=int, default=18081)
    ap.add_argument("--py-port", type=int, default=18000)
    ap.add_argument("--setup", default=None,
                    help="Python setup id/path. Default: a setup derived from the Go assignment when the "
                         "Go side ran (so both sides play the same roles/personas), else aiwolf_0001")
    ap.add_argument("--seed", type=int, default=20261027)
    ap.add_argument("--timeout", type=float, default=120.0)
    a = ap.parse_args(argv)
    work = Path(a.work_dir) if a.work_dir else ROOT / "log" / "_compat"
    work.mkdir(parents=True, exist_ok=True)

    go_summary = py_summary = None
    py_setup = a.setup
    same_assignment = False
    if not a.py_only:
        go_bin = Path(a.go_bin)
        if not go_bin.is_file() or not os.access(go_bin, os.X_OK):
            print(f"[go] binary not found / not executable: {go_bin}")
            return 1
        res = run_go(go_bin, Path(a.go_base_config), a.go_port, work, a.seed, a.timeout)
        if res is None:
            return 1
        log, js = res
        csv_text = log.read_text(encoding="utf-8")
        server_json = json.loads(js.read_text(encoding="utf-8")) if js else None
        ctx = aiwolf_go.context_from_log(csv_text)
        go_rows = aiwolf_go.convert(csv_text, server_json, ctx)
        from common.logwriter import write_rows
        write_rows(work / "go" / "converted.log", go_rows)
        go_summary = summarize(go_rows, ctx.names)
        print_summary(f"Go server ({log.name}, json={'yes' if js else 'no'})", go_summary)
        if py_setup is None:
            py_setup = str(setup_from_go_log(csv_text, work / "aiwolf_9999.json"))
            same_assignment = True
            print(f"[py] setup derived from the Go assignment: {py_setup}")
    if not a.go_only:
        py_setup = py_setup or "aiwolf_0001"
        log = run_py(py_setup, a.py_port, work, a.timeout)
        if log is None:
            return 1
        py_rows = read_log(log)
        py_summary = summarize(py_rows, GameContext.load(py_setup).names)
        print_summary(f"Python server ({log.name})", py_summary)
    if go_summary is None or py_summary is None:
        return 0
    diffs = compare(go_summary, py_summary, same_assignment)
    print("--- diff report")
    if not diffs:
        print("no differences")
        return 0
    for d in diffs:
        print(d)
    unexpected = [d for d in diffs if not d.startswith("(")]
    print(f"{len(unexpected)} unexpected difference(s), {len(diffs) - len(unexpected)} expected")
    return 2 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
