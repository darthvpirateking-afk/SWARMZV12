"""
state_store.py – Append-only state store backed by data/state.jsonl.

Validates records against schemas/state.schema.json. Maintains an
in-memory index for O(1) latest-value lookups by variable name.
Thread-safe.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Optional

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
        self._index: Dict[str, dict] = {}  # variable → latest record
        self._load()

    @property
    def path(self) -> str:
        return self._path

    def append(self, record: dict) -> dict:
        """Validate, persist and index a STATE record."""
        jsonschema.validate(instance=record, schema=_SCHEMA)
        with self._lock:
            self._write(record)
            self._index[record["variable"]] = record
        return record

    def get_latest(self, variable: str) -> Optional[dict]:
        """Return the latest STATE record for *variable*."""
        return self._index.get(variable)

    def get_latest_value(self, variable: str, default: Any = None) -> Any:
        """Return the latest value for *variable*."""
        rec = self.get_latest(variable)
        return rec["value"] if rec else default

    def all_latest(self) -> Dict[str, dict]:
        """Return a copy of the full latest-state index."""
        return dict(self._index)

    def all_latest_values(self) -> Dict[str, Any]:
        """Return {variable: value} for all known variables."""
        return {k: v["value"] for k, v in self._index.items()}

    def _load(self):
        if not os.path.exists(self._path):
            return
        with open(self._path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    self._index[rec["variable"]] = rec
                except (json.JSONDecodeError, KeyError):
                    pass  # skip bad lines

    def _write(self, record: dict):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
