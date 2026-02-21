# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Dispatch endpoints — sovereign dispatch and mission dispatch."""

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from swarmz_runtime.api.models import MissionDispatchRequest, SovereignDispatch

router = APIRouter(tags=["dispatch"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _ROOT_DIR / "data"


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


@router.post("/v1/dispatch")
def dispatch(req: MissionDispatchRequest, request: Request):
    """Dispatch a mission via contract validation + engine."""
    from swarmz_runtime.core.system_primitives import SystemPrimitivesRuntime

    op_key = request.headers.get("X-Operator-Key")
    if not op_key:
        raise HTTPException(status_code=401, detail="operator key required")

    primitives_runtime = SystemPrimitivesRuntime(_ROOT_DIR)
    contract = primitives_runtime.validate_contract(
        {
            "action_type": "dispatch",
            "payload": {
                "goal": req.goal,
                "category": req.category,
                "constraints": req.constraints,
            },
            "safety": {"irreversible": False, "operator_approved": True},
            "resources": {"cpu": 1.0, "memory_mb": 512, "timeout_s": 60},
            "meta": {"source": "api.dispatch", "weaver_validated": True},
        },
        regime="dispatch",
    )
    if not contract["validation"]["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "contract_rejected",
                "violations": contract["validation"]["violations"],
                "companion_notified": contract["companion_notified"],
            },
        )

    from swarmz_runtime.core.engine import SwarmzEngine

    engine = SwarmzEngine(data_dir=str(_DATA_DIR))
    created = engine.create_mission(req.goal, req.category, req.constraints)
    run = (
        engine.run_mission(created.get("mission_id", ""))
        if created.get("mission_id")
        else {"error": "create_failed"}
    )
    return {"created": created, "run": run, "contract": contract["validation"]}


@router.post("/v1/sovereign/dispatch")
def sovereign_dispatch(body: SovereignDispatch):
    """Sovereign-level dispatch with contract validation."""
    from swarmz_runtime.core.system_primitives import SystemPrimitivesRuntime

    primitives_runtime = SystemPrimitivesRuntime(_ROOT_DIR)
    contract = primitives_runtime.validate_contract(
        {
            "action_type": "create_mission",
            "payload": {
                "intent": body.intent,
                "scope": body.scope,
                "limits": body.limits,
            },
            "safety": {"irreversible": False, "operator_approved": True},
            "resources": {"cpu": 1.0, "memory_mb": 256, "timeout_s": 30},
            "meta": {"source": "api.sovereign_dispatch", "weaver_validated": True},
        },
        regime="sovereign_dispatch",
    )
    if not contract["validation"]["allowed"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "contract_rejected",
                "violations": contract["validation"]["violations"],
                "companion_notified": contract["companion_notified"],
            },
        )

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    mission_id = f"M-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(4)}"
    mission = {
        "mission_id": mission_id,
        "intent": body.intent,
        "scope": body.scope,
        "limits": body.limits,
        "status": "PENDING",
        "timestamp": ts,
    }
    missions_file = _DATA_DIR / "missions.jsonl"
    audit_file = _DATA_DIR / "audit.jsonl"
    _append_jsonl(missions_file, mission)
    _append_jsonl(
        audit_file, {"ts": ts, "event": "sovereign_dispatch", "mission_id": mission_id}
    )
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "PENDING",
        "contract": contract["validation"],
    }
