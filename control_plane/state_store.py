# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
state_store.py â€“ Append-only state store backed by data/state.jsonl.

Every state update is validated against schemas/state.schema.json and appended
to the JSONL file.  The in-memory index provides O(1) latest-value lookups.
"""

import json
import os
import threading


import jsonschema

_DIR = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_PATH = os.path.join(_DIR, "schemas", "state.schema.json")
_DATA_PATH = os.path.join(_DIR, "data", "state.jsonl")

with open(_SCHEMA_PATH) as _f:
    _SCHEMA = json.load(_f)


class StateStore:
    """Thread-safe, append-only state store."""

    def __init__(self, data_path: str = _DATA_PATH):
        self._path = data_path
        self._lock = threading.Lock()
        # variable -> latest record
        self._index: dict[str, dict] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def put(self, record: dict) -> dict:
        """Validate, persist and index a STATE record. Returns the record."""
        jsonschema.validate(instance=record, schema=_SCHEMA)
        with self._lock:
            self._append(record)
            self._index[record["variable"]] = record
        return record

    def get(self, variable: str) -> dict | None:
        """Return the latest STATE record for *variable*, or ``None``."""
        return self._index.get(variable)

    def get_value(self, variable: str, default=None):
        """Return the latest value for *variable*."""
        rec = self.get(variable)
        return rec["value"] if rec else default

    def all_latest(self) -> dict[str, dict]:
        """Return a copy of the full latest-state index."""
        return dict(self._index)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self):
        if not os.path.exists(self._path):
            return
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                self._index[rec["variable"]] = rec

    def _append(self, record: dict):
        with open(self._path, "a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

