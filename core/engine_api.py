# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Mission Engine + Artifact Vault + Evolution Tree — API Router.

Endpoints:
  POST /v1/engine/mission/run    — run a single mission
  POST /v1/engine/mission/chain  — chain sequential missions
  GET  /v1/engine/mission/{id}   — get mission by ID
  GET  /v1/engine/missions       — list recent missions
  GET  /v1/engine/missions/stats — mission statistics

  GET  /v1/engine/artifacts            — list artifacts
  GET  /v1/engine/artifacts/latest     — latest artifact
  GET  /v1/engine/artifacts/{id}       — get artifact by ID
  GET  /v1/engine/artifacts/search     — search artifacts
  GET  /v1/engine/artifacts/index      — vault index

  GET  /v1/engine/evolution/tree        — full evolution tree
  GET  /v1/engine/evolution/transitions — available transitions
  POST /v1/engine/evolution/check       — check transition validity

  GET  /v1/engine/workers              — list registered workers
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/v1/engine", tags=["engine"])


# ── Request/Response models ────────────────────────────────────

class RunMissionRequest(BaseModel):
    intent: str
    payload: Optional[Dict[str, Any]] = None
    mission_id: Optional[str] = None

class ChainMissionsRequest(BaseModel):
    steps: List[Dict[str, Any]]

class CheckTransitionRequest(BaseModel):
    current_form: str
    target_form: str
    total_missions: int = 0
    success_rate: float = 0
    swarm_tier: int = 1
    capabilities_used: Optional[List[str]] = None


# ── MISSION ENDPOINTS ──────────────────────────────────────────

@router.post("/mission/run")
async def api_run_mission(req: RunMissionRequest):
    """Run a single mission. Dispatches to the appropriate worker, stores artifact."""
    from core.mission_engine import run_mission
    result = run_mission(
        intent=req.intent,
        payload=req.payload or {},
        mission_id=req.mission_id,
        operator="cockpit",
    )
    return result


@router.post("/mission/chain")
async def api_chain_missions(req: ChainMissionsRequest):
    """Chain sequential missions. Each step's result feeds into the next."""
    from core.mission_engine import chain_missions
    if not req.steps:
        raise HTTPException(400, "At least one step required")
    result = chain_missions(steps=req.steps, operator="cockpit")
    return result


@router.get("/mission/{mission_id}")
async def api_get_mission(mission_id: str):
    """Get a specific mission by ID."""
    from core.mission_engine import get_mission
    m = get_mission(mission_id)
    if not m:
        raise HTTPException(404, f"Mission '{mission_id}' not found")
    return m


@router.get("/missions")
async def api_list_missions(limit: int = 20):
    """List recent missions."""
    from core.mission_engine import recent_missions
    return {"ok": True, "missions": recent_missions(limit=limit)}


@router.get("/missions/stats")
async def api_mission_stats():
    """Aggregate mission statistics."""
    from core.mission_engine import mission_stats
    return {"ok": True, **mission_stats()}


# ── ARTIFACT ENDPOINTS ─────────────────────────────────────────

@router.get("/artifacts")
async def api_list_artifacts(type: Optional[str] = None, limit: int = 20):
    """List artifacts, optionally filtered by type."""
    from core.artifact_vault import list_artifacts
    arts = list_artifacts(artifact_type=type, limit=limit)  # type: ignore
    return {"ok": True, "count": len(arts), "artifacts": arts}


@router.get("/artifacts/latest")
async def api_latest_artifact(type: Optional[str] = None):
    """Get the latest artifact, optionally by type."""
    from core.artifact_vault import load_latest
    art = load_latest(artifact_type=type)  # type: ignore
    if not art:
        raise HTTPException(404, "No artifacts found")
    return art


@router.get("/artifacts/search")
async def api_search_artifacts(q: str = "", limit: int = 10):
    """Search artifacts by text query."""
    from core.artifact_vault import search
    if not q:
        raise HTTPException(400, "Query parameter 'q' required")
    results = search(query=q, limit=limit)
    return {"ok": True, "count": len(results), "artifacts": results}


@router.get("/artifacts/index")
async def api_artifact_index():
    """Get the vault index: type counts and latest IDs."""
    from core.artifact_vault import get_index
    return {"ok": True, **get_index()}


@router.get("/artifacts/{artifact_id}")
async def api_get_artifact(artifact_id: str):
    """Get a specific artifact by ID."""
    from core.artifact_vault import load
    art = load(artifact_id)
    if not art:
        raise HTTPException(404, f"Artifact '{artifact_id}' not found")
    return art


# ── EVOLUTION ENDPOINTS ────────────────────────────────────────

@router.get("/evolution/tree")
async def api_evolution_tree():
    """Return the full evolution tree (nodes + edges)."""
    from core.evolution_tree import get_tree
    return {"ok": True, **get_tree()}


@router.get("/evolution/transitions")
async def api_available_transitions(current_form: str = "core"):
    """Return available evolution transitions from the current form."""
    from core.evolution_tree import get_available_transitions
    edges = get_available_transitions(current_form)
    return {"ok": True, "current_form": current_form, "transitions": edges}


@router.post("/evolution/check")
async def api_check_transition(req: CheckTransitionRequest):
    """Check if a specific evolution transition is valid."""
    from core.evolution_tree import check_transition
    result = check_transition(
        current_form=req.current_form,
        target_form=req.target_form,
        total_missions=req.total_missions,
        success_rate=req.success_rate,
        swarm_tier=req.swarm_tier,
        capabilities_used=req.capabilities_used,
    )
    return {"ok": True, **result}


# ── WORKER ENDPOINTS ───────────────────────────────────────────

@router.get("/workers")
async def api_list_workers():
    """List all registered workers and their capabilities."""
    from core.mission_engine import list_workers
    workers = list_workers()
    return {"ok": True, "count": len(workers), "workers": workers}
