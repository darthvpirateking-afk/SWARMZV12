from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem
from swarmz_runtime.core.primal_state import load_primal_state_slate


router = APIRouter()
_ecosystem = OperatorEcosystem(Path(__file__).resolve().parent.parent.parent)


@router.get("/operator-os/prime-state")
def get_prime_state():
    return load_primal_state_slate()


class TimelineEventRequest(BaseModel):
    event_type: str
    domain: str
    risk: str = "low"
    money_impact_cents: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)


class MissionUpsertRequest(BaseModel):
    mission_id: str
    mission_type: str
    status: str
    risk_level: str
    budget_cents: int
    policy_profile: str
    agents: list[str] = Field(default_factory=list)


class MoneyRiskSnapshotRequest(BaseModel):
    spend_day_cents: int = 0
    spend_week_cents: int = 0
    blocked_actions: int = 0
    refunds_cents: int = 0
    chargebacks_cents: int = 0
    top_risky_entities: list[str] = Field(default_factory=list)


class OperatorProfileRequest(BaseModel):
    name: str
    risk_tolerance: str
    max_autonomy: int = Field(ge=0, le=100)
    default_budget_cap_cents: int
    default_profit_floor_bps: int
    ethics_profile: str


class OperatorPreferenceRequest(BaseModel):
    operator_id: str
    key: str
    value_json: Dict[str, Any] = Field(default_factory=dict)


class OperatorPolicyRequest(BaseModel):
    operator_id: str
    rule_text: str
    rule_code: str
    scope: str
    status: str = "active"


class OperatorGoalRequest(BaseModel):
    operator_id: str
    time_horizon: str
    goal_text: str
    metrics_json: Dict[str, Any] = Field(default_factory=dict)


class PolicyDecisionRequest(BaseModel):
    operator_id: str
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)


class VaultBlueprintRequest(BaseModel):
    blueprint_id: str
    name: str
    version: int
    manifest: Dict[str, Any] = Field(default_factory=dict)


class VaultOfferRequest(BaseModel):
    offer_id: str
    blueprint_id: str
    sku: str
    channel: str
    margin_percent: float


class VaultListingRequest(BaseModel):
    listing_id: str
    offer_id: str
    status: str


class VaultOrderRequest(BaseModel):
    order_id: str
    offer_id: str
    total_cents: int
    refund_rate: float
    supplier: str


class VaultExperimentRequest(BaseModel):
    kind: str
    subject_type: str
    subject_id: str
    variant_a_id: str
    variant_b_id: str
    kpi: str
    result_json: Dict[str, Any] = Field(default_factory=dict)


class VaultOutcomeRequest(BaseModel):
    subject_type: str
    subject_id: str
    conversion: float
    margin: float
    refund_rate: float
    sla_adherence: float
    channel: str
    supplier: str


class VaultReflectionRequest(BaseModel):
    agent: str
    scope: str
    input_summary: str
    output_summary: str
    changes_json: Dict[str, Any] = Field(default_factory=dict)


class VaultEmbeddingRequest(BaseModel):
    source_type: str
    source_id: str
    text: str
    embedding: list[float] = Field(default_factory=list)


@router.post("/operator-os/timeline/event")
def add_timeline_event(payload: TimelineEventRequest):
    return {"ok": True, "event": _ecosystem.add_event(**payload.model_dump())}


@router.get("/operator-os/timeline")
def timeline(
    agent: Optional[str] = Query(default=None),
    domain: Optional[str] = Query(default=None),
    risk: Optional[str] = Query(default=None),
):
    rows = _ecosystem.list_timeline(agent=agent, domain=domain, risk=risk)
    return {"ok": True, "events": rows, "count": len(rows)}


@router.post("/operator-os/missions/upsert")
def upsert_mission(payload: MissionUpsertRequest):
    return {"ok": True, "mission": _ecosystem.upsert_mission(**payload.model_dump())}


