# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Test Suite for SWARMZ Web Server

Tests the FastAPI REST API and PWA functionality.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi.testclient import TestClient
    from swarmz_server import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@unittest.skipIf(not FASTAPI_AVAILABLE, "FastAPI not installed")
class TestWebServer(unittest.TestCase):
    """Test SWARMZ web server endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_home_page(self):
        """Test PWA home page is served."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("SWARMZ", response.text)
        self.assertIn("Operator-Sovereign", response.text)

    def test_manifest(self):
        """Test PWA manifest is served."""
        response = self.client.get("/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["short_name"], "SWARMZ")
        self.assertEqual(data["display"], "standalone")
        self.assertIn("icons", data)

    def test_service_worker(self):
        """Test service worker is served."""
        response = self.client.get("/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CACHE_NAME", response.text)
        self.assertIn("addEventListener", response.text)

    def test_icon_svg(self):
        """Test icon SVG is served."""
        response = self.client.get("/icon.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("svg", response.text.lower())

    def test_apple_touch_icon(self):
        """Test Apple touch icon is served."""
        response = self.client.get("/apple-touch-icon.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("svg", response.text.lower())

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "SWARMZ API")

    def test_list_tasks(self):
        """Test list tasks endpoint."""
        response = self.client.get("/v1/tasks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("tasks", data)
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)

    def test_execute_echo_task(self):
        """Test executing echo task."""
        response = self.client.post(
            "/v1/execute", json={"task": "echo", "params": {"message": "Test message"}}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["result"], "Echo: Test message")

    def test_execute_system_info(self):
        """Test system info endpoint."""
        response = self.client.get("/v1/system/info")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("info", data)
        self.assertIn("platform", data["info"])

    def test_audit_log(self):
        """Test audit log endpoint."""
        # First execute a task
        self.client.post(
            "/v1/execute", json={"task": "echo", "params": {"message": "test"}}
        )

        # Then get audit log
        response = self.client.get("/v1/audit")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("audit_log", data)
        self.assertGreater(len(data["audit_log"]), 0)

    def test_execute_invalid_task(self):
        """Test executing non-existent task."""
        response = self.client.post(
            "/v1/execute", json={"task": "nonexistent_task", "params": {}}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_openapi_docs(self):
        """Test OpenAPI documentation endpoint."""
        response = self.client.get("/docs/openapi.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("openapi", data)
        self.assertIn("info", data)
        self.assertEqual(data["info"]["title"], "SWARMZ API")


def test_swarmz_server():
    """Minimal scaffold for test_swarmz_server.py."""
    pass


def main():
    """Run the test suite."""
    print("=" * 60)
    print("SWARMZ Web Server Test Suite")
    print("=" * 60)
    print()

    if not FASTAPI_AVAILABLE:
        print("âš ï¸  FastAPI not installed - skipping web server tests")
        print("   Install with: pip install -r requirements.txt")
        print()
        return 0

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestWebServer)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
