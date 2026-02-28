from datetime import datetime

from fastapi import APIRouter

router = APIRouter()

AGENT_HEALTH = {
    "helper1": {"status": "healthy", "last_check": None},
    "reality_gate": {"status": "healthy", "last_check": None},
    "mission_engine": {"status": "healthy", "last_check": None},
}


@router.get("/v1/canonical/agents/health")
async def health():
    now = datetime.utcnow().isoformat()
    for a in AGENT_HEALTH.values():
        a["last_check"] = now
    return AGENT_HEALTH
