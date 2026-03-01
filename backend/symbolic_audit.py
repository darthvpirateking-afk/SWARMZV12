from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

AUDIT_LOG: List[Dict[str, Any]] = []


def append_audit_event(
    event: str,
    outcome: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "outcome": outcome,
        "details": details or {},
    }
    AUDIT_LOG.append(record)
    return record


def list_audit_events(limit: int = 400) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    return AUDIT_LOG[-limit:]

