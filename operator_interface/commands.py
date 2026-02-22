from typing import Any, Dict


def nudge_operator(message: str, state_snapshot: Dict[str, Any], intent: str) -> Dict[str, Any]:
    """Create a nudge artifact with mandatory context justification."""
    if not state_snapshot or not intent:
        raise ValueError("nudge_operator requires state_snapshot and intent")

    return {
        "type": "nudge",
        "message": message,
        "justification": {
            "intent": intent,
            "state_snapshot": state_snapshot,
        },
    }
