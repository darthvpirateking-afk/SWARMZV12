"""
verification_store.py – Append-only verification log backed by
data/verification_log.jsonl.

Stores baseline snapshots and verification outcomes.  Also supports
querying outcomes by job_id or decision_id.
"""

import json
import os
import threading
from datetime import datetime, timezone

_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_DIR, "data", "verification_log.jsonl")


class VerificationStore:
    """Thread-safe, append-only verification log."""

    def __init__(self, data_path: str = _DATA_PATH):
        self._path = data_path
        self._lock = threading.Lock()

    def log(self, entry: dict) -> dict:
        """Append a verification entry with a timestamp."""
        entry.setdefault("time", datetime.now(timezone.utc).isoformat())
        with self._lock:
            with open(self._path, "a") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        return entry

    def read_all(self) -> list[dict]:
        """Return every verification entry."""
        if not os.path.exists(self._path):
            return []
        entries: list[dict] = []
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def find_by_job_id(self, job_id: str) -> list[dict]:
        """Return all entries matching *job_id*."""
        return [e for e in self.read_all() if e.get("job_id") == job_id]

    def find_by_decision_id(self, decision_id: str) -> list[dict]:
        """Return all entries matching *decision_id*."""
        return [e for e in self.read_all()
                if e.get("decision_id") == decision_id]

    def find_by_outcome(self, outcome: str) -> list[dict]:
        """Return all entries with a given outcome status."""
        return [e for e in self.read_all() if e.get("outcome") == outcome]
