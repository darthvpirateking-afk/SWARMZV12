from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

from fastapi import APIRouter

from backend.proposal_registry import ProposalRisk, ProposalType, create_proposal

router = APIRouter()


@dataclass
class DraftResult:
    title: str
    rationale: str
    diff: Dict[str, Any]


def draft_test_for_agent(agent_id: str) -> DraftResult:
    return DraftResult(
        title=f"Add regression test for {agent_id}",
        rationale=f"Agent {agent_id} executed missions; ensure behavior is covered.",
        diff={
            "target": f"tests/test_{agent_id}_regression.py",
            "kind": "file",
            "content_hint": (
                f"Add tests covering {agent_id} happy path, failure modes, "
                "and strict-mode behavior."
            ),
        },
    )


def draft_plugin_skeleton(plugin_id: str) -> DraftResult:
    return DraftResult(
        title=f"Add plugin skeleton: {plugin_id}",
        rationale=f"Plugin {plugin_id} missing; drafting initial structure.",
        diff={
            "target": f"plugins/{plugin_id}.py",
            "kind": "file",
            "content_hint": (
                "Create minimal plugin class with on_init, on_activate, run, "
                "on_deactivate, and unload methods."
            ),
        },
    )


def draft_backend_module(name: str) -> DraftResult:
    return DraftResult(
        title=f"Add backend module: {name}",
        rationale=f"Backend module {name} missing; drafting safe scaffold.",
        diff={
            "target": f"backend/{name}.py",
            "kind": "file",
            "content_hint": (
                "Add FastAPI router, safe deterministic endpoints, "
                "and placeholder logic."
            ),
        },
    )


@router.post("/v1/nexusmon/draft")
async def draft(payload: Dict[str, Any]):
    """
    NEXUSMON drafts code based on requested type.
    """
    draft_type = payload.get("draft_type")
    target = payload.get("target")

    if draft_type == "test":
        result = draft_test_for_agent(target)
        risk = ProposalRisk.LOW
        ptype = ProposalType.TEST
    elif draft_type == "plugin":
        result = draft_plugin_skeleton(target)
        risk = ProposalRisk.MEDIUM
        ptype = ProposalType.PLUGIN
    elif draft_type == "backend":
        result = draft_backend_module(target)
        risk = ProposalRisk.HIGH
        ptype = ProposalType.BACKEND
    else:
        return {"error": "unknown draft_type"}

    proposal = await create_proposal(
        {
            "type": ptype.value,
            "risk": risk.value,
            "title": result.title,
            "rationale": result.rationale,
            "diff": result.diff,
            "created_by": "nexusmon",
        }
    )

    return {"proposal": proposal, "draft": asdict(result)}
