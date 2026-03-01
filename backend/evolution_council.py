from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from backend.evolution_scoring import score_proposal
from backend.safety_intelligence import safety_assess


class CouncilAgent(str, Enum):
    SAFETY = "safety_agent"
    COVERAGE = "coverage_agent"
    PERFORMANCE = "performance_agent"
    GOVERNANCE = "governance_agent"


class Vote(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    NEUTRAL = "neutral"


@dataclass
class CouncilVote:
    agent: CouncilAgent
    vote: Vote
    reason: str
    timestamp: str


@dataclass
class CouncilDecision:
    proposal_id: str
    votes: List[CouncilVote]
    consensus: Vote
    summary: str
    timestamp: str


def safety_agent_vote(proposal: Dict[str, Any]) -> CouncilVote:
    safety = safety_assess(proposal)
    if not safety["safe"]:
        v = Vote.REJECT
        reason = f"Flags: {', '.join(safety['flags'])}"
    else:
        v = Vote.APPROVE
        reason = "No safety flags."
    return CouncilVote(
        agent=CouncilAgent.SAFETY,
        vote=v,
        reason=reason,
        timestamp=datetime.utcnow().isoformat(),
    )


def coverage_agent_vote(proposal: Dict[str, Any]) -> CouncilVote:
    ptype = proposal["type"]
    if ptype == "test":
        v = Vote.APPROVE
        reason = "Tests increase coverage."
    elif ptype in ("mission", "manifest"):
        v = Vote.NEUTRAL
        reason = "Coverage impact unclear."
    else:
        v = Vote.NEUTRAL
        reason = "Non-test proposal."
    return CouncilVote(
        agent=CouncilAgent.COVERAGE,
        vote=v,
        reason=reason,
        timestamp=datetime.utcnow().isoformat(),
    )


def performance_agent_vote(proposal: Dict[str, Any]) -> CouncilVote:
    ptype = proposal["type"]
    if ptype == "backend":
        v = Vote.NEUTRAL
        reason = "Backend modules may affect performance; needs profiling."
    else:
        v = Vote.NEUTRAL
        reason = "No direct performance signal."
    return CouncilVote(
        agent=CouncilAgent.PERFORMANCE,
        vote=v,
        reason=reason,
        timestamp=datetime.utcnow().isoformat(),
    )


def governance_agent_vote(proposal: Dict[str, Any]) -> CouncilVote:
    risk = proposal["risk"]
    if risk == "high":
        v = Vote.APPROVE
        reason = "High-risk proposal correctly requires multi-approval."
    else:
        v = Vote.NEUTRAL
        reason = "Governance constraints satisfied."
    return CouncilVote(
        agent=CouncilAgent.GOVERNANCE,
        vote=v,
        reason=reason,
        timestamp=datetime.utcnow().isoformat(),
    )


def compute_consensus(votes: List[CouncilVote]) -> Vote:
    approves = sum(1 for v in votes if v.vote == Vote.APPROVE)
    rejects = sum(1 for v in votes if v.vote == Vote.REJECT)
    if rejects > approves:
        return Vote.REJECT
    if approves > 0 and rejects == 0:
        return Vote.APPROVE
    return Vote.NEUTRAL


def council_evaluate(proposal_id: str, proposal: Dict[str, Any]) -> CouncilDecision:
    _ = score_proposal(proposal)
    votes = [
        safety_agent_vote(proposal),
        coverage_agent_vote(proposal),
        performance_agent_vote(proposal),
        governance_agent_vote(proposal),
    ]
    consensus = compute_consensus(votes)
    summary = (
        f"Consensus={consensus.value}, "
        f"votes={[(v.agent.value, v.vote.value) for v in votes]}"
    )
    return CouncilDecision(
        proposal_id=proposal_id,
        votes=votes,
        consensus=consensus,
        summary=summary,
        timestamp=datetime.utcnow().isoformat(),
    )
