from __future__ import annotations

from typing import Any


RULE_HANDLERS = {
    "secret.found": "operator_alert",
    "flow.c2_pattern_detected": "high_priority_alert",
    "flow.exfil_pattern_detected": "containment_recommendation",
}


def evaluate_rule(event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    action = RULE_HANDLERS.get(event_name, "log_only")
    severity = "info"
    if event_name in {"secret.found", "flow.c2_pattern_detected", "flow.exfil_pattern_detected"}:
        severity = "high"

    return {
        "event": event_name,
        "action": action,
        "severity": severity,
        "payload": payload,
    }


def trigger_rule(event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return evaluate_rule(event_name=event_name, payload=payload)
