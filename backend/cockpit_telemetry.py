from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from core.observability import AgentEvent, ObservabilityEmitter

router = APIRouter()
emitter = ObservabilityEmitter(success_sample_rate=1.0)

TELEMETRY = {
    "strict_mode": False,
    "operator_approval": True,
    "agent_health": {},
    "mission_logs": [],
    "trace_feed": [],
}


@router.get("/v1/canonical/cockpit/state")
async def cockpit_state():
    return TELEMETRY


@router.post("/v1/canonical/cockpit/strict_mode")
async def set_strict_mode(payload: dict):
    TELEMETRY["strict_mode"] = bool(payload.get("value", False))
    emitter.emit(
        AgentEvent(
            agent_id="cockpit",
            trace_id="cockpit",
            event="cockpit.strict_mode.set",
            decision=str(TELEMETRY["strict_mode"]),
            inputs_hash="",
            outcome="success",
        )
    )
    return {"ok": True}


@router.post("/v1/canonical/cockpit/operator_approval")
async def set_operator_approval(payload: dict):
    TELEMETRY["operator_approval"] = bool(payload.get("value", True))
    emitter.emit(
        AgentEvent(
            agent_id="cockpit",
            trace_id="cockpit",
            event="cockpit.operator_approval.set",
            decision=str(TELEMETRY["operator_approval"]),
            inputs_hash="",
            outcome="success",
        )
    )
    return {"ok": True}


@router.post("/v1/canonical/cockpit/health")
async def update_health(payload: dict):
    TELEMETRY["agent_health"] = payload
    emitter.emit(
        AgentEvent(
            agent_id="cockpit",
            trace_id="cockpit",
            event="cockpit.health.update",
            decision="update",
            inputs_hash="",
            outcome="success",
        )
    )
    return {"ok": True}


@router.post("/v1/canonical/cockpit/mission_log")
async def mission_log(payload: dict):
    TELEMETRY["mission_logs"].append(
        {"timestamp": datetime.utcnow().isoformat(), "entry": payload}
    )
    return {"ok": True}


@router.post("/v1/canonical/cockpit/trace_feed")
async def trace_feed(payload: dict):
    TELEMETRY["trace_feed"].append(payload)
    return {"ok": True}
