from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from swarmz_runtime.core.operational_runtime import OperationalRuntime

router = APIRouter()
_runtime = OperationalRuntime(Path(__file__).resolve().parent.parent.parent)


class BlueprintCreateRequest(BaseModel):
    name: str
    spec: Dict[str, Any] = Field(default_factory=dict)
    owner: str = "operator"


class OfferCreateRequest(BaseModel):
    blueprint_id: str
    title: str
    price_cents: int = Field(ge=1)
    cost_cents: int = Field(ge=0)
    spend: float = 0.0
    approved: bool = False
    refund_rate: float = 0.0


class CheckoutRequest(BaseModel):
    sku: str
    quantity: int = Field(default=1, ge=1)
    payment_provider: str = "manual"


class PaymentWebhookRequest(BaseModel):
    order_id: str
    event: str


class FulfillRequest(BaseModel):
    mode: str = "digital"


class AutonomyCycleRequest(BaseModel):
    cycle_label: str = "default"


@router.get("/policy/rules")
def policy_rules():
    return {"ok": True, "rules": _runtime.policy.rules}


@router.post("/blueprints")
def create_blueprint(payload: BlueprintCreateRequest):
    return {
        "ok": True,
        "blueprint": _runtime.create_blueprint(
            payload.name, payload.spec, payload.owner
        ),
    }


@router.post("/blueprints/{blueprint_id}/validate")
def validate_blueprint(blueprint_id: str):
    result = _runtime.validate_blueprint(blueprint_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"ok": True, "validation": result}


@router.post("/offers")
def create_offer(payload: OfferCreateRequest):
    result = _runtime.create_offer(
        blueprint_id=payload.blueprint_id,
        title=payload.title,
        price_cents=payload.price_cents,
        cost_cents=payload.cost_cents,
        spend=payload.spend,
        approved=payload.approved,
        refund_rate=payload.refund_rate,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"ok": True, "offer": result}


@router.get("/store/catalog")
def list_catalog():
    rows = _runtime.list_catalog()
    return {"ok": True, "items": rows, "count": len(rows)}


@router.post("/store/checkout")
def checkout(payload: CheckoutRequest):
    result = _runtime.checkout(payload.sku, payload.quantity, payload.payment_provider)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"ok": True, "order": result}


@router.post("/store/payment-webhook")
def payment_webhook(payload: PaymentWebhookRequest):
    result = _runtime.payment_webhook(payload.order_id, payload.event)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/store/orders/{order_id}/fulfill")
def fulfill_order(order_id: str, payload: Optional[FulfillRequest] = None):
    mode = payload.mode if payload else "digital"
    result = _runtime.fulfill_order(order_id, mode=mode)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/ledger")
def ledger(limit: int = 50):
    rows = _runtime.ledger_tail(limit)
    return {"ok": True, "entries": rows, "count": len(rows)}


@router.post("/autonomy/cycle")
def autonomy_cycle(payload: AutonomyCycleRequest):
    return _runtime.run_autonomy_cycle(payload.cycle_label)
