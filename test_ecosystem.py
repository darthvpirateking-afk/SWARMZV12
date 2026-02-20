# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Tests for the SWARMZ ecosystem autonomous loop and API endpoints.
"""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.core.autoloop import AutoLoopManager


class TestAutoLoopManager(unittest.TestCase):
    """Test the autonomous loop manager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = SwarmzEngine(data_dir=self.tmpdir)
        self.loop = AutoLoopManager(self.engine, data_dir=self.tmpdir)

    def tearDown(self):
        self.loop.stop()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_single_step_returns_mission_id(self):
        """Single step creates a mission and returns its id."""
        result = self.loop.single_step("make money", {}, {})
        self.assertIn("mission_id", result)
        self.assertIn("tick_count", result)
        self.assertEqual(result["tick_count"], 1)

    def test_single_step_writes_audit(self):
        """Single step appends entries to audit.jsonl."""
        audit_file = Path(self.tmpdir) / "audit.jsonl"
        before = audit_file.stat().st_size if audit_file.exists() else 0
        self.loop.single_step("make money")
        after = audit_file.stat().st_size
        self.assertGreater(after, before)

    def test_single_step_persists_state(self):
        """Single step writes state.json."""
        self.loop.single_step("make money")
        state_file = Path(self.tmpdir) / "state.json"
        self.assertTrue(state_file.exists())
        state = json.loads(state_file.read_text())
        self.assertEqual(state["tick_count"], 1)

    def test_get_state(self):
        """get_state returns expected keys."""
        state = self.loop.get_state()
        for key in ("running", "tick_count", "last_tick_ts", "tick_interval", "max_ticks_per_minute"):
            self.assertIn(key, state)

    def test_start_stop(self):
        """Auto loop starts and stops cleanly."""
        self.loop.start(tick_interval=5)
        state = self.loop.get_state()
        self.assertTrue(state["running"])

        self.loop.stop()
        state = self.loop.get_state()
        self.assertFalse(state["running"])

    def test_auto_loop_ticks(self):
        """Auto loop increments tick_count over time."""
        self.loop.start(tick_interval=5)
        time.sleep(7)
        self.loop.stop()
        self.assertGreaterEqual(self.loop._tick_count, 1)

    def test_kill_switch(self):
        """Creating a KILL file stops the loop."""
        kill_file = Path(self.tmpdir) / "KILL"
        self.loop.start(tick_interval=5)
        time.sleep(1)
        kill_file.touch()
        time.sleep(7)
        self.assertFalse(self.loop._running)
        kill_file.unlink(missing_ok=True)

    def test_crash_safe_resume(self):
        """State persists across AutoLoopManager instances."""
        self.loop.single_step("make money")
        self.assertEqual(self.loop._tick_count, 1)

        # Create new manager â€“ should load persisted tick_count
        loop2 = AutoLoopManager(self.engine, data_dir=self.tmpdir)
        self.assertEqual(loop2._tick_count, 1)

    def test_goal_to_category_deterministic(self):
        """Same goal always maps to same category."""
        cat1 = AutoLoopManager._goal_to_category("make money")
        cat2 = AutoLoopManager._goal_to_category("make money")
        self.assertEqual(cat1, cat2)
        self.assertEqual(cat1, "coin")

    def test_goal_to_category_variants(self):
        """Different goal keywords map to expected categories."""
        self.assertEqual(AutoLoopManager._goal_to_category("earn profit"), "coin")
        self.assertEqual(AutoLoopManager._goal_to_category("build something"), "forge")
        self.assertEqual(AutoLoopManager._goal_to_category("learn python"), "library")
        self.assertEqual(AutoLoopManager._goal_to_category("relax"), "sanctuary")

    def test_rate_limit(self):
        """Rate limiter caps ticks per minute."""
        # Fill up the rate limit
        self.loop._recent_tick_times = [time.monotonic()] * self.loop.MAX_TICKS_PER_MINUTE
        self.assertFalse(self.loop._rate_limit_ok())


class TestEcosystemEndpoints(unittest.TestCase):
    """Test ecosystem API endpoints via TestClient."""

    @classmethod
    def setUpClass(cls):
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            raise unittest.SkipTest("fastapi.testclient not available")

        cls.tmpdir = tempfile.mkdtemp()
        # Patch engine to use temp data dir
        from swarmz_runtime.api import server
        original_get_engine = server.get_engine

        def _temp_engine():
            engine = original_get_engine()
            return engine

        from swarmz_runtime.api.server import app
        cls.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/v1/health")
        self.assertEqual(r.status_code, 200)
        self.assertIn("status", r.json())

    def test_openapi(self):
        r = self.client.get("/openapi.json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("paths", r.json())

    def test_ecosystem_run(self):
        r = self.client.post(
            "/v1/ecosystem/run",
            json={"operator_goal": "make money", "constraints": {}, "results": {}},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("mission_id", data)

    def test_ecosystem_status(self):
        r = self.client.get("/v1/ecosystem/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("tick_count", data)
        self.assertIn("running", data)

    def test_ecosystem_verify(self):
        r = self.client.get("/v1/ecosystem/verify")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["healthy"])

    def test_ecosystem_auto_start_stop(self):
        r = self.client.post(
            "/v1/ecosystem/auto/start",
            json={"tick_interval": 60},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "started")

        r = self.client.post("/v1/ecosystem/auto/stop")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "stopped")

    def test_ecosystem_packs_not_found(self):
        r = self.client.get("/v1/ecosystem/packs/nonexistent")
        self.assertEqual(r.status_code, 404)

    def test_ecosystem_packs_found(self):
        # Create a mission first
        r = self.client.post(
            "/v1/ecosystem/run",
            json={"operator_goal": "make money", "constraints": {}, "results": {}},
        )
        mid = r.json()["mission_id"]
        r = self.client.get(f"/v1/ecosystem/packs/{mid}")
        self.assertEqual(r.status_code, 200)
        self.assertIn("mission", r.json())
        self.assertIn("audit", r.json())


def test_ecosystem():
    pass


def run_tests():
    print("=" * 60)
    print("SWARMZ Ecosystem Test Suite")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAutoLoopManager))
    suite.addTests(loader.loadTestsFromTestCase(TestEcosystemEndpoints))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    if result.testsRun > 0:
        print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())

