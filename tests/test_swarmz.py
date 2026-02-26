# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Test Suite for SWARMZ System

Tests core functionality, operator sovereignty, and plugin system.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from swarmz import SwarmzCore, OperatorSovereignty, TaskExecutor


class TestOperatorSovereignty(unittest.TestCase):
    """Test operator sovereignty functionality."""

    def setUp(self):
        self.sovereignty = OperatorSovereignty()

    def test_permission_request(self):
        """Test permission request system."""
        result = self.sovereignty.request_permission("test_action", {"test": "context"})
        self.assertTrue(result)

    def test_audit_log(self):
        """Test audit logging."""
        self.sovereignty.request_permission("action1", {"data": "test1"})
        self.sovereignty.request_permission("action2", {"data": "test2"})

        audit = self.sovereignty.get_audit_log()
        self.assertEqual(len(audit), 2)
        self.assertEqual(audit[0]["action"], "action1")
        self.assertEqual(audit[1]["action"], "action2")


class TestTaskExecutor(unittest.TestCase):
    """Test task execution engine."""

    def setUp(self):
        self.sovereignty = OperatorSovereignty()
        self.executor = TaskExecutor(self.sovereignty)

    def test_register_task(self):
        """Test task registration."""

        def test_func(x):
            return x * 2

        self.executor.register_task("double", test_func, {"desc": "Double a number"})
        self.assertIn("double", self.executor.registered_tasks)

    def test_execute_task(self):
        """Test task execution."""

        def add(a, b):
            return a + b

        self.executor.register_task("add", add)
        result = self.executor.execute_task("add", a=5, b=3)
        self.assertEqual(result, 8)

    def test_list_tasks(self):
        """Test listing tasks."""

        def task1():
            pass

        def task2():
            pass

        self.executor.register_task("task1", task1, {"desc": "Task 1"})
        self.executor.register_task("task2", task2, {"desc": "Task 2"})

        tasks = self.executor.list_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertIn("task1", tasks)
        self.assertIn("task2", tasks)


class TestSwarmzCore(unittest.TestCase):
    """Test core SWARMZ system."""

    def setUp(self):
        self.swarmz = SwarmzCore()

    def test_initialization(self):
        """Test system initialization."""
        self.assertIsNotNone(self.swarmz.sovereignty)
        self.assertIsNotNone(self.swarmz.executor)

    def test_builtin_tasks(self):
        """Test built-in tasks are registered."""
        capabilities = self.swarmz.list_capabilities()
        self.assertIn("echo", capabilities)
        self.assertIn("system_info", capabilities)
        self.assertIn("execute_python", capabilities)

    def test_echo_task(self):
        """Test echo task."""
        result = self.swarmz.execute("echo", message="test")
        self.assertEqual(result, "Echo: test")

    def test_system_info_task(self):
        """Test system info task."""
        result = self.swarmz.execute("system_info")
        self.assertIsInstance(result, dict)
        self.assertIn("platform", result)
        self.assertIn("python_version", result)
        self.assertIn("registered_tasks", result)

    def test_execute_python_task(self):
        """Test Python code execution (operator sovereignty)."""
        code = "result = 10 * 5"
        result = self.swarmz.execute("execute_python", code=code)
        self.assertEqual(result, 50)

    def test_audit_log(self):
        """Test audit log functionality."""
        self.swarmz.execute("echo", message="test1")
        self.swarmz.execute("echo", message="test2")

        audit = self.swarmz.get_audit_log()
        self.assertGreater(len(audit), 0)

    def test_load_plugin(self):
        """Test plugin loading."""
        # Create a temporary plugin
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def register(executor):
    def test_task():
        return "test_plugin_result"
    executor.register_task("test_plugin_task", test_task)
