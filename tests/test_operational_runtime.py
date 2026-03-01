import hashlib
import hmac
import importlib
import json
from pathlib import Path


def test_policy_rules_available(client):
    response = client.get("/v1/policy/rules")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert any("no_publish" in rule for rule in payload["rules"])


def test_blueprint_to_fulfillment_pipeline(client, tmp_path, monkeypatch):
    ops_dir = tmp_path / "ops"

    module = importlib.import_module("swarmz_runtime.api.operational_routes")

    from swarmz_runtime.core.operational_runtime import OperationalRuntime

    runtime = OperationalRuntime(Path(tmp_path))
    runtime._ops_dir = ops_dir
    runtime._ops_dir.mkdir(parents=True, exist_ok=True)
    runtime._blueprints_file = ops_dir / "blueprints.jsonl"
    runtime._offers_file = ops_dir / "offers.jsonl"
    runtime._orders_file = ops_dir / "orders.jsonl"
    runtime._ledger_file = ops_dir / "ledger.jsonl"

    monkeypatch.setattr(module, "_runtime", runtime)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "test_secret")

    bp = client.post(
        "/v1/blueprints",
        json={
            "name": "Digital Operator Pack",
            "spec": {"artifact": "bundle.zip"},
            "owner": "operator",
        },
    )
    assert bp.status_code == 200
    blueprint_id = bp.json()["blueprint"]["blueprint_id"]

    val = client.post(f"/v1/blueprints/{blueprint_id}/validate")
    assert val.status_code == 200
    assert val.json()["validation"]["validation_status"] == "approved"

    offer = client.post(
        "/v1/offers",
        json={
            "blueprint_id": blueprint_id,
            "title": "Operator Pack",
            "price_cents": 1000,
            "cost_cents": 400,
            "spend": 10,
            "approved": False,
            "refund_rate": 1,
        },
    )
    assert offer.status_code == 200
    sku = offer.json()["offer"]["sku"]

    catalog = client.get("/v1/store/catalog")
    assert catalog.status_code == 200
    assert catalog.json()["count"] >= 1

    checkout = client.post(
        "/v1/store/checkout",
        json={"sku": sku, "quantity": 2, "payment_provider": "manual"},
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["order"]["order_id"]

    webhook_payload = json.dumps(
        {"order_id": order_id, "event": "payment_succeeded"}
    ).encode("utf-8")
    webhook_sig = "sha256=" + hmac.new(
        b"test_secret", webhook_payload, hashlib.sha256
    ).hexdigest()
    paid = client.post(
        "/v1/store/payment-webhook",
        content=webhook_payload,
        headers={
            "X-Webhook-Signature": webhook_sig,
            "Content-Type": "application/json",
        },
    )
    assert paid.status_code == 200
    assert paid.json()["ok"] is True

    fulfilled = client.post(
        f"/v1/store/orders/{order_id}/fulfill", json={"mode": "digital"}
    )
    assert fulfilled.status_code == 200
    assert fulfilled.json()["ok"] is True

    ledger = client.get("/v1/ledger")
    assert ledger.status_code == 200
    assert ledger.json()["count"] >= 2


def test_offer_policy_blocked_when_margin_low(client, tmp_path, monkeypatch):
    ops_dir = tmp_path / "ops"

    module = importlib.import_module("swarmz_runtime.api.operational_routes")

    from swarmz_runtime.core.operational_runtime import OperationalRuntime

    runtime = OperationalRuntime(Path(tmp_path))
    runtime._ops_dir = ops_dir
    runtime._ops_dir.mkdir(parents=True, exist_ok=True)
    runtime._blueprints_file = ops_dir / "blueprints.jsonl"
    runtime._offers_file = ops_dir / "offers.jsonl"
    runtime._orders_file = ops_dir / "orders.jsonl"
    runtime._ledger_file = ops_dir / "ledger.jsonl"

    monkeypatch.setattr(module, "_runtime", runtime)

    bp = client.post(
        "/v1/blueprints",
        json={"name": "Low Margin", "spec": {"artifact": "x"}, "owner": "operator"},
    )
    blueprint_id = bp.json()["blueprint"]["blueprint_id"]

    blocked = client.post(
        "/v1/offers",
        json={
            "blueprint_id": blueprint_id,
            "title": "Bad Margin",
            "price_cents": 100,
            "cost_cents": 90,
            "spend": 0,
            "approved": False,
            "refund_rate": 0,
        },
    )

    assert blocked.status_code == 400


def test_autonomy_cycle_uses_langgraph_runtime(client):
    response = client.post("/v1/autonomy/cycle", json={"cycle_label": "hourly"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["cycle_label"] == "hourly"
    assert payload["run"]["status"] == "completed"
    assert "planner" in payload["run"]["agents"]
