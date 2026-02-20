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

SYSTEM_PRIMITIVES = {
    "system": "state + rules + transitions + time",
    "truth": "immutable_event_log",
    "state": "cache(history)",
    "change": "append_only",
    "authoritative_truth": "ordered_event_log",
}

RUNTIME_REFACTOR_REQUIREMENTS = {
    "remove_polling_loops": True,
    "remove_file_based_synchronization": True,
    "use_event_driven_execution": True,
    "use_in_memory_data_passing": True,
    "enable_concurrency": True,
    "cache_repeated_operations": True,
    "reduce_unnecessary_logging": True,
    "consolidate_main_loop_into_event_scheduler": True,
}

SWARMZ_OPERATING_MATRIX = {
    "action": {
        "no_artifact": "nonexistent",
        "no_verification": "rejected",
        "no_outcome": "ignored",
        "external_verification": "accepted",
    },
    "state": {
        "mutable_history": "corruption",
        "immutable_log": "reconstruction",
    },
    "execution": {
        "direct_change": "dangerous",
        "parallel_test": "safe",
        "shadow_run": "safe",
        "replayable_step": "trustworthy",
        "irreversible_action": "operator_required",
    },
}


FUTURE_CHANGE_VECTOR = {
    "stability": "increases",
    "anticipation": "emerges",
    "parallelism": "expands",
    "federation": "activates",
    "operator_leverage": "compounds",
}


FUTURE_INVARIANTS = [
    "doctrine",
    "architecture",
    "sovereignty",
    "safety",
    "determinism",
    "event_driven_nature",
    "immutable_history",
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


def evaluate_prime_directive(
    intent: str, explicit: bool, action: str, requested_autonomy: int, max_autonomy: int
) -> CharterDecision:
    if not intent.strip() and not explicit:
        return CharterDecision(
            mode="minimal_action",
            allowed=False,
            rationale="Operator intent unclear; defaulting to safety and minimal action.",
            constraints=[
                "require_operator_clarification",
                "freeze_high_risk_execution",
            ],
        )

    capped = min(100, max(0, requested_autonomy))
    if capped > max_autonomy:
        return CharterDecision(
            mode="bounded_execution",
            allowed=False,
            rationale="Requested autonomy exceeds operator profile maximum.",
            constraints=[f"autonomy_cap={max_autonomy}", "require_operator_override"],
        )

    is_high_risk = any(
        k in action.lower()
        for k in ["rollback", "withdraw", "execute", "publish", "high_risk"]
    )
    constraints = [
        "ledger_log_required",
        "policy_engine_required",
        "governance_agent_required",
    ]
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


def doctrine_document() -> Dict[str, Any]:
    return {
        "system_primitives": SYSTEM_PRIMITIVES,
        "runtime_refactor_requirements": RUNTIME_REFACTOR_REQUIREMENTS,
        "operating_matrix": SWARMZ_OPERATING_MATRIX,
        "future_change_vector": FUTURE_CHANGE_VECTOR,
        "future_invariants": FUTURE_INVARIANTS,
        "primary_task": "control_change_flow",
        "primary_safety_mechanism": "immutable_audit + external_validation + replayability",
    }


def future_contract() -> Dict[str, Any]:
    return {
        "changes": FUTURE_CHANGE_VECTOR,
        "does_not_change": FUTURE_INVARIANTS,
        "constraint": "all future upgrades must preserve doctrine and deterministic event-driven immutable execution",
    }


def evaluate_change_flow(
    *,
    execution_model: str,
    write_mode: str,
    history_mutable: bool,
    uses_polling_loops: bool,
    uses_file_sync: bool,
    event_driven: bool,
    in_memory_passing: bool,
    replayable_steps: bool,
    external_verification: bool,
) -> Dict[str, Any]:
    violations: List[str] = []
    constraints: List[str] = ["ordered_event_log_required", "append_only_required"]

    if write_mode != "append_only":
        violations.append("write_mode_must_be_append_only")
    if history_mutable:
        violations.append("history_mutation_forbidden")
    if uses_polling_loops:
        violations.append("polling_loops_disallowed")
    if uses_file_sync:
        violations.append("file_based_sync_disallowed")
    if not event_driven:
        violations.append("event_driven_execution_required")
    if not in_memory_passing:
        violations.append("in_memory_data_passing_required")
    if not replayable_steps:
        violations.append("replayable_steps_required")
    if not external_verification:
        violations.append("external_verification_required")

    if execution_model not in {"sequential", "parallel", "event_driven"}:
        violations.append("execution_model_invalid")
    if execution_model == "parallel":
        constraints.append("collision_control_required")
        constraints.append("survivable_path_selection_required")

    allowed = len(violations) == 0
    mode = "aligned_change_flow" if allowed else "blocked_change_flow"
    rationale = (
        "Change flow aligned with immutable, event-driven doctrine."
        if allowed
        else "Change flow violates immutable/event-driven doctrine constraints."
    )

    return {
        "mode": mode,
        "allowed": allowed,
        "rationale": rationale,
        "constraints": constraints,
        "violations": violations,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def evaluate_operating_matrix(
    *,
    has_artifact: bool,
    has_verification: bool,
    has_outcome: bool,
    external_verification: bool,
    replayable_step: bool,
    irreversible_action: bool,
    operator_approved: bool,
) -> Dict[str, Any]:
    violations: List[str] = []

    if not has_artifact:
        violations.append("no_artifact_nonexistent")
    if not has_verification:
        violations.append("no_verification_rejected")
    if not has_outcome:
        violations.append("no_outcome_ignored")
    if not external_verification:
        violations.append("external_verification_required")
    if not replayable_step:
        violations.append("replayable_step_required")
    if irreversible_action and not operator_approved:
        violations.append("irreversible_action_requires_operator")

    allowed = len(violations) == 0
    return {
        "mode": "matrix_pass" if allowed else "matrix_block",
        "allowed": allowed,
        "rationale": (
            "Operating matrix constraints satisfied."
            if allowed
            else "Operating matrix rejected action."
        ),
        "violations": violations,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
