# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""Tests for the interactive web UI router (addons/api/ui_router.py)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from addons.api.ui_router import router

# Build a minimal FastAPI app that only contains the UI router.
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestUIPage(unittest.TestCase):
    """Test that the /ui page is served correctly."""

    def test_ui_returns_html(self):
        resp = client.get("/ui")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers["content-type"])
        self.assertIn("SWARMZ", resp.text)
        self.assertIn("Operator Console", resp.text)

    def test_ui_contains_key_sections(self):
        resp = client.get("/ui")
        body = resp.text
        self.assertIn("Available Capabilities", body)
        self.assertIn("Execute Task", body)
        self.assertIn("Audit Log", body)


class TestUIApiCapabilities(unittest.TestCase):
    """Test GET /ui/api/capabilities."""

    def test_returns_capabilities(self):
        resp = client.get("/ui/api/capabilities")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("capabilities", data)
        self.assertIn("echo", data["capabilities"])
        self.assertIn("system_info", data["capabilities"])

    def test_capabilities_have_metadata(self):
        resp = client.get("/ui/api/capabilities")
        caps = resp.json()["capabilities"]
        echo_meta = caps["echo"]
        self.assertIn("description", echo_meta)


class TestUIApiExecute(unittest.TestCase):
    """Test POST /ui/api/execute."""

    def test_execute_echo(self):
        resp = client.post(
            "/ui/api/execute",
            json={"task": "echo", "params": {"message": "hello"}},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"], "Echo: hello")

    def test_execute_system_info(self):
        resp = client.post("/ui/api/execute", json={"task": "system_info"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertIn("platform", data["result"])

    def test_execute_unknown_task(self):
        resp = client.post("/ui/api/execute", json={"task": "nonexistent"})
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertIn("error", data)


class TestUIApiAudit(unittest.TestCase):
    """Test GET /ui/api/audit."""

    def test_returns_audit_list(self):
        # Execute something first to ensure at least one entry
        client.post(
            "/ui/api/execute",
            json={"task": "echo", "params": {"message": "audit test"}},
        )
        resp = client.get("/ui/api/audit")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("audit", data)
        self.assertIsInstance(data["audit"], list)
        self.assertGreater(len(data["audit"]), 0)


class TestUIApiInfo(unittest.TestCase):
    """Test GET /ui/api/info."""

    def test_returns_system_info(self):
        resp = client.get("/ui/api/info")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("info", data)
        self.assertIn("platform", data["info"])


def test_ui():
    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)

