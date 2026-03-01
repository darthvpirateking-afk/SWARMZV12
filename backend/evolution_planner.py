from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from backend.proposal_registry import ProposalRisk, ProposalType, create_proposal


@dataclass
class EvolutionStep:
    id: str
    title: str
    description: str
    target: str
    kind: str
    status: str


@dataclass
class EvolutionPlan:
    id: str
    created_at: str
    horizon: str
    goal: str
    steps: List[EvolutionStep]


PLANS: Dict[str, EvolutionPlan] = {}


def next_plan_id() -> str:
    return f"plan-{len(PLANS) + 1:03d}"


def create_basic_plan() -> EvolutionPlan:
    now = datetime.utcnow().isoformat()
    pid = next_plan_id()
    steps = [
        EvolutionStep(
            id="step-1",
            title="Strengthen mission_engine tests",
            description="Add regression tests for mission_engine behavior.",
            target="mission_engine",
            kind="test",
            status="planned",
        ),
        EvolutionStep(
            id="step-2",
            title="Introduce example plugin",
            description="Add example_plugin skeleton for future missions.",
            target="example_plugin",
            kind="plugin",
            status="planned",
        ),
    ]
    plan = EvolutionPlan(
        id=pid,
        created_at=now,
        horizon="short",
        goal="Increase reliability and extensibility of mission pipeline.",
        steps=steps,
    )
    PLANS[pid] = plan
    return plan


async def realize_step(step: EvolutionStep):
    if step.kind == "test":
        ptype = ProposalType.TEST
        risk = ProposalRisk.LOW
        diff = {
            "target": f"tests/test_{step.target}_plan_regression.py",
            "kind": "file",
            "content_hint": "Add regression tests for evolution plan.",
        }
    elif step.kind == "plugin":
        ptype = ProposalType.PLUGIN
        risk = ProposalRisk.MEDIUM
        diff = {
            "target": f"plugins/{step.target}.py",
            "kind": "file",
            "content_hint": "Add plugin skeleton for evolution plan.",
        }
    else:
        ptype = ProposalType.DOC
        risk = ProposalRisk.LOW
        diff = {
            "target": f"docs/{step.target}_plan.md",
            "kind": "file",
            "content_hint": "Describe evolution step.",
        }

    await create_proposal(
        {
            "type": ptype.value,
            "risk": risk.value,
            "title": step.title,
            "rationale": step.description,
            "diff": diff,
            "created_by": "nexusmon",
        }
    )
    step.status = "proposed"
