# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
FastAPI surface for the SWARMZ Awareness Module.

Call register_awareness_api(app) from server.py to mount:
- GET /v1/awareness/topology
- GET /v1/awareness/alerts

All endpoints are read-only views over local data/missions.jsonl and
data/audit.jsonl via core.awareness_model.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI

from core.atomic import atomic_append_jsonl

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
AWARENESS_LOG = DATA_DIR / "audit_awareness.jsonl"


def _audit(event: str, payload: Dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "payload": payload,
    }
    atomic_append_jsonl(AWARENESS_LOG, entry)


def register_awareness_api(app: FastAPI) -> None:
    """Mount /v1/awareness/* endpoints on the given FastAPI app."""

    @app.get("/v1/awareness/topology")
    async def get_awareness_topology() -> Dict[str, Any]:
        try:
            from core.awareness_model import build_topology

            topo = build_topology()
            _audit("awareness_topology_viewed", {"meta": topo.get("meta", {})})
            return {"ok": True, "topology": topo}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    @app.get("/v1/awareness/alerts")
    async def get_awareness_alerts() -> Dict[str, Any]:
        try:
            from core.awareness_model import build_topology, compute_alerts

            topo = build_topology()
            alerts = compute_alerts(topo)
            _audit("awareness_alerts_viewed", alerts)
            return {"ok": True, "alerts": alerts}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300], "alerts": {}}

    @app.post("/v1/awareness/self_check")
    async def awareness_self_check_endpoint() -> Dict[str, Any]:
        """Expose the module self-check for diagnostics.

        This is safe and read-only for core data; it only appends to the
        module-specific awareness log.
        """
        try:
            from core.awareness_model import self_check

            result = self_check()
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

