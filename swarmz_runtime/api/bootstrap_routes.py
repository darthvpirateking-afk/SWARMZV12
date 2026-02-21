# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Bootstrap status routes for the cockpit BootstrapPage."""

from fastapi import APIRouter

router = APIRouter(tags=["bootstrap"])


@router.get("/status")
def bootstrap_status():
    """Return current bootstrap/initialization status."""
    return {
        "ok": True,
        "phase": "operational",
        "steps": [
            {"name": "core_engine", "status": "complete", "progress": 100},
            {"name": "storage_layer", "status": "complete", "progress": 100},
            {"name": "api_routes", "status": "complete", "progress": 100},
            {"name": "websocket", "status": "complete", "progress": 100},
            {"name": "frontend_build", "status": "complete", "progress": 100},
        ],
        "overall_progress": 100,
    }
