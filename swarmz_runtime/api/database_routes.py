# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Database layer status routes for the cockpit DatabaseLayerPage."""

import os
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["database"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _ROOT_DIR / "data"


@router.get("/status")
def db_status():
    """Return database layer status (JSONL or PostgreSQL)."""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/swarmz.db")
    backend = "postgresql" if "postgresql" in db_url or "postgres" in db_url else "sqlite"

    return {
        "ok": True,
        "backend": backend,
        "connected": True,
        "data_dir": str(_DATA_DIR),
        "jsonl_legacy": _DATA_DIR.exists(),
    }


@router.get("/collections")
def db_collections():
    """Return list of data collections/tables."""
    collections = [
        {"name": "missions", "type": "table", "description": "Mission records"},
        {"name": "audit_entries", "type": "table", "description": "Audit log entries"},
        {"name": "runes", "type": "table", "description": "Pattern templates"},
        {"name": "runs", "type": "table", "description": "Mission execution runs"},
        {"name": "system_state", "type": "table", "description": "Runtime state (single-row)"},
        {"name": "command_center_state", "type": "table", "description": "Command center (single-row)"},
    ]
    return {"ok": True, "collections": collections, "count": len(collections)}


@router.get("/stats")
def db_stats():
    """Return database statistics."""
    from swarmz_runtime.storage.database import get_engine
    from sqlalchemy import text

    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Works for both SQLite and PostgreSQL
            result = conn.execute(text("SELECT count(*) FROM missions")).scalar()
            missions_count = result or 0
    except Exception:
        missions_count = 0

    return {
        "ok": True,
        "missions_count": missions_count,
        "storage_backend": str(get_engine().url).split("://")[0] if get_engine() else "unknown",
    }
