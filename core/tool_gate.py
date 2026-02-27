# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/tool_gate.py â€” Gate every AIâ€‘suggested tool invocation through review.

ALL outputs from the AI companion or mission solver that resemble
executable actions (commands, API calls, file writes, purchases, messages)
are intercepted here and routed to prepared_actions/ via safe_execution.

The operator must explicitly approve and execute each action.

Functions:
  gate(action_type, payload, mission_id, reason) â†’ proposal path
  is_allowed(action_type) â†’ bool  (always True for prepareâ€‘only; reserved for future denyâ€‘lists)
"""

from typing import Any, Dict, Optional
import logging
import time

from core.safe_execution import prepare_action
from core.time_source import now
from core.ai_audit import log_decision
from core.governance_perf import perf_ledger

# Governance layers (P0 → P1 → P2)
from core import (
    reversible,
    integrity,
    scoring,
    threshold,
    sovereign,
    shadow_channel,
    geometry,
    boundaries,
    emergence,
    uplift,
    stabilization,
    exploration,
)

logger = logging.getLogger(__name__)

# Action type â†’ prepared_actions category
_CATEGORY_MAP = {
    "shell_command": "commands",
    "command": "commands",
    "api_call": "commands",
    "file_write": "commands",
    "message": "messages",
    "email": "messages",
    "notification": "messages",
    "schedule": "schedules",
    "calendar": "schedules",
    "reminder": "schedules",
    "purchase": "purchases",
    "payment": "purchases",
    "subscription": "purchases",
    "preemptive": "preemptive",
}


def _resolve_category(action_type: str) -> str:
    return _CATEGORY_MAP.get(action_type.lower(), "commands")


def is_allowed(action_type: str) -> bool:
    """Check if an action type is permitted.

    Under prepare_only policy, everything is allowed because nothing
    actually executes â€” it all goes to proposals.  This function exists
    as a hook for future denyâ€‘lists.
    """
    return True


def run_governance_pipeline(
    action: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run full governance pipeline (P0 → P1 → P2).

    Returns:
        {"passed": bool, "layer": str, "reason": str, "metadata": dict}
    """
    _pipeline_start = time.perf_counter()

    def _ms(t0: float) -> float:
        return (time.perf_counter() - t0) * 1000.0

    # P0.1 - Geometry (transform context first)
    _t = time.perf_counter()
    geometry_result = geometry.evaluate(action, context)
    perf_ledger.record("geometry", _ms(_t), geometry_result.passed)
    if not geometry_result.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": geometry_result.layer,
            "reason": geometry_result.reason,
            "metadata": geometry_result.metadata,
        }

    # Use transformed context for remaining layers
    transformed_context = geometry_result.metadata.get("transformed_context", context)

    # P0.2 - Integrity (structural constraints)
    _t = time.perf_counter()
    integrity_result = integrity.evaluate(action, transformed_context)
    integrity_with_sovereign = sovereign.resolve_override(
        integrity_result, action, transformed_context
    )
    perf_ledger.record("integrity", _ms(_t), integrity_with_sovereign.passed)
    if not integrity_with_sovereign.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": integrity_with_sovereign.layer,
            "reason": integrity_with_sovereign.reason,
            "metadata": integrity_with_sovereign.metadata,
        }

    # P0.3 - Scoring (risk assessment)
    _t = time.perf_counter()
    scoring_result = scoring.evaluate(action, transformed_context)
    scoring_with_sovereign = sovereign.resolve_override(
        scoring_result, action, transformed_context
    )
    perf_ledger.record("scoring", _ms(_t), scoring_with_sovereign.passed)
    if not scoring_with_sovereign.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": scoring_with_sovereign.layer,
            "reason": scoring_with_sovereign.reason,
            "metadata": scoring_with_sovereign.metadata,
        }

    # P0.4 - Threshold (activation gates)
    _t = time.perf_counter()
    threshold_result = threshold.evaluate(action, transformed_context)
    threshold_with_sovereign = sovereign.resolve_override(
        threshold_result, action, transformed_context
    )
    perf_ledger.record("threshold", _ms(_t), threshold_with_sovereign.passed)
    if not threshold_with_sovereign.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": threshold_with_sovereign.layer,
            "reason": threshold_with_sovereign.reason,
            "metadata": threshold_with_sovereign.metadata,
        }

    # P1.4 - Boundaries (domain crossing)
    _t = time.perf_counter()
    boundaries_result = boundaries.evaluate(action, transformed_context)
    perf_ledger.record("boundaries", _ms(_t), boundaries_result.passed)
    if not boundaries_result.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": boundaries_result.layer,
            "reason": boundaries_result.reason,
            "metadata": boundaries_result.metadata,
        }

    # P2.3 - Stabilization (oscillation check)
    _t = time.perf_counter()
    stabilization_result = stabilization.evaluate(action, transformed_context)
    perf_ledger.record("stabilization", _ms(_t), stabilization_result.passed)
    if not stabilization_result.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": stabilization_result.layer,
            "reason": stabilization_result.reason,
            "metadata": stabilization_result.metadata,
        }

    # P2.4 - Exploration (safety bounds)
    _t = time.perf_counter()
    exploration_result = exploration.evaluate(action, transformed_context)
    perf_ledger.record("exploration", _ms(_t), exploration_result.passed)
    if not exploration_result.passed:
        perf_ledger.record("_pipeline", _ms(_pipeline_start), False)
        return {
            "passed": False,
            "layer": exploration_result.layer,
            "reason": exploration_result.reason,
            "metadata": exploration_result.metadata,
        }

    # P2.1 - Emergence (pattern tracking - non-blocking)
    _t = time.perf_counter()
    emergence.evaluate(action, transformed_context)
    perf_ledger.record("emergence", _ms(_t), None)

    # P2.2 - Uplift (maturity tracking - non-blocking)
    _t = time.perf_counter()
    uplift.evaluate(action, transformed_context)
    perf_ledger.record("uplift", _ms(_t), None)

    # All layers passed — record full pipeline timing
    perf_ledger.record("_pipeline", _ms(_pipeline_start), True)
    return {
        "passed": True,
        "layer": "governance_pipeline",
        "reason": "All governance layers passed",
        "metadata": {
            "layers_evaluated": [
                "geometry",
                "integrity",
                "scoring",
                "threshold",
                "boundaries",
                "stabilization",
                "exploration",
            ],
            "pipeline_ms": round(_ms(_pipeline_start), 3),
        },
    }


def gate(
    action_type: str,
    payload: Dict[str, Any],
    mission_id: str = "",
    reason: str = "",
    risk_level: str = "low",
    expected_effect: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Gate an AIâ€‘suggested action into prepared_actions/.

    Returns:
      {"ok": True, "proposal_dir": str, "category": str}
      or {"ok": False, "error": str}
    """
    if not is_allowed(action_type):
        return {"ok": False, "error": f"action type '{action_type}' denied by policy"}

    category = _resolve_category(action_type)

    # Determine a safe mission_id if not provided
    if not mission_id:
        mission_id = f"gate_{int(__import__('time').time() * 1000)}"

    # Build action and context for governance
    action = {
        "action_type": action_type,
        "payload": payload,
        "mission_id": mission_id,
    }

    context = {
        "risk_level": risk_level,
        "reason": reason,
        "category": category,
    }

    # Run governance pipeline
    governance_result = run_governance_pipeline(action, context)

    # Wrap result with shadow channel
    shadow_wrapped = shadow_channel.wrap_layer_result(
        reversible.LayerResult(
            layer=governance_result["layer"],
            passed=governance_result["passed"],
            reason=governance_result["reason"],
            metadata=governance_result["metadata"],
            timestamp=now(),
        ),
        opacity_level=shadow_channel.OpacityLevel.PARTIAL,
    )

    if not governance_result["passed"]:
        logger.warning(
            f"Governance blocked: {action_type} by {governance_result['layer']}"
        )

        # Audit the rejection
        log_decision(
            decision_type="governance_block",
            mission_id=mission_id,
            strategy=action_type,
            rationale=governance_result["reason"][:200],
            source=governance_result["layer"],
            extra=governance_result["metadata"],
        )

        return {
            "ok": False,
            "error": shadow_wrapped.reason,
            "blocked_by": governance_result["layer"],
        }

    logger.info(f"Governance approved: {action_type}")

    action_data = {
        "action_type": action_type,
        "payload": payload,
        "gated_at": now(),
    }

    proposal_dir = prepare_action(
        category=category,
        mission_id=mission_id,
        action_data=action_data,
        reason=reason,
        expected_effect=expected_effect,
        risk_level=risk_level,
    )

    # Audit the gating decision
    log_decision(
        decision_type="tool_gate",
        mission_id=mission_id,
        strategy=action_type,
        rationale=reason[:200],
        source="tool_gate",
        extra={"category": category, "risk_level": risk_level},
    )

    return {"ok": True, "proposal_dir": proposal_dir, "category": category}
