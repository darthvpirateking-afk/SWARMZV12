# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""Tests for SWARMZ Runtime infra API layer.

These tests exercise the new /v1/infra endpoints on the runtime FastAPI
app, with the infra orchestrator feature flag enabled via environment
variables.
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure repository root is on the path
sys.path.insert(0, str(Path(__file__).parent))

# Enable infra orchestrator before importing the runtime server so that
# the config singleton sees the environment flag on first use.
os.environ["SWARMZ_INFRA_ORCHESTRATOR_ENABLED"] = "1"

try:
    from fastapi.testclient import TestClient
    from swarmz_runtime.api.server import app as runtime_app
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False


@unittest.skipIf(not FASTAPI_AVAILABLE, "FastAPI or runtime server not available")
class TestRuntimeInfraAPI(unittest.TestCase):
    """Tests for /v1/infra runtime endpoints."""

    def setUp(self):
        self.client = TestClient(runtime_app)

    def test_ingest_metrics_and_overview(self):
        """Posting a metrics sample makes it visible in overview/events."""

        payload = {
            "node_id": "node-1",
            "cpu": 0.5,
            "memory": 0.75,
            "gpu": 0.25,
            "disk": 0.9,
            "net_rx": 10.0,
            "net_tx": 5.0,
            "extra": {"role": "worker"},
        }
        resp = self.client.post("/v1/infra/metrics", json=payload)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("ok"))

        # Overview should include at least one node with averages.
        overview = self.client.get("/v1/infra/overview").json()
        self.assertGreaterEqual(overview.get("total_nodes", 0), 1)
        nodes = overview.get("nodes", [])
        self.assertTrue(any(n.get("node_id") == "node-1" for n in nodes))

        # Raw events should show at least one metrics event.
        events_resp = self.client.get("/v1/infra/events?limit=10")
        self.assertEqual(events_resp.status_code, 200)
        events = events_resp.json().get("events", [])
        self.assertGreater(len(events), 0)
        self.assertTrue(any(e.get("type") == "metrics" for e in events))


def test_runtime_infra():
    pass


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

