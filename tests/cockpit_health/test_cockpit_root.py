from __future__ import annotations

from fastapi.testclient import TestClient

from swarmz_server import app


def test_cockpit_root_returns_200() -> None:
    with TestClient(app) as client:
        resp = client.get("/cockpit/")
    assert resp.status_code == 200


def test_cockpit_root_contains_root_element() -> None:
    with TestClient(app) as client:
        resp = client.get("/cockpit/")
    assert 'id="app"' in resp.text


def test_cockpit_root_references_canonical_bridge_script() -> None:
    with TestClient(app) as client:
        resp = client.get("/cockpit/")
    assert "canonical_bridge.js" in resp.text
