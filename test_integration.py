#!/usr/bin/env python3
"""
Integration test for SWARMZ Companion with SWARMZ Core.
Tests that the companion can execute real tasks through the core system.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from companion import SwarmzCompanion, TaskContext, WorkerSwarm, CommitEngine, CommitState
from swarmz import SwarmzCore


class TestCompanionCoreIntegration(unittest.TestCase):
    """Test full integration between Companion and Core."""

    @classmethod
    def setUpClass(cls):
        cls.core = SwarmzCore()
        cls.core.load_plugin("plugins/filesystem.py")
        cls.core.load_plugin("plugins/dataprocessing.py")
        cls.companion = SwarmzCompanion(swarmz_core=cls.core)

    def test_core_initialization(self):
        """Core initializes with expected capabilities."""
        self.assertGreaterEqual(len(self.core.list_capabilities()), 3)

    def test_companion_mode_conversation(self):
        """Companion mode handles conversation input."""
        response = self.companion.interact("What is SWARMZ?")
        self.assertIn("[CONVERSATION]", response)

    def test_operator_mode_execution(self):
        """Operator mode executes tasks."""
        response = self.companion.interact("Run echo task", {"message": "Integration test"})
        self.assertTrue(
            any(tag in response for tag in ["[ACTION_READY]", "[NEEDS_CONFIRM]", "[BLOCKED]"])
        )

    def test_metrics_tracking(self):
        """Metrics are tracked after task execution."""
        # Ensure at least one action has run
        self.companion.interact("Run echo task", {"message": "test"})
        metrics = self.companion.get_metrics()
        self.assertIn("total_actions", metrics)
        self.assertIn("success_rate", metrics)
        self.assertGreaterEqual(metrics["total_actions"], 1)

    def test_memory_persistence(self):
        """Memory can be updated and retrieved."""
        self.companion.mode_manager.update_memory({
            "preferences": {"test_pref": "value"},
            "caps": {"test_cap": 100}
        })
        memory = self.companion.mode_manager.get_memory()
        self.assertEqual(memory.preferences.get("test_pref"), "value")
        self.assertEqual(memory.caps.get("test_cap"), 100)

    def test_worker_swarm(self):
        """Worker swarm executes Scout -> Builder -> Verify workflow."""
        swarm = WorkerSwarm()
        task_context = TaskContext(task_id="test", intent="integration test")
        results = swarm.execute_workflow(task_context)
        self.assertEqual(len(results), 3)
        self.assertEqual(
            [r.worker_type.value for r in results],
            ["scout", "builder", "verify"]
        )

    def test_commit_engine(self):
        """Commit engine evaluates task context."""
        task_context = TaskContext(task_id="test", intent="integration test")
        engine = CommitEngine()
        state = engine.evaluate(task_context)
        self.assertIn(state, [CommitState.ACTION_READY, CommitState.NEEDS_CONFIRM, CommitState.BLOCKED])

    def test_intelligence_layer(self):
        """Intelligence layer records execution logs."""
        # Run a task to generate logs
        self.companion.interact("Run echo task", {"message": "test"})
        intelligence = self.companion.mode_manager.operator_mode.intelligence
        self.assertIsInstance(intelligence.execution_logs, list)


if __name__ == "__main__":
    unittest.main()
