# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Mission lifecycle state machine endpoints."""

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ── State machine ─────────────────────────────────────────────────────────────
VALID_STATES = {
    "IDLE",
    "QUEUED",
    "INITIALIZING",
    "RUNNING",
    "PAUSED",
    "COMPLETED",
    "FAILED",
    "ABORTED",
}

ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "IDLE": ["QUEUED"],
    "QUEUED": ["INITIALIZING", "ABORTED"],
    "INITIALIZING": ["RUNNING", "FAILED", "ABORTED"],
    "RUNNING": ["PAUSED", "COMPLETED", "FAILED", "ABORTED"],
    "PAUSED": ["RUNNING", "ABORTED"],
    "COMPLETED": [],
    "FAILED": [],
    "ABORTED": [],
}

_LOCK = threading.Lock()
_MISSIONS: Dict[str, Dict[str, Any]] = {}


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_mission(mission_id: str) -> Dict[str, Any]:
    with _LOCK:
        m = _MISSIONS.get(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")
    return dict(m)


def _transition(mission_id: str, new_state: str) -> Dict[str, Any]:
    with _LOCK:
        m = _MISSIONS.get(mission_id)
        if not m:
            raise HTTPException(
                status_code=404, detail=f"Mission {mission_id} not found"
            )
        current = m["state"]
        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if new_state not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {current} to {new_state}. Allowed: {allowed}",
            )
        m["state"] = new_state
        m["history"].append({"state": new_state, "timestamp": _ts()})
        return dict(m)


# ── Request schemas ───────────────────────────────────────────────────────────


class StartMissionRequest(BaseModel):
    goal: str
    category: str = "default"
    constraints: Dict[str, Any] = {}


class MissionActionRequest(BaseModel):
    mission_id: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/start")
def start_mission(req: StartMissionRequest) -> Dict[str, Any]:
    """Create and start a new mission lifecycle."""
    mission_id = f"MLC-{uuid.uuid4().hex[:10].upper()}"
    now = _ts()
    mission: Dict[str, Any] = {
        "mission_id": mission_id,
        "goal": req.goal,
        "category": req.category,
        "constraints": req.constraints,
        "state": "QUEUED",
        "created_at": now,
        "history": [{"state": "QUEUED", "timestamp": now}],
    }
    with _LOCK:
        _MISSIONS[mission_id] = mission
    return {"mission_id": mission_id, "state": "QUEUED", "timestamp": now}


@router.post("/stop")
def stop_mission(req: MissionActionRequest) -> Dict[str, Any]:
    """Abort a running mission."""
    m = _transition(req.mission_id, "ABORTED")
    return {"mission_id": req.mission_id, "state": m["state"], "timestamp": _ts()}


@router.post("/pause")
def pause_mission(req: MissionActionRequest) -> Dict[str, Any]:
    """Pause a running mission."""
    m = _transition(req.mission_id, "PAUSED")
    return {"mission_id": req.mission_id, "state": m["state"], "timestamp": _ts()}


@router.post("/resume")
def resume_mission(req: MissionActionRequest) -> Dict[str, Any]:
    """Resume a paused mission."""
    m = _transition(req.mission_id, "RUNNING")
    return {"mission_id": req.mission_id, "state": m["state"], "timestamp": _ts()}


@router.get("/status")
def missions_status() -> Dict[str, Any]:
    """Return all active missions and their current states."""
    with _LOCK:
        missions = [dict(m) for m in _MISSIONS.values()]
    return {
        "missions": missions,
        "total": len(missions),
        "timestamp": _ts(),
    }


@router.get("/status/{mission_id}")
def mission_status(mission_id: str) -> Dict[str, Any]:
    """Return state of a specific mission."""
    m = _get_mission(mission_id)
    return {
        "mission_id": mission_id,
        "state": m["state"],
        "history": m["history"],
        "timestamp": _ts(),
    }
