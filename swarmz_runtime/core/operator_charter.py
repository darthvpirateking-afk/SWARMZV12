from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


OPERATOR_PRIME_DIRECTIVE = (
    "All systems, agents, organisms, and autonomous processes must act in service of the "
    "Operator's intent, protection, and advantage—never in conflict with them. When intent "
    "is unclear, systems default to safety, transparency, and minimal action. When intent is "
    "explicit, systems execute with precision, auditability, and alignment."
)

OPERATOR_CHARTER_SECTIONS = [
    "Operator Identity",
    "Safety & Governance",
    "Value System",
    "Autonomy Boundaries",
    "Evolution Rules",
    "Federation Principles",
    "Operator Rights",
    "System Purpose",
]


@dataclass
class CharterDecision:
    mode: str
    allowed: bool
    rationale: str
    constraints: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "allowed": self.allowed,
            "rationale": self.rationale,
            "constraints": self.constraints,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }


def evaluate_prime_directive(intent: str, explicit: bool, action: str, requested_autonomy: int, max_autonomy: int) -> CharterDecision:
    if not intent.strip() and not explicit:
        return CharterDecision(
            mode="minimal_action",
            allowed=False,
            rationale="Operator intent unclear; defaulting to safety and minimal action.",
            constraints=["require_operator_clarification", "freeze_high_risk_execution"],
        )

    capped = min(100, max(0, requested_autonomy))
    if capped > max_autonomy:
        return CharterDecision(
            mode="bounded_execution",
            allowed=False,
            rationale="Requested autonomy exceeds operator profile maximum.",
            constraints=[f"autonomy_cap={max_autonomy}", "require_operator_override"],
        )

    is_high_risk = any(k in action.lower() for k in ["rollback", "withdraw", "execute", "publish", "high_risk"])
    constraints = ["ledger_log_required", "policy_engine_required", "governance_agent_required"]
    if is_high_risk:
        constraints.append("approval_required_for_irreversible")

    return CharterDecision(
        mode="aligned_execution",
        allowed=True,
        rationale="Intent explicit and within operator bounds; execute with auditability and alignment.",
        constraints=constraints,
    )


def charter_document() -> Dict[str, Any]:
    return {
        "prime_directive": OPERATOR_PRIME_DIRECTIVE,
        "sections": OPERATOR_CHARTER_SECTIONS,
    }
