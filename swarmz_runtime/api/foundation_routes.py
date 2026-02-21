# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""API foundation status routes for the cockpit ApiFoundationPage."""

from fastapi import APIRouter

router = APIRouter(tags=["foundation"])


@router.get("/status")
def api_status():
    """Return API foundation health status."""
    return {
        "ok": True,
        "api_version": "1.0.0",
        "domains_registered": 8,
        "endpoints_active": 42,
        "uptime_hours": 0,
    }


@router.get("/domains")
def api_domains():
    """Return registered API domains."""
    return {
        "ok": True,
        "domains": [
            {"name": "missions", "prefix": "/v1/missions", "endpoints": 3, "status": "active"},
            {"name": "system", "prefix": "/v1/system", "endpoints": 4, "status": "active"},
            {"name": "command-center", "prefix": "/v1/command-center", "endpoints": 10, "status": "active"},
            {"name": "companion", "prefix": "/v1/companion", "endpoints": 3, "status": "active"},
            {"name": "dispatch", "prefix": "/v1/dispatch", "endpoints": 2, "status": "active"},
            {"name": "auth", "prefix": "/v1/auth", "endpoints": 2, "status": "active"},
            {"name": "galileo", "prefix": "/v1/galileo", "endpoints": 6, "status": "active"},
            {"name": "health", "prefix": "/health", "endpoints": 4, "status": "active"},
        ],
    }
