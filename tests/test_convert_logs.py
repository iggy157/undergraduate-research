"""scripts/convert_logs.py: the violations record is rebuilt without losing structural items (DESIGN §3.2, §8)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from common import ROOT
from common.logwriter import read_jsonl
from common.setup import GameContext
from single.base import FakeLLM, canned_transcript, run_single

_spec = importlib.util.spec_from_file_location("convert_logs", ROOT / "scripts" / "convert_logs.py")
convert_logs = importlib.util.module_from_spec(_spec)
sys.modules["convert_logs"] = convert_logs
_spec.loader.exec_module(convert_logs)


def _single_game(tmp_path: Path, setup_id: str, info_mode: str):
    ctx = GameContext.load(setup_id)
    ctx.setup.info_mode = info_mode
    run = run_single(ctx, FakeLLM(canned_transcript(ctx)), tmp_path, model="fake", model_tag="fake", max_tokens=10)
    return ctx, run


def _rewrite_violations(jsonl: Path, items: list[dict]) -> None:
    recs = [r for r in read_jsonl(jsonl) if r["kind"] != "violations"]
    recs.append({"kind": "violations", "items": items})
    jsonl.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")


def test_single_run_writes_one_merged_violations_record(tmp_path: Path):
    ctx, run = _single_game(tmp_path, "aiwolf_0001", "dynamic")
    recs = list(read_jsonl(run.game_dir / f"{run.game_id}.jsonl"))
    assert [r["kind"] for r in recs] == ["header", "llm_call", "violations"]
    assert recs[2]["items"] == [] and run.violations == []


def test_process_keeps_structural_items_and_recomputes_common(tmp_path: Path):
    ctx, run = _single_game(tmp_path, "candidate_selection_0001", "fixed")
    jsonl = run.game_dir / f"{run.game_id}.jsonl"
    structural = [{"seq": None, "line": 3, "code": "format_noise", "detail": "code fence around the document"},
                  {"seq": None, "line": None, "code": "llm_error", "detail": "boom"},
                  {"seq": 9, "line": 40, "code": "dead_actor", "detail": "x votes"}]
    stale = [{"seq": 7, "code": "over_cap", "detail": {"words": 99, "cap": 40}},
             {"seq": None, "line": None, "code": "truncated", "detail": "finish_reason=length"}]
    _rewrite_violations(jsonl, structural + stale)
    summary, talks = convert_logs.process(run.game_dir, run.game_dir / f"{run.game_id}.log", dry_run=False)
    recs = list(read_jsonl(jsonl))
    assert [r["kind"] for r in recs] == ["header", "llm_call", "violations"]
    assert recs[2]["items"] == structural  # stale common items dropped, canned rows are clean
    assert summary["over_cap"] == 0 and summary["truncated"] == 0 and summary["format_noise"] == 1
    assert talks == sum(1 for r in run.rows if r.type == "talk")
    # idempotent
    convert_logs.process(run.game_dir, run.game_dir / f"{run.game_id}.log", dry_run=False)
    assert list(read_jsonl(jsonl))[2]["items"] == structural
    # dry run touches nothing
    _rewrite_violations(jsonl, stale)
    convert_logs.process(run.game_dir, run.game_dir / f"{run.game_id}.log", dry_run=True)
    assert list(read_jsonl(jsonl))[2]["items"] == stale


def test_context_follows_header_info_mode(tmp_path: Path):
    """A game run with --info-mode fixed on a dynamic setup file is checked as fixed."""
    ctx, run = _single_game(tmp_path, "shared_living_0001", "fixed")
    assert GameContext.load("shared_living_0001").setup.info_mode == "dynamic"
    recs = list(read_jsonl(run.game_dir / f"{run.game_id}.jsonl"))
    assert recs[0]["info_mode"] == "fixed"
    assert convert_logs.context_of(run.game_dir, recs).setup.info_mode == "fixed"
    assert convert_logs.context_of(run.game_dir, []).setup.info_mode == "dynamic"


def test_main_runs_over_a_log_dir(tmp_path: Path, capsys):
    _single_game(tmp_path, "aiwolf_0001", "dynamic")
    assert convert_logs.main(["--log-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "TOTAL (1 games)" in out and "trailing_over" in out and "early_reveal_partial" in out


@pytest.mark.parametrize("setup_id", ["aiwolf_0001", "shared_living_0001"])
def test_setup_provenance_in_header(tmp_path: Path, setup_id: str):
    ctx, run = _single_game(tmp_path, setup_id, "fixed")
    h = list(read_jsonl(run.game_dir / f"{run.game_id}.jsonl"))[0]
    assert h["setup_path"] == f"setups/{ctx.domain}/{setup_id}.json"
    import hashlib
    assert h["setup_sha1"] == hashlib.sha1((ROOT / h["setup_path"]).read_bytes()).hexdigest()
