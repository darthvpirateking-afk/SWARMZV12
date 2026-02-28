from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from backend.evolution_council import council_evaluate
from backend.evolution_scoring import score_proposal
from backend.safety_intelligence import safety_assess
from core.observability import AgentEvent, ObservabilityEmitter

router = APIRouter()
emitter = ObservabilityEmitter(success_sample_rate=1.0)


class ProposalType(str, Enum):
    MANIFEST = "manifest"
    MISSION = "mission"
    PLUGIN = "plugin"
    TEST = "test"
    DOC = "doc"
    BACKEND = "backend"


class ProposalRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProposalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class Proposal:
    id: str
    created_at: str
    created_by: str
    type: ProposalType
    risk: ProposalRisk
    title: str
    rationale: str
    diff: Dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING
    approvals_required: int = 1
    approvals_given: int = 0
    rejections_given: int = 0


PROPOSALS: Dict[str, Proposal] = {}
COUNCIL_DECISIONS: Dict[str, Any] = {}


def emit_proposal_event(event: str, proposal: Proposal) -> None:
    emitter.emit(
        AgentEvent(
            agent_id="nexusmon",
            trace_id=f"proposal:{proposal.id}",
            event=f"proposal.{event}",
            decision=proposal.status.value,
            inputs_hash="",
            outcome="success",
            payload={
                "id": proposal.id,
                "type": proposal.type.value,
                "risk": proposal.risk.value,
            },
        )
    )


def next_proposal_id() -> str:
    return f"p-{len(PROPOSALS) + 1:04d}"


@router.get("/v1/nexusmon/proposals")
async def list_proposals(status: Optional[str] = None):
    items = list(PROPOSALS.values())
    if status:
        items = [p for p in items if p.status.value == status]
    return [asdict(p) for p in items]


@router.get("/v1/nexusmon/proposals/scores")
async def score_all():
    results = {}
    for pid, p in PROPOSALS.items():
        results[pid] = asdict(score_proposal(asdict(p)))
    return results


@router.get("/v1/nexusmon/proposals/council")
async def council_all():
    results = {}
    for pid, p in PROPOSALS.items():
        decision = council_evaluate(pid, asdict(p))
        results[pid] = asdict(decision)
        COUNCIL_DECISIONS[pid] = asdict(decision)
    return results


@router.get("/v1/nexusmon/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    return asdict(p)


@router.get("/v1/nexusmon/proposals/{proposal_id}/council")
async def council_single(proposal_id: str):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    decision = council_evaluate(proposal_id, asdict(p))
    COUNCIL_DECISIONS[proposal_id] = asdict(decision)
    return asdict(decision)


@router.get("/v1/nexusmon/proposals/{proposal_id}/score")
async def score_single(proposal_id: str):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    score = score_proposal(asdict(p))
    return asdict(score)


@router.get("/v1/nexusmon/proposals/{proposal_id}/safety")
async def safety_single(proposal_id: str):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    return safety_assess(asdict(p))


@router.post("/v1/nexusmon/proposals")
async def create_proposal(payload: Dict[str, Any]):
    """
    NEXUSMON or operator creates a proposal.
    """
    p_type = ProposalType(payload.get("type", "doc"))
    risk = ProposalRisk(payload.get("risk", "low"))
    title = str(payload.get("title", "untitled"))
    rationale = str(payload.get("rationale", ""))
    diff = payload.get("diff", {})

    approvals_required = 2 if risk == ProposalRisk.HIGH else 1

    pid = next_proposal_id()
    now = datetime.utcnow().isoformat()
    proposal = Proposal(
        id=pid,
        created_at=now,
        created_by=str(payload.get("created_by", "nexusmon")),
        type=p_type,
        risk=risk,
        title=title,
        rationale=rationale,
        diff=diff,
        approvals_required=approvals_required,
    )
    PROPOSALS[pid] = proposal
    emit_proposal_event("created", proposal)
    return asdict(proposal)


@router.post("/v1/nexusmon/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, payload: Dict[str, Any] | None = None):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    if p.status not in (ProposalStatus.PENDING, ProposalStatus.APPROVED):
        raise HTTPException(status_code=400, detail="proposal not approvable")

    _ = payload
    p.approvals_given += 1
    if p.approvals_given >= p.approvals_required:
        p.status = ProposalStatus.APPROVED
    emit_proposal_event("approved", p)
    return asdict(p)


@router.post("/v1/nexusmon/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, payload: Dict[str, Any] | None = None):
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    if p.status not in (ProposalStatus.PENDING, ProposalStatus.APPROVED):
        raise HTTPException(status_code=400, detail="proposal not rejectable")

    _ = payload
    p.rejections_given += 1
    p.status = ProposalStatus.REJECTED
    emit_proposal_event("rejected", p)
    return asdict(p)


@router.post("/v1/nexusmon/proposals/{proposal_id}/apply")
async def apply_proposal(proposal_id: str, payload: Dict[str, Any] | None = None):
    """
    Marker only: actual code changes are performed by the operator/agent.
    This endpoint records that the proposal has been applied.
    """
    p = PROPOSALS.get(proposal_id)
    if not p:
        raise HTTPException(status_code=404, detail="proposal not found")
    if p.status != ProposalStatus.APPROVED:
        raise HTTPException(status_code=400, detail="proposal not approved")

    _ = payload
    p.status = ProposalStatus.APPLIED
    emit_proposal_event("applied", p)
    return asdict(p)