@router.get("/operator-os/missions")
def missions(status: Optional[str] = Query(default=None)):
    rows = _ecosystem.list_missions(status=status)
    return {"ok": True, "missions": rows, "count": len(rows)}


@router.post("/operator-os/money-risk/snapshot")
def money_risk_snapshot(payload: MoneyRiskSnapshotRequest):
    return {"ok": True, "snapshot": _ecosystem.set_money_risk_snapshot(payload.model_dump())}


@router.post("/identity/profiles")
def create_profile(payload: OperatorProfileRequest):
    return {"ok": True, "profile": _ecosystem.create_operator_profile(**payload.model_dump())}


@router.get("/identity/profiles")
def list_profiles():
    rows = _ecosystem.list_operator_profiles()
    return {"ok": True, "profiles": rows, "count": len(rows)}


@router.post("/identity/preferences")
def add_preference(payload: OperatorPreferenceRequest):
    return {"ok": True, "preference": _ecosystem.add_preference(**payload.model_dump())}


@router.post("/identity/policies")
def add_policy(payload: OperatorPolicyRequest):
    return {"ok": True, "policy": _ecosystem.add_policy(**payload.model_dump())}


@router.post("/identity/goals")
def add_goal(payload: OperatorGoalRequest):
    return {"ok": True, "goal": _ecosystem.add_goal(**payload.model_dump())}


@router.post("/identity/policy-decision")
def policy_decision(payload: PolicyDecisionRequest):
    result = _ecosystem.evaluate_policy_decision(**payload.model_dump())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"ok": True, "decision": result}


@router.post("/vault/blueprints")
def vault_add_blueprint(payload: VaultBlueprintRequest):
    return {"ok": True, "blueprint": _ecosystem.add_blueprint(**payload.model_dump())}


@router.post("/vault/offers")
def vault_add_offer(payload: VaultOfferRequest):
    return {"ok": True, "offer": _ecosystem.add_offer(**payload.model_dump())}


@router.post("/vault/listings")
def vault_add_listing(payload: VaultListingRequest):
    return {"ok": True, "listing": _ecosystem.add_listing(**payload.model_dump())}


@router.post("/vault/orders")
def vault_add_order(payload: VaultOrderRequest):
    return {"ok": True, "order": _ecosystem.add_order(**payload.model_dump())}


@router.post("/vault/experiments")
def vault_add_experiment(payload: VaultExperimentRequest):
    return {"ok": True, "experiment": _ecosystem.add_experiment(**payload.model_dump())}


@router.post("/vault/outcomes")
def vault_add_outcome(payload: VaultOutcomeRequest):
    return {"ok": True, "outcome": _ecosystem.add_outcome(**payload.model_dump())}


@router.post("/vault/reflections")
def vault_add_reflection(payload: VaultReflectionRequest):
    return {"ok": True, "reflection": _ecosystem.add_reflection(**payload.model_dump())}


@router.post("/vault/embeddings")
def vault_add_embedding(payload: VaultEmbeddingRequest):
    return {"ok": True, "embedding": _ecosystem.add_embedding(**payload.model_dump())}


@router.get("/vault/blueprints/{blueprint_id}/lineage")
def blueprint_lineage(blueprint_id: str):
    return {"ok": True, "lineage": _ecosystem.get_lineage(blueprint_id)}


@router.get("/vault/experiments")
def experiments(
    subject_type: Optional[str] = Query(default=None),
    subject_id: Optional[str] = Query(default=None),
):
    rows = _ecosystem.list_experiments(subject_type=subject_type, subject_id=subject_id)
    return {"ok": True, "experiments": rows, "count": len(rows)}


@router.get("/vault/patterns/top_winners")
def top_winners(limit: int = 5):
    rows = _ecosystem.top_winners(limit)
    return {"ok": True, "items": rows, "count": len(rows)}


@router.get("/vault/patterns/top_failures")
def top_failures(limit: int = 5):
    rows = _ecosystem.top_failures(limit)
    return {"ok": True, "items": rows, "count": len(rows)}
