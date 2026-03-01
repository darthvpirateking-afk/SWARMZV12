from __future__ import annotations

from fastapi.testclient import TestClient

from swarmz_server import app


def test_canonical_agents_200() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/canonical/agents")
    assert resp.status_code == 200


def test_canonical_traces_recent_200() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/canonical/traces/recent")
    assert resp.status_code == 200


def test_canonical_missions_templates_200() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/canonical/missions/templates")
    assert resp.status_code == 200


def test_canonical_health_200() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/canonical/health")
    assert resp.status_code == 200
