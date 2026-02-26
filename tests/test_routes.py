"""
NEXUSMON route integration tests.
Tests every critical endpoint required by the ultimate integration pass.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from swarmz_server import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_v1_health():
    r = client.get("/v1/health")
    assert r.status_code == 200


def test_ui_state():
    r = client.get("/v1/ui/state")
    assert r.status_code == 200
    data = r.json()
    assert "phase" in data
    assert "organism_stage" in data


def test_organism_status():
    r = client.get("/v1/nexusmon/organism/status")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") == True
    assert "evolution" in data
    assert "operator" in data
    assert "workers" in data


def test_organism_evolution():
    r = client.get("/v1/nexusmon/organism/evolution")
    assert r.status_code == 200
    data = r.json()
    assert "stage" in data
    assert data["stage"] in ["DORMANT", "AWAKENING", "FORGING", "SOVEREIGN", "APEX"]


def test_evolution_sync():
    r = client.post(
        "/v1/nexusmon/organism/evolution/sync",
        json={"total_missions": 0, "success_count": 0, "belief_count": 0},
    )
    assert r.status_code == 200
    assert r.json().get("ok") == True


def test_operator():
    r = client.get("/v1/nexusmon/organism/operator")
    assert r.status_code == 200


def test_operator_fusion():
    r = client.get("/v1/nexusmon/organism/operator/fusion")
    assert r.status_code == 200
    assert "fusion_block" in r.json()


def test_worker_list():
    r = client.get("/v1/nexusmon/organism/worker")
    assert r.status_code == 200
    assert "workers" in r.json()


def test_worker_spawn():
    r = client.post(
        "/v1/nexusmon/organism/worker/spawn",
        json={"goal": "test goal", "autonomous": False},
    )
    assert r.status_code in [200, 202]
    data = r.json()
    assert data.get("ok") == True
    assert "worker_id" in data


def test_companion():
    # Patch the name as bound in companion.py (from core.model_router import call as model_call)
    mock_response = {"ok": True, "text": "NEXUSMON online. Awaiting orders.", "provider": "mock", "model": "mock", "latencyMs": 0}
    with patch("core.companion.model_call", return_value=mock_response):
        r = client.post(
            "/v1/nexusmon/organism/companion",
            json={"text": "status check"},
        )
    assert r.status_code == 200


def test_beliefs_list():
    r = client.get("/v1/claimlab/beliefs")
    assert r.status_code == 200
    assert "beliefs" in r.json()


def test_beliefs_create():
    r = client.post(
        "/v1/claimlab/beliefs",
        json={"claim": "Test claim", "confidence": 0.7},
    )
    assert r.status_code == 201
    assert "belief_id" in r.json()


def test_claimlab_analyze():
    r = client.post(
        "/v1/claimlab/analyze",
        json={"claim": "Remote work increases productivity"},
    )
    assert r.status_code == 200
    assert "analysis" in r.json()


def test_cognition_status():
    r = client.get("/v1/cognition/status")
    assert r.status_code == 200
    assert r.json().get("ok") == True


def test_predictions_list():
    r = client.get("/v1/cognition/predictions")
    assert r.status_code == 200


def test_prediction_create():
    r = client.post(
        "/v1/cognition/predictions",
        json={"claim": "It will rain tomorrow", "probability": 0.7},
    )
    assert r.status_code == 201
    data = r.json()
    assert "prediction_id" in data


def test_errors_list():
    r = client.get("/v1/cognition/errors")
    assert r.status_code == 200


def test_error_taxonomy():
    r = client.get("/v1/cognition/errors/taxonomy")
    assert r.status_code == 200
    assert "taxonomy" in r.json()


def test_attention_list():
    r = client.get("/v1/cognition/attention")
    assert r.status_code == 200


def test_sources_list():
    r = client.get("/v1/cognition/sources")
    assert r.status_code == 200


def test_cockpit_route():
    r = client.get("/organism")
    assert r.status_code == 200
