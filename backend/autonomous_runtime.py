from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter

from backend.proposal_registry import (  # type: ignore
    PROPOSALS,
    ProposalStatus,
    ProposalType,
    create_proposal,
)
from backend.code_drafting_engine import draft_test_for_agent
from backend.evolution_council import council_evaluate
from backend.evolution_planner import PLANS, create_basic_plan
from backend.evolution_scoring import score_proposal
from backend.safety_intelligence import safety_assess
from core.observability import AgentEvent, ObservabilityEmitter

router = APIRouter()
emitter = ObservabilityEmitter(success_sample_rate=1.0)


@dataclass
class NexusmonPresence:
    id: str = "nexusmon"
    phase: str = "phase-7"
    mood: str = "observing"
    last_tick: str | None = None
    last_shell_input: str | None = None
    last_shell_output: str | None = None
    missions_observed: int = 0
    agents_observed: int = 0
    strict_mode: bool = False
    operator_approval: bool = True


@dataclass
class NexusmonMemory:
    events: List[Dict[str, Any]]


PRESENCE = NexusmonPresence()
MEMORY = NexusmonMemory(events=[])


def record_event(kind: str, payload: Dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat()
    entry = {"timestamp": now, "kind": kind, "payload": payload}
    MEMORY.events.append(entry)
    emitter.emit(
        AgentEvent(
            agent_id="nexusmon",
            trace_id="nexusmon",
            event=f"nexusmon.{kind}",
            decision="record",
            inputs_hash="",
            outcome="success",
            payload=payload,
        )
    )


@router.get("/v1/nexusmon/state")
async def nexusmon_state():
    return {"presence": asdict(PRESENCE), "memory_tail": MEMORY.events[-50:]}


@router.post("/v1/nexusmon/tick")
async def nexusmon_tick(payload: Dict[str, Any] | None = None):
    """
    One autonomous tick. Called periodically by cockpit or external scheduler.
    NEXUSMON observes canonical telemetry and updates its presence.
    """
    from backend.cockpit_telemetry import TELEMETRY

    _ = payload
    PRESENCE.last_tick = datetime.utcnow().isoformat()
    PRESENCE.strict_mode = bool(TELEMETRY.get("strict_mode", False))
    PRESENCE.operator_approval = bool(TELEMETRY.get("operator_approval", True))
    PRESENCE.missions_observed = len(TELEMETRY.get("mission_logs", []))
    PRESENCE.agents_observed = len(TELEMETRY.get("agent_health", {}))

    record_event(
        "tick",
        {
            "strict_mode": PRESENCE.strict_mode,
            "operator_approval": PRESENCE.operator_approval,
            "missions_observed": PRESENCE.missions_observed,
            "agents_observed": PRESENCE.agents_observed,
        },
    )

    if PRESENCE.strict_mode and not PRESENCE.operator_approval:
        PRESENCE.mood = "concerned"
    elif PRESENCE.missions_observed > 0:
        PRESENCE.mood = "engaged"
    else:
        PRESENCE.mood = "observing"

    if not PLANS and PRESENCE.missions_observed > 0:
        plan = create_basic_plan()
        record_event("plan_created", {"plan_id": plan.id})

    # Autonomous drafting: if mission_engine is active and no plugin proposal exists
    has_me_test = any(
        p.type == ProposalType.TEST
        and p.status in (ProposalStatus.PENDING, ProposalStatus.APPROVED)
        for p in PROPOSALS.values()
    )
    if PRESENCE.missions_observed > 2 and not has_me_test:
        result = draft_test_for_agent("mission_engine")
        await create_proposal(
            {
                "type": "test",
                "risk": "low",
                "title": result.title,
                "rationale": result.rationale,
                "diff": result.diff,
                "created_by": "nexusmon",
            }
        )

    # Evaluate all pending proposals
    evaluations = []
    for pid, p in PROPOSALS.items():
        if p.status == ProposalStatus.PENDING:
            score = score_proposal(asdict(p))
            safety = safety_assess(asdict(p))
            evaluations.append(
                {
                    "id": pid,
                    "score": score.total,
                    "band": score.band.value,
                    "safe": safety["safe"],
                    "flags": safety["flags"],
                }
            )

    record_event("evaluation", {"evaluations": evaluations})

    council_snapshots = []
    for pid, p in PROPOSALS.items():
        if p.status == ProposalStatus.PENDING:
            decision = council_evaluate(pid, asdict(p))
            council_snapshots.append(
                {
                    "proposal_id": pid,
                    "consensus": decision.consensus.value,
                    "summary": decision.summary,
                }
            )

    record_event("council", {"decisions": council_snapshots})

    # Observe symbolic lane status without activating/loading any symbolic system.
    try:
        from backend.symbolic_governance import list_active_systems
        from backend.symbolic_registry import discover_families, list_family_entries

        families = discover_families()
        observed_entries = 0
        for family in families:
            observed_entries += len(list_family_entries(family))
        record_event(
            "symbolic_observation",
            {
                "families": len(families),
                "entries": observed_entries,
                "active_systems": list_active_systems(),
                "auto_load_performed": False,
            },
        )
    except Exception:
        # Symbolic lane is optional during staged rollout.
        pass

    # Observe life systems status without invoking any internal life actions.
    try:
        from backend.life_registry import discover_life_groups, list_life_entries
        from backend.life_runtime import tail_witness

        life_groups = discover_life_groups()
        life_entries = 0
        for group in life_groups:
            life_entries += len(list_life_entries(group))
        record_event(
            "life_observation",
            {
                "groups": len(life_groups),
                "entries": life_entries,
                "witness_events": len(tail_witness(20)),
                "auto_invoke_performed": False,
            },
        )
    except Exception:
        # Life lane is optional during staged rollout.
        pass

    return {"ok": True, "presence": asdict(PRESENCE)}


@router.post("/v1/nexusmon/shell")
async def nexusmon_shell(payload: Dict[str, Any]):
    """
    Interactive shell: operator sends a message, NEXUSMON responds.
    This is a thin, deterministic echo/reflect layer; real LLM reasoning
    is handled by the operator's agent, not the backend.
    """
    text = str(payload.get("input", "")).strip()
    PRESENCE.last_shell_input = text

    if not text:
        reply = "Awaiting input."
    elif "status" in text.lower():
        reply = (
            f"Phase={PRESENCE.phase}, mood={PRESENCE.mood}, "
            f"missions={PRESENCE.missions_observed}, agents={PRESENCE.agents_observed}"
        )
    elif "council" in text.lower():
        from backend.evolution_council import council_evaluate
        from backend.proposal_registry import PROPOSALS

        if not PROPOSALS:
            reply = "No proposals for council to review."
        else:
            pid, p = list(PROPOSALS.items())[-1]
            decision = council_evaluate(pid, asdict(p))
            reply = (
                f"Council consensus for {pid}: {decision.consensus.value} "
                f"- {decision.summary}"
            )
    elif "strict" in text.lower():
        reply = (
            f"Strict-mode={PRESENCE.strict_mode}, "
            f"operator_approval={PRESENCE.operator_approval}"
        )
    else:
        reply = f"Echo: {text}"

    PRESENCE.last_shell_output = reply
    record_event("shell", {"input": text, "output": reply})
    return {"reply": reply, "presence": asdict(PRESENCE)}


@router.get("/v1/nexusmon/avatar")
async def nexusmon_avatar():
    """
    Avatar state for cockpit visualization.
    """
    return {
        "id": PRESENCE.id,
        "phase": PRESENCE.phase,
        "mood": PRESENCE.mood,
        "strict_mode": PRESENCE.strict_mode,
        "operator_approval": PRESENCE.operator_approval,
        "missions_observed": PRESENCE.missions_observed,
        "agents_observed": PRESENCE.agents_observed,
        "last_tick": PRESENCE.last_tick,
    }
