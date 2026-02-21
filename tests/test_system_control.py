"""Tests for system control and mission lifecycle endpoints."""

import pytest
from fastapi.testclient import TestClient
from swarmz_runtime.api.server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_system_status(client):
    resp = client.get("/v1/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "timestamp" in data


def test_system_heartbeat(client):
    resp = client.get("/v1/system/heartbeat")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alive"] is True
    assert "status" in data


def test_system_start_stop_restart(client):
    resp = client.post("/v1/system/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"

    resp = client.post("/v1/system/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"

    resp = client.post("/v1/system/restart")
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_system_logs(client):
    # Trigger some log entries first
    client.get("/v1/system/heartbeat")
    resp = client.get("/v1/system/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_system_logs_filter(client):
    resp = client.get("/v1/system/logs?level=INFO&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert all(e["level"] == "INFO" for e in data["entries"])


def test_mission_lifecycle_start(client):
    resp = client.post(
        "/v1/missions/start",
        json={"goal": "Test mission", "category": "test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "mission_id" in data
    assert data["state"] == "QUEUED"
    return data["mission_id"]


def test_mission_lifecycle_status(client):
    # Start a mission
    resp = client.post(
        "/v1/missions/start",
        json={"goal": "Status test mission", "category": "test"},
    )
    mission_id = resp.json()["mission_id"]

    resp = client.get(f"/v1/missions/status/{mission_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "QUEUED"
    assert data["mission_id"] == mission_id


def test_missions_list_status(client):
    resp = client.get("/v1/missions/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "missions" in data
    assert isinstance(data["missions"], list)


def test_mission_stop(client):
    resp = client.post(
        "/v1/missions/start",
        json={"goal": "Stop test", "category": "test"},
    )
    mission_id = resp.json()["mission_id"]

    resp = client.post("/v1/missions/stop", json={"mission_id": mission_id})
    assert resp.status_code == 200
    assert resp.json()["state"] == "ABORTED"


def test_mission_invalid_transition(client):
    resp = client.post(
        "/v1/missions/start",
        json={"goal": "Invalid transition test", "category": "test"},
    )
    mission_id = resp.json()["mission_id"]

    # Can't pause a QUEUED mission
    resp = client.post("/v1/missions/pause", json={"mission_id": mission_id})
    assert resp.status_code == 400
