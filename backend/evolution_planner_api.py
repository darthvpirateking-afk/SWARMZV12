from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from backend.evolution_planner import PLANS, create_basic_plan, realize_step

router = APIRouter()


@router.post("/v1/nexusmon/plans")
async def create_plan():
    plan = create_basic_plan()
    return asdict(plan)


@router.get("/v1/nexusmon/plans")
async def list_plans():
    return [asdict(p) for p in PLANS.values()]


@router.post("/v1/nexusmon/plans/{plan_id}/realize")
async def realize_plan(plan_id: str):
    plan = PLANS.get(plan_id)
    if not plan:
        return {"error": "plan not found"}
    for step in plan.steps:
        if step.status == "planned":
            await realize_step(step)
    return asdict(plan)
