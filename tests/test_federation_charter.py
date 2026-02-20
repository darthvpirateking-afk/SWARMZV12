import importlib
from pathlib import Path


def _set_isolated_federation(monkeypatch, tmp_path):
    federation_module = importlib.import_module("swarmz_runtime.api.federation_routes")
    from swarmz_runtime.core.federation_manager import FederationManager
    from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem

    manager = FederationManager(Path(tmp_path))
    ecosystem = OperatorEcosystem(Path(tmp_path))

    monkeypatch.setattr(federation_module, "_manager", manager)
    monkeypatch.setattr(federation_module, "_ecosystem", ecosystem)


def test_federation_organism_lifecycle(client, monkeypatch, tmp_path):
    _set_isolated_federation(monkeypatch, tmp_path)

    created = client.post(
        "/v1/federation/organisms",
        json={"name": "Prime-1", "owner_id": "regan", "config_json": {"mode": "prime"}},
    )
    assert created.status_code == 200
    organism_id = created.json()["organism"]["id"]

    fetched = client.get(f"/v1/federation/organisms/{organism_id}")
    assert fetched.status_code == 200
    assert fetched.json()["organism"]["status"] == "active"

    evolved = client.post(
        f"/v1/federation/organisms/{organism_id}/evolve",
        json={"mission_success": True, "incidents": 0, "policy_compliance": True},
    )
    assert evolved.status_code == 200
    assert evolved.json()["organism"]["partner"]["tier"] >= 1

    paused = client.post(f"/v1/federation/organisms/{organism_id}/pause", json={"reason": "risk_spike"})
    assert paused.status_code == 200
    assert paused.json()["organism"]["status"] == "paused"

    retired = client.post(f"/v1/federation/organisms/{organism_id}/retire", json={"reason": "operator_request"})
    assert retired.status_code == 200
    assert retired.json()["organism"]["status"] == "retired"

    metrics = client.get("/v1/federation/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["metrics"]["organism_count"] >= 1


def test_federation_nightly_insights(client, monkeypatch, tmp_path):
    _set_isolated_federation(monkeypatch, tmp_path)

    # Seed ecosystem outcomes to drive cross-organism safe insights
    client.post(
        "/v1/vault/outcomes",
        json={
            "subject_type": "offer",
            "subject_id": "of-good",
            "conversion": 0.2,
            "margin": 40.0,
            "refund_rate": 1.0,
            "sla_adherence": 0.95,
            "channel": "store",
            "supplier": "pod",
        },
    )
    client.post(
        "/v1/vault/outcomes",
        json={
            "subject_type": "offer",
            "subject_id": "of-bad",
            "conversion": 0.02,
            "margin": 5.0,
            "refund_rate": 25.0,
            "sla_adherence": 0.35,
            "channel": "store",
            "supplier": "pod",
        },
    )

    nightly = client.post("/v1/federation/insights/nightly")
    assert nightly.status_code == 200
    payload = nightly.json()["insight"]
    assert payload["privacy_mode"] == "no_customer_data"

    latest = client.get("/v1/federation/insights/latest")
    assert latest.status_code == 200
    assert latest.json()["insight"] is not None


def test_charter_prime_directive_paths(client):
    charter = client.get("/v1/charter")
    assert charter.status_code == 200
    assert "prime_directive" in charter.json()["charter"]

    unclear = client.post(
        "/v1/charter/evaluate",
        json={
            "intent": "",
            "explicit": False,
            "action": "publish",
            "requested_autonomy": 50,
            "max_autonomy": 60,
        },
    )
    assert unclear.status_code == 200
    assert unclear.json()["decision"]["allowed"] is False
    assert unclear.json()["decision"]["mode"] == "minimal_action"

    bounded = client.post(
        "/v1/charter/evaluate",
        json={
            "intent": "publish approved offer",
            "explicit": True,
            "action": "publish",
            "requested_autonomy": 90,
            "max_autonomy": 60,
        },
    )
    assert bounded.status_code == 200
    assert bounded.json()["decision"]["allowed"] is False
    assert bounded.json()["decision"]["mode"] == "bounded_execution"

    aligned = client.post(
        "/v1/charter/evaluate",
        json={
            "intent": "fulfill paid order",
            "explicit": True,
            "action": "fulfill",
            "requested_autonomy": 40,
            "max_autonomy": 60,
        },
    )
    assert aligned.status_code == 200
    assert aligned.json()["decision"]["allowed"] is True
    assert aligned.json()["decision"]["mode"] == "aligned_execution"


def test_charter_doctrine_document_and_change_flow_eval(client):
    doc = client.get("/v1/charter/doctrine")
    assert doc.status_code == 200
    payload = doc.json()["doctrine"]
    assert payload["system_primitives"]["truth"] == "immutable_event_log"
    assert payload["future_change_vector"]["stability"] == "increases"
    assert "immutable_history" in payload["future_invariants"]

    blocked = client.post(
        "/v1/charter/evaluate/change-flow",
        json={
            "execution_model": "parallel",
            "write_mode": "mutable",
            "history_mutable": True,
            "uses_polling_loops": True,
            "uses_file_sync": True,
            "event_driven": False,
            "in_memory_passing": False,
            "replayable_steps": False,
            "external_verification": False,
        },
    )
    assert blocked.status_code == 200
    assert blocked.json()["decision"]["allowed"] is False
    assert "write_mode_must_be_append_only" in blocked.json()["decision"]["violations"]

    aligned = client.post(
        "/v1/charter/evaluate/change-flow",
        json={
            "execution_model": "event_driven",
            "write_mode": "append_only",
            "history_mutable": False,
            "uses_polling_loops": False,
            "uses_file_sync": False,
            "event_driven": True,
            "in_memory_passing": True,
            "replayable_steps": True,
            "external_verification": True,
        },
    )
    assert aligned.status_code == 200
    assert aligned.json()["decision"]["allowed"] is True


def test_charter_future_contract_endpoint(client):
    resp = client.get("/v1/charter/future-contract")
    assert resp.status_code == 200
    body = resp.json()["future_contract"]
    assert body["changes"]["parallelism"] == "expands"
    assert "determinism" in body["does_not_change"]


def test_charter_operating_matrix_eval(client):
    fail = client.post(
        "/v1/charter/evaluate/operating-matrix",
        json={
            "has_artifact": False,
            "has_verification": False,
            "has_outcome": False,
            "external_verification": False,
            "replayable_step": False,
            "irreversible_action": True,
            "operator_approved": False,
        },
    )
    assert fail.status_code == 200
    assert fail.json()["decision"]["allowed"] is False
    assert "irreversible_action_requires_operator" in fail.json()["decision"]["violations"]

    ok = client.post(
        "/v1/charter/evaluate/operating-matrix",
        json={
            "has_artifact": True,
            "has_verification": True,
            "has_outcome": True,
            "external_verification": True,
            "replayable_step": True,
            "irreversible_action": True,
            "operator_approved": True,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["decision"]["allowed"] is True
