from fastapi import APIRouter
from pydantic import BaseModel, Field

from swarmz_runtime.core.operator_charter import (
    charter_document,
    doctrine_document,
    evaluate_change_flow,
    evaluate_operating_matrix,
    evaluate_prime_directive,
    future_contract,
)

router = APIRouter()


class PrimeDirectiveEvalRequest(BaseModel):
    intent: str = ""
    explicit: bool = False
    action: str = ""
    requested_autonomy: int = Field(default=0, ge=0, le=100)
    max_autonomy: int = Field(default=50, ge=0, le=100)


class ChangeFlowEvalRequest(BaseModel):
    execution_model: str = "event_driven"
    write_mode: str = "append_only"
    history_mutable: bool = False
    uses_polling_loops: bool = False
    uses_file_sync: bool = False
    event_driven: bool = True
    in_memory_passing: bool = True
    replayable_steps: bool = True
    external_verification: bool = True


class OperatingMatrixEvalRequest(BaseModel):
    has_artifact: bool = True
    has_verification: bool = True
    has_outcome: bool = True
    external_verification: bool = True
    replayable_step: bool = True
    irreversible_action: bool = False
    operator_approved: bool = False


@router.get("/charter")
def get_charter():
    return {"ok": True, "charter": charter_document()}


@router.get("/charter/doctrine")
def get_doctrine():
    return {"ok": True, "doctrine": doctrine_document()}


@router.get("/charter/future-contract")
def get_future_contract():
    return {"ok": True, "future_contract": future_contract()}


@router.post("/charter/evaluate")
def evaluate(payload: PrimeDirectiveEvalRequest):
    decision = evaluate_prime_directive(
        intent=payload.intent,
        explicit=payload.explicit,
        action=payload.action,
        requested_autonomy=payload.requested_autonomy,
        max_autonomy=payload.max_autonomy,
    )
    return {"ok": True, "decision": decision.as_dict()}


@router.post("/charter/evaluate/change-flow")
def evaluate_change_flow_path(payload: ChangeFlowEvalRequest):
    decision = evaluate_change_flow(
        execution_model=payload.execution_model,
        write_mode=payload.write_mode,
        history_mutable=payload.history_mutable,
        uses_polling_loops=payload.uses_polling_loops,
        uses_file_sync=payload.uses_file_sync,
        event_driven=payload.event_driven,
        in_memory_passing=payload.in_memory_passing,
        replayable_steps=payload.replayable_steps,
        external_verification=payload.external_verification,
    )
    return {"ok": True, "decision": decision}


@router.post("/charter/evaluate/operating-matrix")
def evaluate_operating_matrix_path(payload: OperatingMatrixEvalRequest):
    decision = evaluate_operating_matrix(
        has_artifact=payload.has_artifact,
        has_verification=payload.has_verification,
        has_outcome=payload.has_outcome,
        external_verification=payload.external_verification,
        replayable_step=payload.replayable_step,
        irreversible_action=payload.irreversible_action,
        operator_approved=payload.operator_approved,
    )
    return {"ok": True, "decision": decision}
