from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from swarmz_runtime.core.system_primitives import ERROR_TAXONOMY, SystemPrimitivesRuntime


router = APIRouter()
_runtime = SystemPrimitivesRuntime(Path(__file__).resolve().parent.parent.parent)


class ConstraintSolveRequest(BaseModel):
    mission_type: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    facts: Dict[str, Any] = Field(default_factory=dict)


class MissionCompileRequest(BaseModel):
    intent: str
    mission_type: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class RealitySyncPushRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "runtime"


class RealitySyncDrainRequest(BaseModel):
    max_items: int = Field(default=100, ge=1, le=1000)


class OperatorOverrideRequest(BaseModel):
    command: str
    args: Dict[str, Any] = Field(default_factory=dict)
    operator_approved: bool = False
    reason: str = "operator_shell"


class ContractValidateRequest(BaseModel):
    action: Dict[str, Any] = Field(default_factory=dict)
    regime: str = "default"


@router.get("/system-primitives/errors")
def error_taxonomy():
    return {"ok": True, "taxonomy": ERROR_TAXONOMY}


@router.post("/system-primitives/constraints/solve")
def solve_constraints(payload: ConstraintSolveRequest):
    return {
        "ok": True,
        "decision": _runtime.solve_constraints(payload.mission_type, payload.constraints, payload.facts),
    }


@router.post("/system-primitives/contracts/validate")
def validate_contract(payload: ContractValidateRequest):
    out = _runtime.validate_contract(payload.action, regime=payload.regime)
    return {"ok": True, **out}


@router.post("/system-primitives/missions/compile")
def compile_mission(payload: MissionCompileRequest):
    return _runtime.compile_mission(payload.intent, payload.mission_type, payload.constraints, payload.context)


@router.post("/system-primitives/reality-sync/push")
def push_reality_event(payload: RealitySyncPushRequest):
    return {"ok": True, "event": _runtime.push_reality_event(payload.event_type, payload.payload, payload.source)}


@router.post("/system-primitives/reality-sync/drain")
def drain_reality_events(payload: RealitySyncDrainRequest):
    return {"ok": True, "drain": _runtime.drain_reality_events(payload.max_items)}


@router.post("/system-primitives/override/execute")
def execute_override(payload: OperatorOverrideRequest):
    return _runtime.execute_override(payload.command, payload.args, payload.operator_approved, payload.reason)


@router.get("/system-primitives/state")
def primitives_state():
    return {"ok": True, "state": _runtime.snapshot()}
