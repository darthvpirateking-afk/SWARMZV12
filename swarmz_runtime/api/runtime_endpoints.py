from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/v1/runtime/scoreboard",
    tags=["runtime"],
    operation_id="runtime_endpoints_scoreboard_get",
)
def runtime_scoreboard():
    return {
        "ok": True,
        "partner_traits_mode": "deterministic_static",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
