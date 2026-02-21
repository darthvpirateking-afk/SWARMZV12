# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter, HTTPException, Depends
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()


class OperatorCommand(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}
    operator_key: str


class SovereigntyCheck(BaseModel):
    operator_key: str
    action: str
    scope: str = "global"


@router.post("/command")
def execute_operator_command(request: OperatorCommand):
    """Execute precision operator commands with sovereignty validation."""
    engine = get_engine()

    # Validate operator sovereignty
    if not engine.validate_operator_sovereignty(request.operator_key):
        raise HTTPException(
            status_code=403, detail="Operator sovereignty validation failed"
        )

    # Execute command with precision
    result = engine.execute_operator_command(
        command=request.command,
        parameters=request.parameters,
        operator_key=request.operator_key,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/sovereignty/check")
def check_operator_sovereignty(request: SovereigntyCheck):
    """Validate operator sovereignty for actions."""
    engine = get_engine()

    is_sovereign = engine.validate_operator_sovereignty(
        request.operator_key, action=request.action, scope=request.scope
    )

    return {
        "sovereign": is_sovereign,
        "action": request.action,
        "scope": request.scope,
        "timestamp": engine.get_current_timestamp(),
    }


@router.get("/sovereignty/status")
def get_sovereignty_status(operator_key: str):
    """Get current sovereignty status for operator."""
    engine = get_engine()

    status = engine.get_sovereignty_status(operator_key)

    return status


@router.post("/maintenance")
def schedule_maintenance():
    result = get_engine().schedule_maintenance()
    return result
