"""Server tests for shared_living (3 options, source: living)."""
from __future__ import annotations

from discussion_checks import run_dynamic, run_fixed, run_invalid_vote, run_tie

SETUP = "shared_living_0001"


def test_fixed_mode_real_data(log_dir):
    run = run_fixed(SETUP, log_dir)
    assert run.header["n_options"] == 3


def test_dynamic_mode_with_titles(log_dir):
    run = run_dynamic(SETUP, log_dir)
    assert run.header["domain"] == "shared_living"


def test_tie_break(log_dir):
    run_tie("shared_living_0003", log_dir)


def test_vote_label_forms(log_dir):
    run_invalid_vote(SETUP, log_dir)
