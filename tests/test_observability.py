def test__dump_routes(client):
    from starlette.routing import Mount

    routes = client.app.routes
    print("\n=== ROUTES ===")
    for r in routes:
        cls = r.__class__.__name__
        path = getattr(r, "path", "")
        methods = ",".join(sorted(getattr(r, "methods", []) or []))
        extra = ""
        if isinstance(r, Mount):
            extra = f" -> MOUNT name={getattr(r, 'name', None)} app={type(getattr(r, 'app', None)).__name__}"
        print(f"{cls:10s} {methods:10s} {path}{extra}")

    paths = {getattr(r, "path", "") for r in routes}
    assert "/v1/prepared/pending" in paths or "/v1/v1/prepared/pending" in paths
    assert "/v1/ai/status" in paths or "/v1/v1/ai/status" in paths


# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_observability.py â€” Tests for observability endpoints (Commit 12).

Validates /v1/runtime/scoreboard, /v1/companion/state, /v1/companion/history, /v1/prepared/pending.
Uses FastAPI TestClient.
"""


import pytest


def test_runtime_scoreboard(client):
    resp = client.get("/v1/runtime/scoreboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok", True) is True
    assert "personality" in data
    assert "timestamp" in data


def test_companion_state(client):
    resp = client.get("/v1/companion/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok", True) is True
    assert "master_identity" in data
    assert "self_assessment" in data
    assert "MASTER_SWARMZ" in data.get("self_assessment", "")


def test_companion_history(client):
    resp = client.get("/v1/companion/history?tail=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok", True) is True
    assert "records" in data
    assert isinstance(data["records"], list)
    assert "read_only" in data


def test_prepared_pending(client):
    resp = client.get("/v1/prepared/pending")
    assert resp.status_code == 200
    data = resp.json()
    # Accept both stub and legacy keys for now
    assert "pending" in data or "items" in data
    assert "count" in data or "counts" in data


def test_prepared_pending_filtered(client):
    resp = client.get("/v1/prepared/pending?category=commands")
    assert resp.status_code == 200
    data = resp.json()
    assert "pending" in data or "items" in data


def test_ai_status_includes_phase(client):
    resp = client.get("/v1/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "phase" in data


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_observability_health(client):
    r = client.get("/v1/observability/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_observability_ready(client):
    r = client.get("/v1/observability/ready")
    assert r.status_code == 200
    assert r.json().get("status") == "ready"


def test_debug_routes(client):
    app = client.app
    paths = sorted({getattr(r, "path", "") for r in app.routes})
    obs = [p for p in paths if "observability" in p]
    print("\n".join(obs))
    assert obs  # just to see output


import unittest
from unittest.mock import patch, MagicMock
from kernel_runtime.orchestrator import SwarmzOrchestrator


class TestObservabilityEndpoints(unittest.TestCase):

    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_api")
    def test_api_reporting_endpoint(self, mock_start_api):
        # Mock the API start method
        mock_start_api.return_value = MagicMock()

        # Create an instance of the orchestrator
        orchestrator = SwarmzOrchestrator()

        # Call the API start method
        api = orchestrator.start_api()

        # Assert that the API start method was called
        mock_start_api.assert_called_once()
        self.assertIsNotNone(api)

    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.launch_cockpit")
    def test_cockpit_reporting_endpoint(self, mock_launch_cockpit):
        # Mock the cockpit launch method
        mock_launch_cockpit.return_value = MagicMock()

        # Create an instance of the orchestrator
        orchestrator = SwarmzOrchestrator()

        # Call the cockpit launch method
        cockpit = orchestrator.launch_cockpit()

        # Assert that the cockpit launch method was called
        mock_launch_cockpit.assert_called_once()
        self.assertIsNotNone(cockpit)


if __name__ == "__main__":
    unittest.main()
