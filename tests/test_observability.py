# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_observability.py â€” Tests for observability endpoints (Commit 12).

Validates /v1/runtime/scoreboard, /v1/companion/state, /v1/companion/history, /v1/prepared/pending.
Uses FastAPI TestClient.
"""


from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_runtime_scoreboard():
    resp = client.get("/v1/runtime/scoreboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "personality" in data
    assert "timestamp" in data


def test_companion_state():
    resp = client.get("/v1/companion/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "master_identity" in data
    assert "self_assessment" in data
    assert "MASTER_SWARMZ" in data.get("self_assessment", "")


def test_companion_history():
    resp = client.get("/v1/companion/history?tail=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "records" in data
    assert isinstance(data["records"], list)
    assert "read_only" in data


def test_prepared_pending():
    resp = client.get("/v1/prepared/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "items" in data
    assert "counts" in data


def test_prepared_pending_filtered():
    resp = client.get("/v1/prepared/pending?category=commands")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_ai_status_includes_phase():
    resp = client.get("/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "phase" in data
    assert "quarantine" in data


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

