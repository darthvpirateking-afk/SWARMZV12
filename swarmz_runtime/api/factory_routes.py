# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter

from swarmz_runtime.factory import engine

router = APIRouter()


@router.post("/v1/factory/intake")
def factory_intake(body: dict):
    return engine.intake(body)


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

