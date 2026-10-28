"""Thin wrapper around ``python -m single`` (IMPLEMENTATION_NOTES §5).

usage: .venv/bin/python scripts/run_single.py --setup <id> --log-dir log [--model default] [--dry-run] [--fake]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from single.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
