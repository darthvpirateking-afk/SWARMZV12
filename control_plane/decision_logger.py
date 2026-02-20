# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
decision_logger.py â€“ Append-only decision log backed by data/decision_log.jsonl.

Records every scoring decision (including NO_ACTION) with a timestamp.
"""

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
        """Append *entry* (with an added timestamp) to the decision log."""
        entry.setdefault("time", datetime.now(timezone.utc).isoformat())
        with self._lock:
            with open(self._path, "a") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        return entry

    def read_all(self) -> list[dict]:
        """Return every logged decision."""
        if not os.path.exists(self._path):
            return []
        entries: list[dict] = []
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

