"""
debug.py – Debug / diagnostics endpoints for the SWARMZ runtime.

Provides storage health checks and diagnostic info accessible at
``/v1/debug/...``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict

from fastapi import APIRouter
from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.storage.jsonl_utils import read_jsonl

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()


@router.get("/storage_check")
def storage_check() -> Dict[str, Any]:
    """Return a diagnostic summary of all JSONL / JSON storage files."""
    engine = get_engine()
    db = engine.db
    data_dir = db.data_dir

    def _check_jsonl(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"exists": False, "rows": 0, "size_bytes": 0}
        rows = read_jsonl(path)
        return {
            "exists": True,
            "rows": len(rows),
            "size_bytes": path.stat().st_size,
        }

    def _check_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {"exists": False, "size_bytes": 0}
        try:
            import json

            with open(path) as fh:
                json.load(fh)
            return {
                "exists": True,
                "valid": True,
                "size_bytes": path.stat().st_size,
            }
        except Exception as exc:
            return {
                "exists": True,
                "valid": False,
                "error": str(exc),
                "size_bytes": path.stat().st_size,
            }

    return {
        "data_dir": str(data_dir),
        "missions_jsonl": _check_jsonl(db.missions_file),
        "audit_jsonl": _check_jsonl(db.audit_file),
        "runes_json": _check_json(db.runes_file),
        "system_state_json": _check_json(db.state_file),
    }
