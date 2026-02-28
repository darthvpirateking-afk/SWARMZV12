from __future__ import annotations

from fastapi.testclient import TestClient

from swarmz_server import app

REQUIRED_FIELDS = {"total", "executed", "pending", "lastExecutionISO"}


def test_prepared_actions_status_contains_required_fields() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/prepared_actions/status")
    assert resp.status_code == 200
    payload = resp.json()
    assert REQUIRED_FIELDS.issubset(payload.keys())
