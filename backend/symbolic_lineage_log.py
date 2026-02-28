from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

LINEAGE_LOG: List[Dict[str, Any]] = []


def append_lineage_record(
    action: str,
    target: str,
    operator_approved: bool,
    ritual_confirmed: bool,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "target": target,
        "operator_approved": operator_approved,
        "ritual_confirmed": ritual_confirmed,
        "details": details or {},
    }
    LINEAGE_LOG.append(record)
    return record


def list_lineage_records(limit: int = 200) -> List[Dict[str, Any]]:
    if limit <= 0:
        return []
    return LINEAGE_LOG[-limit:]

