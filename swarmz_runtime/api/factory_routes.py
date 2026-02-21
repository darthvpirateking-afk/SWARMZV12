# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from swarmz_runtime.factory import engine

router = APIRouter()


class ArtifactExecutionRequest(BaseModel):
    artifact_id: str
    parameters: Dict[str, Any] = {}
    operator_key: str
    safe_mode: bool = True


@router.post("/v1/factory/intake")
def factory_intake(body: dict):
    return engine.intake(body)


@router.post("/v1/factory/execute")
def execute_artifact(request: ArtifactExecutionRequest):
    """Execute an artifact with manifestation and safety checks."""
    try:
        result = engine.execute_artifact(
            artifact_id=request.artifact_id,
            parameters=request.parameters,
            operator_key=request.operator_key,
            safe_mode=request.safe_mode,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/v1/factory/missions")
def factory_missions(limit: int = 200):
    return {"missions": engine.list_missions(limit)}


@router.get("/v1/factory/mission/{mission_id}")
def factory_mission(mission_id: str):
    m = engine.get_mission(mission_id)
    if not m:
        return {"error": "not found"}
    return m


@router.get("/v1/factory/graph.mmd")
def factory_graph():
    return engine.mermaid_graph()


@router.get("/v1/decisions/latest")
def decisions_latest():
    dec = engine.latest_decision()
    return dec or {}
