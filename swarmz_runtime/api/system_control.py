# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""System runtime control endpoints: start, stop, restart, status, heartbeat, logs."""

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional

from fastapi import APIRouter, Query

logger = logging.getLogger("swarmz.system_control")

router = APIRouter()

# ── In-memory runtime state ───────────────────────────────────────────────────
_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {
    "status": "running",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "stopped_at": None,
    "restart_count": 0,
    "last_heartbeat": datetime.now(timezone.utc).isoformat(),
}

# ── In-memory log ring (deque for O(1) append/pop) ───────────────────────────
_LOG_RING_MAX = 500
_LOG_RING: Deque[Dict[str, Any]] = deque(maxlen=_LOG_RING_MAX)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_log(
    level: str,
    source: str,
    message: str,
    mission_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    entry: Dict[str, Any] = {
        "timestamp": _ts(),
        "level": level.upper(),
        "source": source,
        "mission_id": mission_id,
        "message": message,
        "details": details or {},
    }
    with _LOCK:
        _LOG_RING.append(entry)  # deque(maxlen) handles eviction automatically


# ── Runtime state helpers ─────────────────────────────────────────────────────


def _get_state() -> Dict[str, Any]:
    with _LOCK:
        return dict(_STATE)


def _set_status(status: str) -> None:
    with _LOCK:
        _STATE["status"] = status
        if status == "running":
            _STATE["started_at"] = _ts()
            _STATE["stopped_at"] = None
        elif status == "stopped":
            _STATE["stopped_at"] = _ts()
        _STATE["last_heartbeat"] = _ts()


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/start")
def start_runtime() -> Dict[str, Any]:
    """Start the SWARMZ runtime."""
    _set_status("running")
    _append_log("INFO", "system_control", "Runtime started via API")
    return {"status": "running", "timestamp": _ts(), "details": {"action": "start"}}


@router.post("/stop")
def stop_runtime() -> Dict[str, Any]:
    """Stop the SWARMZ runtime."""
    _set_status("stopped")
    _append_log("INFO", "system_control", "Runtime stopped via API")
    return {"status": "stopped", "timestamp": _ts(), "details": {"action": "stop"}}


@router.post("/restart")
def restart_runtime() -> Dict[str, Any]:
    """Restart the SWARMZ runtime."""
    with _LOCK:
        _STATE["status"] = "restarting"
        _STATE["restart_count"] = _STATE.get("restart_count", 0) + 1
        count = _STATE["restart_count"]
    _append_log("INFO", "system_control", "Runtime restarting via API")
    _set_status("running")
    _append_log("INFO", "system_control", "Runtime restart complete")
    return {
        "status": "running",
        "timestamp": _ts(),
        "details": {"action": "restart", "restart_count": count},
    }


@router.get("/status")
def get_runtime_status() -> Dict[str, Any]:
    """Get current runtime status."""
    state = _get_state()
    return {
        "status": state["status"],
        "timestamp": _ts(),
        "details": {
            "started_at": state.get("started_at"),
            "stopped_at": state.get("stopped_at"),
            "restart_count": state.get("restart_count", 0),
            "last_heartbeat": state.get("last_heartbeat"),
        },
    }


@router.get("/heartbeat")
def get_heartbeat() -> Dict[str, Any]:
    """Return current heartbeat / liveness status."""
    with _LOCK:
        _STATE["last_heartbeat"] = _ts()
        status = _STATE["status"]
    _append_log("INFO", "system_control", "Heartbeat polled")
    return {
        "alive": True,
        "status": status,
        "timestamp": _ts(),
    }


@router.get("/logs")
def get_logs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    level: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    mission_id: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Return kernel log entries with optional filtering."""
    with _LOCK:
        entries = list(_LOG_RING)

    if level:
        entries = [e for e in entries if e.get("level", "").upper() == level.upper()]
    if source:
        entries = [e for e in entries if e.get("source", "") == source]
    if mission_id:
        entries = [e for e in entries if e.get("mission_id") == mission_id]

    total = len(entries)
    page = entries[offset : offset + limit]
    return {"entries": page, "total": total, "offset": offset, "limit": limit}
