from __future__ import annotations

from backend.entity.mood_modifiers import apply_override

DESTRUCTIVE_ACTIONS = ["delete_data", "exfiltrate", "pivot_network", "drop_persistence"]
HIGH_RISK_ACTIONS = ["exploit_cve", "brute_force", "scan_internal"]


def check_operator_override(
    loyalty: int, action: dict, operator_approved: bool, mood: str | None = "calm"
) -> bool:
    action_type = str(action.get("type", ""))

    if action_type in DESTRUCTIVE_ACTIONS:
        return bool(operator_approved)

    require_operator = bool(apply_override(False, "require_operator_approval", mood))
    if action_type in HIGH_RISK_ACTIONS and (loyalty >= 80 or require_operator):
        return bool(operator_approved)

    return True
