def test_contract_validator_rejects_irreversible_without_approval(client):
    resp = client.post(
        "/v1/system-primitives/contracts/validate",
        json={
            "action": {
                "action_type": "publish",
                "payload": {"id": "x"},
                "safety": {"irreversible": True, "operator_approved": False},
                "resources": {"cpu": 1, "memory_mb": 256, "timeout_s": 30},
                "meta": {"source": "test"},
            },
            "regime": "test",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["validation"]["allowed"] is False
    assert "irreversible_requires_operator_approval" in body["validation"]["violations"]
    assert body["companion_notified"] is True
    assert body["ledger"]["suppression_reason"] is not None


def test_contract_validator_accepts_valid_action(client):
    resp = client.post(
        "/v1/system-primitives/contracts/validate",
        json={
            "action": {
                "action_type": "dispatch",
                "payload": {"goal": "status"},
                "safety": {"irreversible": False, "operator_approved": True},
                "resources": {"cpu": 1, "memory_mb": 256, "timeout_s": 30},
                "meta": {"source": "test", "weaver_validated": True},
            },
            "regime": "test",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["validation"]["allowed"] is True
    assert body["companion_notified"] is False
    assert body["ledger"]["chosen_action"] == "dispatch"


def test_dispatch_rejected_without_operator_key(client):
    resp = client.post(
        "/v1/dispatch",
        json={"goal": "health", "category": "general", "constraints": {}},
    )
    assert resp.status_code == 401


def test_contract_validator_rejects_companion_bypass_without_weaver(client):
    resp = client.post(
        "/v1/system-primitives/contracts/validate",
        json={
            "action": {
                "action_type": "dispatch",
                "payload": {"goal": "status"},
                "safety": {"irreversible": False, "operator_approved": True},
                "resources": {"cpu": 1, "memory_mb": 256, "timeout_s": 30},
                "meta": {"source": "companion", "weaver_validated": False},
            },
            "regime": "test",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["validation"]["allowed"] is False
    assert "weaver_validation_required" in body["validation"]["violations"]
