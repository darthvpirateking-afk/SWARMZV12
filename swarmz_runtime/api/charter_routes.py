from fastapi import APIRouter
from pydantic import BaseModel, Field

from swarmz_runtime.core.operator_charter import charter_document, evaluate_prime_directive


router = APIRouter()


class PrimeDirectiveEvalRequest(BaseModel):
    intent: str = ""
    explicit: bool = False
    action: str = ""
    requested_autonomy: int = Field(default=0, ge=0, le=100)
    max_autonomy: int = Field(default=50, ge=0, le=100)


@router.get("/charter")
def get_charter():
    return {"ok": True, "charter": charter_document()}


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