""")
            plugin_path = f.name

        try:
            # Load the plugin
            plugin_name = self.swarmz.load_plugin(plugin_path)
            self.assertIsNotNone(plugin_name)

            # Test the plugin task
            result = self.swarmz.execute("test_plugin_task")
            self.assertEqual(result, "test_plugin_result")
        finally:
            # Clean up
            Path(plugin_path).unlink()


class TestPlugins(unittest.TestCase):
    """Test plugin functionality."""

    def test_filesystem_plugin(self):
        """Test filesystem plugin."""
        swarmz = SwarmzCore()
        plugin_path = Path(__file__).parent / "plugins" / "filesystem.py"

        if plugin_path.exists():
            swarmz.load_plugin(str(plugin_path))

            # Test fs_list
            capabilities = swarmz.list_capabilities()
            self.assertIn("fs_list", capabilities)
            self.assertIn("fs_read", capabilities)
            self.assertIn("fs_write", capabilities)
            self.assertIn("fs_mkdir", capabilities)
            self.assertIn("fs_info", capabilities)

    def test_dataprocessing_plugin(self):
        """Test data processing plugin."""
        swarmz = SwarmzCore()
        plugin_path = Path(__file__).parent / "plugins" / "dataprocessing.py"

        if plugin_path.exists():
            swarmz.load_plugin(str(plugin_path))

            # Test data tasks
            capabilities = swarmz.list_capabilities()
            self.assertIn("data_json_parse", capabilities)
            self.assertIn("data_json_stringify", capabilities)
            self.assertIn("data_hash", capabilities)

            # Test JSON stringify
            obj = {"test": "data", "number": 42}
            result = swarmz.execute("data_json_stringify", obj=obj)
            self.assertIsInstance(result, str)
            self.assertIn("test", result)


class TestBrainMapping(unittest.TestCase):
    """Test brain mapping and routing."""

    def setUp(self):
        from swarmz_runtime.core.brain import BrainMapping, BrainRole

        self.BrainMapping = BrainMapping
        self.BrainRole = BrainRole
        self.mapping = BrainMapping()

    def test_default_brains(self):
        """All four brain roles are present by default."""
        brains = self.mapping.get_all_brains()
        self.assertEqual(
            set(brains.keys()), {"commander", "builder", "utility", "safety"}
        )

    def test_commander_model(self):
        """Commander brain uses Claude Opus 4.6."""
        brain = self.mapping.get_brain(self.BrainRole.COMMANDER)
        self.assertEqual(brain["model"], "claude-opus-4.6")
        self.assertEqual(brain["provider"], "anthropic")

    def test_builder_model(self):
        """Builder brain uses GPT-5.3-Codex."""
        brain = self.mapping.get_brain(self.BrainRole.BUILDER)
        self.assertEqual(brain["model"], "gpt-5.3-codex")
        self.assertEqual(brain["provider"], "openai")

    def test_utility_model(self):
        """Utility brain uses Claude Sonnet 4.5."""
        brain = self.mapping.get_brain(self.BrainRole.UTILITY)
        self.assertEqual(brain["model"], "claude-sonnet-4.5")
        self.assertEqual(brain["provider"], "anthropic")

    def test_safety_model(self):
        """Safety brain uses GPT-5.1-Codex-Max."""
        brain = self.mapping.get_brain(self.BrainRole.SAFETY)
        self.assertEqual(brain["model"], "gpt-5.1-codex-max")
        self.assertEqual(brain["provider"], "openai")

    def test_route_thinking(self):
        """Thinking tasks route to commander brain."""
        result = self.mapping.route("thinking")
        self.assertEqual(result["role"], "commander")
        self.assertEqual(result["model"], "claude-opus-4.6")

    def test_route_coding(self):
        """Coding tasks route to builder brain."""
        result = self.mapping.route("coding")
        self.assertEqual(result["role"], "builder")
        self.assertEqual(result["model"], "gpt-5.3-codex")

    def test_route_classification(self):
        """Classification tasks route to utility brain."""
        result = self.mapping.route("classification")
        self.assertEqual(result["role"], "utility")
        self.assertEqual(result["model"], "claude-sonnet-4.5")

    def test_route_verification(self):
        """Verification tasks route to safety brain."""
        result = self.mapping.route("verification")
        self.assertEqual(result["role"], "safety")
        self.assertEqual(result["model"], "gpt-5.1-codex-max")

    def test_unknown_task_falls_back_to_utility(self):
        """Unknown task types default to the utility brain."""
        result = self.mapping.route("unknown_task_xyz")
        self.assertEqual(result["role"], "utility")

    def test_auto_mode_always_disabled(self):
        """Auto mode is always False."""
        self.assertFalse(self.mapping.auto_mode)

    def test_auto_mode_config_rejected(self):
        """Enabling auto_mode via config raises ValueError."""
        with self.assertRaises(ValueError):
            self.BrainMapping({"auto_mode": True})

    def test_routing_table(self):
        """Routing table includes all default task types."""
        table = self.mapping.get_routing_table()
        self.assertEqual(table["planning"], "commander")
        self.assertEqual(table["refactoring"], "builder")
        self.assertEqual(table["intent_detection"], "utility")
        self.assertEqual(table["pre_commit"], "safety")

    def test_config_override_model(self):
        """Operator can override a brain model via config."""
        cfg = {"brains": {"builder": {"model": "custom-codex-7"}}}
        mapping = self.BrainMapping(cfg)
        brain = mapping.get_brain(self.BrainRole.BUILDER)
        self.assertEqual(brain["model"], "custom-codex-7")

    def test_deterministic_routing(self):
        """Same task type always returns the same result."""
        first = self.mapping.route("reasoning")
        second = self.mapping.route("reasoning")
        self.assertEqual(first, second)


def run_tests():
    """Run all tests."""
    print("=" * 60)
    print("SWARMZ Test Suite")
    print("=" * 60)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOperatorSovereignty))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestSwarmzCore))
    suite.addTests(loader.loadTestsFromTestCase(TestPlugins))
    suite.addTests(loader.loadTestsFromTestCase(TestBrainMapping))

    # Run tests
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
    sys.exit(run_tests())
