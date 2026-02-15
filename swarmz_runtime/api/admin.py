from fastapi import APIRouter
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()
engine = SwarmzEngine()


@router.post("/maintenance")
def schedule_maintenance():
    result = engine.schedule_maintenance()
    return result
