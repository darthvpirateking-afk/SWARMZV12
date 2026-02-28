from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException, Request

from backend.symbolic_audit import append_audit_event
from backend.symbolic_lineage_log import append_lineage_record

ACTIVE_SYMBOLIC_SYSTEMS: set[str] = set()


def _operator_approved(request: Request) -> bool:
    header = request.headers.get("X-Operator-Approval", "")
    return header.strip().lower() in {"1", "true", "approved", "yes"}


def _ritual_confirmed(payload: Dict[str, Any]) -> bool:
    confirmation = payload.get("ritual_confirmation", {})
    if not isinstance(confirmation, dict):
        return False
    return bool(confirmation.get("confirmed", False))


def enforce_operator_protocol(
    request: Request,
    payload: Dict[str, Any],
    action: str,
    target: str,
) -> Dict[str, Any]:
    approved = _operator_approved(request)
    confirmed = _ritual_confirmed(payload)

    if not approved:
        append_audit_event(
            event="symbolic.governance.denied",
            outcome="rejected",
            details={"action": action, "target": target, "reason": "missing-approval"},
        )
        raise HTTPException(
            status_code=403,
            detail="operator approval required via X-Operator-Approval header",
        )

    if not confirmed:
        append_audit_event(
            event="symbolic.governance.denied",
            outcome="rejected",
            details={
                "action": action,
                "target": target,
                "reason": "missing-ritual-confirmation",
            },
        )
        raise HTTPException(status_code=400, detail="ritual confirmation required")

    lineage = append_lineage_record(
        action=action,
        target=target,
        operator_approved=True,
        ritual_confirmed=True,
        details={"governed": True},
    )
    audit = append_audit_event(
        event="symbolic.governance.approved",
        outcome="success",
        details={"action": action, "target": target},
    )
    return {"lineage": lineage, "audit": audit}


def activate_symbolic_system(symbolic_id: str) -> None:
    ACTIVE_SYMBOLIC_SYSTEMS.add(symbolic_id)


def list_active_systems() -> list[str]:
    return sorted(ACTIVE_SYMBOLIC_SYSTEMS)

