from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from backend.proposal_registry import PROPOSALS
from backend.simulation_layer import simulate_proposal

router = APIRouter()


@router.get("/v1/nexusmon/proposals/{proposal_id}/simulate")
async def simulate_single(proposal_id: str):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    return simulate_proposal(asdict(p))
