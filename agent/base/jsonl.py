"""Append-only jsonl for the per-seat raw record file (<game_id>/raw/agent.<seat>.jsonl)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class RawJsonlWriter:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(self.path, "a", encoding="utf-8")  # noqa: SIM115 - kept open for appends

    def write(self, record: dict[str, Any]) -> None:
        self._f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._f.flush()

    def close(self) -> None:
        if not self._f.closed:
            self._f.close()
