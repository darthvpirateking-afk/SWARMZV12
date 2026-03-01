import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from swarmz_runtime.core.operational_runtime import (
    OperationalRuntime,
    _extract_event_id,
    is_already_processed,
    mark_processed,
    verify_webhook_signature,
)

router = APIRouter()
_runtime = OperationalRuntime(Path(__file__).resolve().parent.parent.parent)
logger = logging.getLogger("swarmz.operational.webhooks")


class BlueprintCreateRequest(BaseModel):
    name: str
    spec: dict[str, Any] = Field(default_factory=dict)
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
async def payment_webhook(request: Request):
    raw_body = await request.body()
    signature_header = request.headers.get("X-Webhook-Signature", "")

    if not os.environ.get("PAYMENT_WEBHOOK_SECRET"):
        logger.error("[NEXUSMON] PAYMENT_WEBHOOK_SECRET not configured; failing closed")
        raise HTTPException(status_code=503, detail="Webhook security not configured")

    if not signature_header or not verify_webhook_signature(raw_body, signature_header):
        _log_security_event("forged_webhook", request)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    event_id = _extract_event_id(payload)
    if is_already_processed(event_id):
        _log_security_event("webhook_replay", request, event_id=event_id)
        return {"status": "already_processed"}

    order_id = payload.get("order_id")
    event = payload.get("event")
    if not isinstance(order_id, str) or not isinstance(event, str):
        raise HTTPException(status_code=400, detail="Missing order_id or event")

    result = _runtime.payment_webhook(order_id, event)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    mark_processed(event_id)
    return result


@router.post("/store/orders/{order_id}/fulfill")
def fulfill_order(order_id: str, payload: FulfillRequest | None = None):
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


def _log_security_event(
    event_type: str,
    request: Request,
    event_id: str | None = None,
) -> None:
    from addons.security import append_security_event

    details: dict[str, Any] = {
        "source_ip": request.client.host if request.client else "unknown",
        "path": str(request.url.path),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if event_id:
        details["event_id"] = event_id
    append_security_event(event_type, details)
