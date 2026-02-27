# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Mission lifecycle state machine endpoints."""

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("swarmz.mission_lifecycle")

router = APIRouter()

# Optional artifact vault — import at module level so failures are visible at startup
try:
    from nexusmon_artifact_vault import store_artifact as _vault_store_artifact

    _VAULT_AVAILABLE = True
except Exception as _vault_import_err:
    _vault_store_artifact = None  # type: ignore[assignment]
    _VAULT_AVAILABLE = False
    logger.warning("Artifact vault unavailable: %s", _vault_import_err)

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
        snapshot = dict(m)

    # Store an artifact when a mission reaches a terminal state
    if (
        new_state in ("COMPLETED", "FAILED", "ABORTED")
        and _VAULT_AVAILABLE
        and _vault_store_artifact is not None
    ):
        try:
            artifact_type = "REPORT" if new_state == "COMPLETED" else "LOG"
            _vault_store_artifact(
                mission_id=mission_id,
                task_id=mission_id,
                type=artifact_type,
                title=f"Mission {mission_id} — {new_state}",
                content={
                    "goal": snapshot.get("goal"),
                    "category": snapshot.get("category"),
                    "final_state": new_state,
                    "history": snapshot.get("history", []),
                },
                input_snapshot={"constraints": snapshot.get("constraints", {})},
            )
        except Exception as exc:
            logger.warning(
                "Failed to store mission artifact for %s: %s", mission_id, exc
            )

    return snapshot


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
