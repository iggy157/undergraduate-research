"""single.base.build_messages and the CLI (dry-run / fake). No LLM is called."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from common import ROOT
from common.convert.single_markdown import convert
from common.logwriter import read_jsonl, read_log
from common.render import identity_block, shared_block
from common.setup import GameContext
from single.__main__ import main
from single.base import SHARED_BLOCKS, build_messages, canned_transcript, make_single_env

SETUPS = ["aiwolf_0001", "candidate_selection_0001", "shared_living_0001"]


@pytest.mark.parametrize("setup_id", SETUPS)
@pytest.mark.parametrize("info_mode", ["dynamic", "fixed"])
def test_build_messages_renders_and_embeds_shared_blocks(setup_id, info_mode):
    ctx = GameContext.load(setup_id)
    ctx.setup.info_mode = info_mode
    msgs = build_messages(ctx)  # StrictUndefined: any missing variable raises here
    assert [m["role"] for m in msgs] == ["system", "user"]
    system, user = msgs[0]["content"], msgs[1]["content"]
    # same split as multi (audit A3): system = writer note + identities + shared blocks (+ disclosure); user = request
    assert system.startswith("You are the writer of the discussion described below.")
    assert user.startswith("Write the complete transcript of the discussion in the exact Markdown format")
    env = make_single_env()
    for b in SHARED_BLOCKS:
        block = shared_block(env, ctx, b)
        assert block and block in system and block not in user, b
    for seat in range(1, 6):
        assert identity_block(env, ctx, seat) in system
    assert f"# {setup_id}" in user
    user = system + "\n\n" + user  # the content checks below only care that the text is somewhere in the prompt
    if ctx.domain == "aiwolf":
        assert "## For the writer only" not in user
        assert "| Seat |" not in user  # no Participants table: the participants are in the system prompt
        assert "- divine: <Seer's name>" in user
    else:
        assert "## Hidden information" in user
        assert "| Seat |" not in user
        for o in ctx.options():
            assert f"- {o['label']}: {o['name']}. {o['summary']}" in user
        assert f"{ctx.rules['option_noun'].capitalize()}s (see the schedule above):" in user
        if info_mode == "fixed":
            assert "Cards given to each participant (see the schedule above):" in user
            assert ctx.fixed_cards_of_seat(1)[0]["text"] in user
            assert "- investigate:" not in user
        else:
            assert "Cards (see the schedule above; title: text):" in user
            assert "- investigate: <Name> -> <card title>; <card title>" in user
    # DESIGN §7.2 order inside the system prompt: role, the shared blocks, then identities (seat order)
    pos = [system.index(shared_block(env, ctx, b)) for b in SHARED_BLOCKS]
    pos += [system.index(identity_block(env, ctx, seat)) for seat in range(1, 6)]
    assert pos == sorted(pos)


def test_shared_blocks_are_byte_identical_to_render_module():
    """What single embeds is exactly common.render.shared_block output (verify_prompt_control relies on it)."""
    ctx = GameContext.load("shared_living_0001")
    env = make_single_env()
    system = build_messages(ctx, env)[0]["content"]
    joined = "\n\n".join(shared_block(env, ctx, b) for b in SHARED_BLOCKS)
    assert joined in system
    assert system.index(joined) < system.index(identity_block(env, ctx, 1))


def test_dry_run_cli_writes_prompt_json(tmp_path: Path, capsys):
    rc = main(["--setup", "aiwolf_0001", "--log-dir", str(tmp_path), "--dry-run"])
    assert rc == 0
    files = list(tmp_path.glob("aiwolf/single-batch/aiwolf_0001__single-batch__dryrun__*/raw/prompt.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == build_messages(GameContext.load("aiwolf_0001"))
    assert not list(files[0].parent.parent.glob("*.log"))
    out = capsys.readouterr().out
    assert out.startswith("=== system ===\n") and "=== user ===" in out


def test_dry_run_module_entry_point(tmp_path: Path):
    p = subprocess.run([sys.executable, "-m", "single", "--setup", "candidate_selection_0001", "--info-mode", "fixed",
                        "--log-dir", str(tmp_path), "--dry-run"], cwd=ROOT, capture_output=True, text=True,
                       check=False)
    assert p.returncode == 0, p.stderr
    assert "# candidate_selection_0001" in p.stdout
    assert list(tmp_path.glob("candidate_selection/single-batch/*/raw/prompt.json"))


@pytest.mark.parametrize("setup_id,info_mode", [("aiwolf_0001", "dynamic"), ("candidate_selection_0001", "fixed"),
                                                ("shared_living_0001", "fixed")])
def test_fake_cli_writes_log_and_jsonl(tmp_path: Path, setup_id, info_mode, capsys):
    rc = main(["--setup", setup_id, "--log-dir", str(tmp_path), "--fake", "--info-mode", info_mode])
    assert rc == 0
    ctx = GameContext.load(setup_id)
    ctx.setup.info_mode = info_mode
    game_dirs = list(tmp_path.glob(f"{ctx.domain}/single-batch/{setup_id}__single-batch__fake__*"))
    assert len(game_dirs) == 1
    gd = game_dirs[0]
    gid = gd.name
    assert (gd / "raw" / "prompt.json").exists()
    assert (gd / "raw" / "transcript.md").read_text(encoding="utf-8") == canned_transcript(ctx)
    rows = read_log(gd / f"{gid}.log")
    expected = convert(canned_transcript(ctx), ctx, gid)
    assert expected.violations == []
    assert rows == expected.rows
    recs = list(read_jsonl(gd / f"{gid}.jsonl"))
    assert [r["kind"] for r in recs] == ["header", "llm_call", "violations"]
    h = recs[0]
    assert h["game_id"] == gid and h["setup_id"] == setup_id and h["domain"] == ctx.domain
    assert h["method"] == "single" and h["model"] == "fake" and h["model_tag"] == "fake" and h["info_mode"] == info_mode
    assert h["speaking_order"] == ctx.setup.speaking_order and h["outcome"] == expected.outcome
    assert [p["seat"] for p in h["participants"]] == [1, 2, 3, 4, 5]
    assert set(h["participants"][0]) == {"seat", "name", "role_slot", "persona", "private_seed"}
    assert set(h["participants"][0]["persona"]) == {"name", "age", "gender", "personality"}
    assert len(h["rules_hash"]) == 40
    if ctx.domain == "aiwolf":
        assert h["card_pool"] == [] and h["n_options"] == 0 and h["n_unique_cards"] == 0
    else:
        assert len(h["card_pool"]) == 10 and set(h["card_pool"][0]) == {"card_id", "title", "origin_seat"}
        assert h["n_options"] == len(ctx.options()) and h["n_unique_cards"] == 10
    assert h["setup_path"] == f"setups/{ctx.domain}/{setup_id}.json" and len(h["setup_sha1"]) == 40
    assert h["started_at"].endswith("+00:00") and h["finished_at"].endswith("+00:00")
    c = recs[1]
    assert c["seat"] == "writer" and c["request"] == "FULL" and c["seq"] == 0 and c["model"] == "fake"
    assert c["messages"] == build_messages(ctx) and c["response"] == canned_transcript(ctx)
    assert c["finish_reason"] == "stop" and c["truncated"] is False and c["error"] is None
    assert "usage" in c and "latency_ms" in c and c["ts"] == h["started_at"]
    assert recs[2]["items"] == []  # structural (converter) + common codes: the canned transcript is clean
    assert gid in capsys.readouterr().out


def test_dry_run_checks_dynamic_titles(tmp_path: Path, monkeypatch):
    """--dry-run goes through the same gate as a real run: dynamic mode without card titles is refused."""
    import common.setup as cs
    orig = cs.GameContext.card_pool

    def untitled(self):
        return [{**c, "title": ""} for c in orig(self)]
    monkeypatch.setattr(cs.GameContext, "card_pool", untitled)
    with pytest.raises(ValueError, match="needs card titles"):
        main(["--setup", "shared_living_0001", "--log-dir", str(tmp_path), "--dry-run"])
    monkeypatch.setattr(cs.GameContext, "card_pool", orig)
    assert main(["--setup", "shared_living_0001", "--log-dir", str(tmp_path), "--dry-run"]) == 0
    assert main(["--setup", "shared_living_0001", "--log-dir", str(tmp_path), "--dry-run", "--info-mode", "fixed"]) == 0
