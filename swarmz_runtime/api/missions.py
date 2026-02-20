# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, Callable
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()


class CreateMissionRequest(BaseModel):
    goal: str
    category: str
    constraints: Dict[str, Any] = {}


class RunMissionRequest(BaseModel):
    mission_id: str
    operator_key: Optional[str] = None


class ApproveMissionRequest(BaseModel):
    mission_id: str
    operator_key: str


@router.post("/create")
def create_mission(request: CreateMissionRequest):
    result = get_engine().create_mission(
        goal=request.goal,
        category=request.category,
        constraints=request.constraints
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/run")
def run_mission(request: RunMissionRequest):
    result = get_engine().run_mission(
        mission_id=request.mission_id,
        operator_key=request.operator_key
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/list")
def list_missions(status: Optional[str] = None):
    missions = get_engine().list_missions(status=status)
    return {"missions": missions, "count": len(missions)}


@router.post("/approve")
def approve_mission(request: ApproveMissionRequest):
    result = get_engine().approve_mission(
        mission_id=request.mission_id,
        operator_key=request.operator_key
    )
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result

