from datetime import datetime, timezone
from typing import Any, Dict

from jsonl_utils import write_jsonl

AUDIT_PATH = "data/audit.jsonl"


def log_event(
    event_type: str, role: str, details: Dict[str, Any], path: str = AUDIT_PATH
) -> Dict[str, Any]:
    """Write an auditable event with explicit role tag.

    Allowed roles: user, agent, system.
    """
    normalized_role = (role or "").strip().lower()
    if normalized_role not in {"user", "agent", "system"}:
        raise ValueError("role must be one of: user, agent, system")

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "role": normalized_role,
        "details": details or {},
    }
    write_jsonl(path, payload)
    return payload
