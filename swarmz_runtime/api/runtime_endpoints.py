from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()

@router.get("/v1/runtime/scoreboard", tags=["runtime"])
def runtime_scoreboard():
    return {
        "ok": True,
        "partner_traits_mode": "deterministic_static",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }