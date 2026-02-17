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

from core.safe_execution import prepare_action
from core.time_source import now
from core.ai_audit import log_decision

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

