# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Ecosystem API â€“ autonomous loop endpoints for SWARMZ.

Routes:
    POST /v1/ecosystem/run            â€“ single mission step
    POST /v1/ecosystem/auto/start     â€“ start autonomous loop
    POST /v1/ecosystem/auto/stop      â€“ stop autonomous loop
    GET  /v1/ecosystem/verify         â€“ verify ecosystem health
    GET  /v1/ecosystem/packs/{mid}    â€“ fetch mission pack by id
    GET  /v1/ecosystem/status         â€“ loop state, tick_count, last_tick_ts
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Callable, Dict, Optional

from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.core.autoloop import AutoLoopManager

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()

_loop_manager: Optional[AutoLoopManager] = None


def _get_loop() -> AutoLoopManager:
    global _loop_manager
    if _loop_manager is None:
        _loop_manager = AutoLoopManager(get_engine())
    return _loop_manager


def set_engine_provider(fn: Callable[[], SwarmzEngine]) -> None:
    """Called by server.py to inject the shared engine getter."""
    global get_engine, _loop_manager
    get_engine = fn
    _loop_manager = None  # reset so next call re-creates with new engine


# â”€â”€ request / response models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class EcosystemRunRequest(BaseModel):
    operator_goal: str = "make money"
    constraints: Dict[str, Any] = {}
    results: Dict[str, Any] = {}


class AutoStartRequest(BaseModel):
    tick_interval: int = 30  # seconds between ticks


# â”€â”€ endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/run")
def ecosystem_run(req: EcosystemRunRequest):
    """Execute a single ecosystem step and return mission_id."""
    loop = _get_loop()
    result = loop.single_step(req.operator_goal, req.constraints, req.results)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/auto/start")
def auto_start(req: AutoStartRequest = AutoStartRequest()):
    """Start the autonomous tick loop."""
    loop = _get_loop()
    loop.start(req.tick_interval)
    return {"status": "started", "tick_interval": req.tick_interval}


@router.post("/auto/stop")
def auto_stop():
    """Stop the autonomous tick loop."""
    loop = _get_loop()
    loop.stop()
    return {"status": "stopped"}


@router.get("/verify")
def ecosystem_verify():
    """Verify the ecosystem is healthy."""
    loop = _get_loop()
    state = loop.get_state()
    engine = get_engine()
    health = engine.get_health()
    return {
        "healthy": True,
        "engine_status": health.get("status", "unknown"),
        "loop_running": state.get("running", False),
        "tick_count": state.get("tick_count", 0),
    }


@router.get("/packs/{mission_id}")
def get_pack(mission_id: str):
    """Return mission pack (mission + audit entries) for a given id."""
    engine = get_engine()
    mission = engine.db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    audit_entries = [
        e for e in engine.db.load_audit_log(limit=500)
        if e.get("mission_id") == mission_id
    ]
    return {"mission": mission, "audit": audit_entries}


@router.get("/status")
def ecosystem_status():
    """Show loop state, tick_count, last_tick_ts."""
    loop = _get_loop()
    return loop.get_state()

