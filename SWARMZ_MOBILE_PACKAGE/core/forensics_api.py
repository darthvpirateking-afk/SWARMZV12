# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
FastAPI surface for the SWARMZ Forensics Module.

Call register_forensics_api(app) from server.py to mount:
- GET /v1/forensics/index
- GET /v1/forensics/timeline?mission_id=...
- GET /v1/forensics/casefile?mission_id=...

All endpoints are read-only and operate over local files only.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query

from core.atomic import atomic_append_jsonl
from jsonl_utils import read_jsonl

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
FORENSICS_LOG = DATA_DIR / "audit_forensics.jsonl"


def _audit(event: str, payload: Dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    atomic_append_jsonl(FORENSICS_LOG, entry)


def _index_missions_with_activity() -> List[str]:
    rows, _, _ = read_jsonl(MISSIONS_FILE)
    return [str(m.get("mission_id")) for m in rows if m.get("mission_id")]


def register_forensics_api(app: FastAPI) -> None:
    """Mount /v1/forensics/* endpoints on the given FastAPI app."""

    @app.get("/v1/forensics/index")
    async def forensics_index() -> Dict[str, Any]:
        try:
            mission_ids = _index_missions_with_activity()
            _audit("forensics_index_viewed", {"count": len(mission_ids)})
            return {"ok": True, "mission_ids": mission_ids}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300], "mission_ids": []}

    @app.get("/v1/forensics/timeline")
    async def forensics_timeline(mission_id: str = Query(...)) -> Dict[str, Any]:
        try:
            from core.forensics import build_timeline

            tl = build_timeline(mission_id)
            if not tl:
                raise HTTPException(status_code=404, detail="No events for mission_id")
            _audit(
                "forensics_timeline_viewed",
                {"mission_id": mission_id, "count": len(tl)},
            )
            return {"ok": True, "mission_id": mission_id, "timeline": tl}
        except HTTPException:
            raise
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc)[:300],
                "mission_id": mission_id,
                "timeline": [],
            }

    @app.get("/v1/forensics/casefile")
    async def forensics_casefile(mission_id: str = Query(...)) -> Dict[str, Any]:
        try:
            from core.forensics import build_casefile

            cf = build_casefile(mission_id)
            if cf is None:
                raise HTTPException(status_code=404, detail="mission_id not found")
            _audit("forensics_casefile_viewed", {"mission_id": mission_id})
            return {"ok": True, "casefile": cf}
        except HTTPException:
            raise
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300], "casefile": None}

    @app.post("/v1/forensics/self_check")
    async def forensics_self_check_endpoint() -> Dict[str, Any]:
        try:
            from core.forensics import self_check

            result = self_check()
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}
