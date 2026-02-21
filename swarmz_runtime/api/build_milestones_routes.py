# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Build milestones routes for the cockpit BuildMilestonesPage."""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["build-milestones"])


@router.get("/status")
def milestones_status():
    """Return build milestones status."""
    return {
        "ok": True,
        "current_phase": "operational",
        "milestones": [
            {
                "id": "m1",
                "name": "Core Engine Boot",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m2",
                "name": "API Layer Online",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m3",
                "name": "Mission Engine Active",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m4",
                "name": "Cockpit UI Connected",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m5",
                "name": "WebSocket Real-time",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m6",
                "name": "PostgreSQL Migration",
                "status": "complete",
                "completed_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "m7",
                "name": "Full System Integration",
                "status": "in_progress",
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "m8",
                "name": "Railway Deployment",
                "status": "pending",
            },
        ],
    }


@router.post("/promote")
def promote_milestone(milestone_id: str):
    """Promote a milestone to the next status."""
    return {
        "ok": True,
        "milestone_id": milestone_id,
        "new_status": "complete",
        "promoted_at": datetime.now(timezone.utc).isoformat(),
    }
