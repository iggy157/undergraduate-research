"""Server tests for candidate_selection (4 options, source: panel)."""
from __future__ import annotations

from discussion_checks import run_dynamic, run_fixed, run_invalid_vote, run_tie

SETUP = "candidate_selection_0001"


def test_fixed_mode_real_data(log_dir):
    run = run_fixed(SETUP, log_dir)
    assert run.header["n_options"] == 4


def test_dynamic_mode_with_titles(log_dir):
    run = run_dynamic(SETUP, log_dir)
    assert run.header["domain"] == "candidate_selection"


def test_tie_break(log_dir):
    run_tie("candidate_selection_0002", log_dir)


def test_vote_label_forms(log_dir):
    run_invalid_vote(SETUP, log_dir)
