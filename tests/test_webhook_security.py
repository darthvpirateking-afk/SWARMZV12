import hashlib
import hmac
import importlib
import json
from pathlib import Path

from swarmz_runtime.core.operational_runtime import OperationalRuntime

SECRET = "test_secret_for_tests_only"


def make_sig(body: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _wire_runtime(tmp_path, monkeypatch):
    routes_module = importlib.import_module("swarmz_runtime.api.operational_routes")
    runtime_module = importlib.import_module("swarmz_runtime.core.operational_runtime")
    runtime = OperationalRuntime(Path(tmp_path))
    ops_dir = tmp_path / "ops"
    ops_dir.mkdir(parents=True, exist_ok=True)
    runtime._ops_dir = ops_dir
    runtime._blueprints_file = ops_dir / "blueprints.jsonl"
    runtime._offers_file = ops_dir / "offers.jsonl"
    runtime._orders_file = ops_dir / "orders.jsonl"
    runtime._ledger_file = ops_dir / "ledger.jsonl"
    monkeypatch.setattr(routes_module, "_runtime", runtime)

    processed_events = tmp_path / "data" / "payments" / "processed_events.jsonl"
    monkeypatch.setattr(runtime_module, "PROCESSED_EVENTS_PATH", processed_events)

    captured_events: list[tuple[str, dict[str, object]]] = []

    def _capture(event_type: str, details: dict[str, object]) -> None:
        captured_events.append((event_type, details))

    monkeypatch.setattr("addons.security.append_security_event", _capture)
    return runtime, processed_events, captured_events


def _create_order(client) -> str:
    bp = client.post(
        "/v1/blueprints",
        json={"name": "Webhook Test Pack", "spec": {"artifact": "bundle.zip"}},
    )
    blueprint_id = bp.json()["blueprint"]["blueprint_id"]

    offer = client.post(
        "/v1/offers",
        json={
            "blueprint_id": blueprint_id,
            "title": "Webhook SKU",
            "price_cents": 1000,
            "cost_cents": 400,
            "spend": 10,
            "approved": False,
            "refund_rate": 1,
        },
    )
    sku = offer.json()["offer"]["sku"]

    checkout = client.post(
        "/v1/store/checkout",
        json={"sku": sku, "quantity": 1, "payment_provider": "manual"},
    )
    return checkout.json()["order"]["order_id"]


def test_invalid_signature_400(client, tmp_path, monkeypatch):
    _, _, captured_events = _wire_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", SECRET)
    order_id = _create_order(client)
    payload = json.dumps(
        {"id": "evt_invalid_sig", "order_id": order_id, "event": "payment_succeeded"}
    ).encode("utf-8")

    response = client.post(
        "/v1/store/payment-webhook",
        content=payload,
        headers={"X-Webhook-Signature": "sha256=bad_sig"},
    )

    assert response.status_code == 400
    assert any(event == "forged_webhook" for event, _ in captured_events)


def test_missing_signature_400(client, tmp_path, monkeypatch):
    _, _, captured_events = _wire_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", SECRET)
    order_id = _create_order(client)
    payload = json.dumps(
        {"id": "evt_missing_sig", "order_id": order_id, "event": "payment_succeeded"}
    ).encode("utf-8")

    response = client.post("/v1/store/payment-webhook", content=payload)

    assert response.status_code == 400
    assert any(event == "forged_webhook" for event, _ in captured_events)


def test_missing_secret_503(client, tmp_path, monkeypatch):
    _wire_runtime(tmp_path, monkeypatch)
    monkeypatch.delenv("PAYMENT_WEBHOOK_SECRET", raising=False)
    payload = json.dumps(
        {"id": "evt_missing_secret", "order_id": "ord-any", "event": "payment_succeeded"}
    ).encode("utf-8")

    response = client.post(
        "/v1/store/payment-webhook",
        content=payload,
        headers={"X-Webhook-Signature": "sha256=unused"},
    )

    assert response.status_code == 503


def test_valid_first_delivery_200(client, tmp_path, monkeypatch):
    runtime, processed_events, _ = _wire_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", SECRET)
    order_id = _create_order(client)
    payload = json.dumps(
        {"id": "evt_first", "order_id": order_id, "event": "payment_succeeded"}
    ).encode("utf-8")
    signature = make_sig(payload)

    response = client.post(
        "/v1/store/payment-webhook",
        content=payload,
        headers={"X-Webhook-Signature": signature},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert runtime.ledger_tail(10)
    assert processed_events.exists()
    assert len(processed_events.read_text(encoding="utf-8").strip().splitlines()) == 1


def test_duplicate_delivery_200(client, tmp_path, monkeypatch):
    runtime, processed_events, captured_events = _wire_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", SECRET)
    order_id = _create_order(client)
    payload = json.dumps(
        {"id": "evt_duplicate", "order_id": order_id, "event": "payment_succeeded"}
    ).encode("utf-8")
    signature = make_sig(payload)

    first = client.post(
        "/v1/store/payment-webhook",
        content=payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert first.status_code == 200
    first_ledger_count = len(runtime.ledger_tail(20))
    first_processed_count = len(
        processed_events.read_text(encoding="utf-8").strip().splitlines()
    )

    second = client.post(
        "/v1/store/payment-webhook",
        content=payload,
        headers={"X-Webhook-Signature": signature},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "already_processed"
    assert len(runtime.ledger_tail(20)) == first_ledger_count
    assert (
        len(processed_events.read_text(encoding="utf-8").strip().splitlines())
        == first_processed_count
    )
    assert any(event == "webhook_replay" for event, _ in captured_events)
