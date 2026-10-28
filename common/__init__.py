"""ugr common package: protocol, log schema, setup loading, tie-break, prompt rendering."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("aiwolf", "candidate_selection", "shared_living")
METHODS = ("single", "multi")
LOG_DIRS = ("single-batch", "single-online", "multi-private", "multi-public", "single", "multi")  # conditions + legacy
