from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from swarmz_runtime.core.federation_manager import FederationManager
from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem


router = APIRouter()
_manager = FederationManager(Path(__file__).resolve().parent.parent.parent)
_ecosystem = OperatorEcosystem(Path(__file__).resolve().parent.parent.parent)


class CreateOrganismRequest(BaseModel):
    name: str
    owner_id: str
    config_json: Dict[str, Any] = Field(default_factory=dict)


class LifecycleRequest(BaseModel):
    reason: str = "operator_command"


class EvolveRequest(BaseModel):
    mission_success: bool = True
    incidents: int = 0
    policy_compliance: bool = True


@router.post("/federation/organisms")
def create_organism(payload: CreateOrganismRequest):
    return {"ok": True, **_manager.create_organism(payload.name, payload.owner_id, payload.config_json)}


@router.get("/federation/organisms/{organism_id}")
def get_organism(organism_id: str):
    row = _manager.get_organism(organism_id)
    if not row:
        raise HTTPException(status_code=404, detail="organism_not_found")
    return {"ok": True, "organism": row}


@router.get("/federation/organisms")
def list_organisms():
    rows = _manager.list_organisms()
    return {"ok": True, "organisms": rows, "count": len(rows)}


@router.post("/federation/organisms/{organism_id}/pause")
def pause_organism(organism_id: str, payload: Optional[LifecycleRequest] = None):
    reason = payload.reason if payload else "operator_command"
    row = _manager.pause_organism(organism_id, reason=reason)
    if not row:
        raise HTTPException(status_code=404, detail="organism_not_found")
    return {"ok": True, "organism": row}


@router.post("/federation/organisms/{organism_id}/retire")
def retire_organism(organism_id: str, payload: Optional[LifecycleRequest] = None):
    reason = payload.reason if payload else "operator_retire"
    row = _manager.retire_organism(organism_id, reason=reason)
    if not row:
        raise HTTPException(status_code=404, detail="organism_not_found")
    return {"ok": True, "organism": row}


@router.post("/federation/organisms/{organism_id}/evolve")
def evolve_organism(organism_id: str, payload: EvolveRequest):
    row = _manager.evolve_organism(
        organism_id,
        mission_success=payload.mission_success,
        incidents=payload.incidents,
        policy_compliance=payload.policy_compliance,
    )
    if not row:
        raise HTTPException(status_code=404, detail="organism_not_found")
    return {"ok": True, "organism": row}


@router.get("/federation/metrics")
def federation_metrics():
    return {"ok": True, "metrics": _manager.aggregate_metrics()}


@router.post("/federation/insights/nightly")
def nightly_insights():
    outcomes = _ecosystem.top_winners(limit=20) + _ecosystem.top_failures(limit=20)
    insight = _manager.generate_nightly_insights(outcomes)
    return {"ok": True, "insight": insight}


@router.get("/federation/insights/latest")
def latest_insights():
    insight = _manager.latest_insights()
    return {"ok": True, "insight": insight}
