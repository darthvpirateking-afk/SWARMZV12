"""
decision_logger.py – Append-only decision log backed by
data/decision_log.jsonl.

Records every scoring decision (including NO_ACTION) with timestamps,
score breakdowns, objective id, and config_hash.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_DIR, "data", "decision_log.jsonl")


class DecisionLogger:
    """Thread-safe, append-only decision logger."""

    def __init__(self, data_path: str = _DATA_PATH):
        self._path = data_path
        self._lock = threading.Lock()

    def log(self, entry: dict) -> dict:
        entry.setdefault("time", datetime.now(timezone.utc).isoformat())
        with self._lock:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "a") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        return entry

    def read_all(self) -> list[dict]:
        if not os.path.exists(self._path):
            return []
        entries: list[dict] = []
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries
