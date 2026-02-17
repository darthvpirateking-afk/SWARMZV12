# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Test Suite for SWARMZ Companion

Tests dual-mode cognition, execution loop, worker swarms, and all companion features.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from companion import (
    SwarmzCompanion, ModeManager, CompanionMode, OperatorMode,
    SystemMode, CommitState, WorkerType, WorkerSwarm,
    ScoutWorker, BuilderWorker, VerifyWorker,
    CommitEngine, IntelligenceLayer, EvolutionMechanism,
    TaskContext, WorkerResult, ExecutionLog, Memory
)


class TestSystemModes(unittest.TestCase):
    """Test dual-mode cognition system."""
    
    def test_mode_enum(self):
        """Test mode enumeration."""
        self.assertEqual(SystemMode.COMPANION.value, "companion")
        self.assertEqual(SystemMode.OPERATOR.value, "operator")
    
    def test_commit_states(self):
        """Test commit state enumeration."""
        self.assertEqual(CommitState.ACTION_READY.value, "action_ready")
        self.assertEqual(CommitState.NEEDS_CONFIRM.value, "needs_confirm")
        self.assertEqual(CommitState.BLOCKED.value, "blocked")


class TestWorkerSwarm(unittest.TestCase):
    """Test worker swarm system."""
    
    def setUp(self):
        self.swarm = WorkerSwarm()
    
    def test_spawn_scout_worker(self):
        """Test spawning scout worker."""
        worker = self.swarm.spawn_worker(WorkerType.SCOUT)
        self.assertIsInstance(worker, ScoutWorker)
        self.assertEqual(worker.worker_type, WorkerType.SCOUT)
    
    def test_spawn_builder_worker(self):
        """Test spawning builder worker."""
        worker = self.swarm.spawn_worker(WorkerType.BUILDER)
        self.assertIsInstance(worker, BuilderWorker)
        self.assertEqual(worker.worker_type, WorkerType.BUILDER)
    
    def test_spawn_verify_worker(self):
        """Test spawning verify worker."""
        worker = self.swarm.spawn_worker(WorkerType.VERIFY)
        self.assertIsInstance(worker, VerifyWorker)
        self.assertEqual(worker.worker_type, WorkerType.VERIFY)
    
    def test_max_workers_limit(self):
        """Test maximum 3 workers per task."""
        self.swarm.spawn_worker(WorkerType.SCOUT)
        self.swarm.spawn_worker(WorkerType.BUILDER)
        self.swarm.spawn_worker(WorkerType.VERIFY)
        
        with self.assertRaises(ValueError):
            self.swarm.spawn_worker(WorkerType.SCOUT)
    
    def test_workflow_execution(self):
        """Test complete workflow: Scout -> Builder -> Verify."""
        task_context = TaskContext(
            task_id="test_task",
            intent="test intent"
        )
        
        results = self.swarm.execute_workflow(task_context)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].worker_type, WorkerType.SCOUT)
        self.assertEqual(results[1].worker_type, WorkerType.BUILDER)
        self.assertEqual(results[2].worker_type, WorkerType.VERIFY)
    
    def test_clear_workers(self):
        """Test clearing workers after task completion."""
        self.swarm.spawn_worker(WorkerType.SCOUT)
        self.assertEqual(len(self.swarm.active_workers), 1)
        
        self.swarm.clear_workers()
        self.assertEqual(len(self.swarm.active_workers), 0)


class TestCommitEngine(unittest.TestCase):
    """Test commit engine that prevents stalling."""
    
    def setUp(self):
        self.engine = CommitEngine()
    
    def test_action_ready_default(self):
        """Test default behavior: execute unless vetoed."""
        task_context = TaskContext(
            task_id="test",
            intent="safe task",
            parameters={"key": "value"}
        )
        
        state = self.engine.evaluate(task_context)
        self.assertEqual(state, CommitState.ACTION_READY)
    
    def test_blocked_on_missing_params(self):
        """Test BLOCKED state when missing required input."""
        task_context = TaskContext(
            task_id="test",
            intent="needs params",
            parameters={}
        )
        
        state = self.engine.evaluate(task_context)
        self.assertEqual(state, CommitState.BLOCKED)
    
    def test_needs_confirm_on_risks(self):
        """Test NEEDS_CONFIRM for risky operations."""
        task_context = TaskContext(
            task_id="test",
            intent="risky task",
            parameters={"key": "value"},
            worker_results=[
                WorkerResult(
                    result={},
                    risks=["Potential destructive operation"],
                    next_action="needs_confirm"
                )
            ]
        )
        
        state = self.engine.evaluate(task_context)
        self.assertEqual(state, CommitState.NEEDS_CONFIRM)
    
    def test_update_safety_caps(self):
        """Test updating safety boundaries."""
        new_caps = {"max_spend": 200.0, "custom_cap": True}
        self.engine.update_safety_caps(new_caps)
        
        self.assertEqual(self.engine.safety_caps["max_spend"], 200.0)
        self.assertTrue(self.engine.safety_caps["custom_cap"])


class TestIntelligenceLayer(unittest.TestCase):
    """Test intelligence layer for learning."""
    
    def setUp(self):
        self.intelligence = IntelligenceLayer()
    
    def test_predict_outcome_no_history(self):
        """Test prediction with no historical data."""
        task_context = TaskContext(
            task_id="test",
            intent="new task"
        )
        
        prediction = self.intelligence.predict_outcome(task_context)
        
        self.assertIn("predicted_time", prediction)
        self.assertIn("predicted_cost", prediction)
        self.assertIn("success_probability", prediction)
    
    def test_record_execution(self):
        """Test recording execution logs."""
        log_entry = ExecutionLog(
            task_id="test",
            task_name="test_task",
            success=True,
            time_taken=1.5,
            cost=0.5
        )
        
        self.intelligence.record_execution(log_entry)
        self.assertEqual(len(self.intelligence.execution_logs), 1)
    
    def test_predict_with_history(self):
        """Test prediction improves with historical data."""
        # Add some history
        for i in range(5):
            log = ExecutionLog(
                task_id=f"task_{i}",
                task_name="test_task",
                success=True,
                time_taken=2.0,
                cost=1.0
            )
            self.intelligence.record_execution(log)
        
        task_context = TaskContext(
            task_id="new",
            intent="test_task"
        )
        
        prediction = self.intelligence.predict_outcome(task_context)
        self.assertAlmostEqual(prediction["predicted_time"], 2.0)
        self.assertAlmostEqual(prediction["predicted_cost"], 1.0)
    
    def test_evolve_weights(self):
        """Test weight evolution based on performance."""
        initial_weights = self.intelligence.scoring_weights.copy()
        
        performance = {
            "success_rate": 0.9,
            "time_efficiency": 0.7,
            "cost_efficiency": 0.8
        }
        
        self.intelligence.evolve_weights(performance)
        
        # Weights should have changed
        self.assertNotEqual(
            self.intelligence.scoring_weights,
            initial_weights
        )


class TestEvolutionMechanism(unittest.TestCase):
    """Test evolution mechanism for patchpacks."""
    
    def setUp(self):
        self.intelligence = IntelligenceLayer()
        self.evolution = EvolutionMechanism(self.intelligence)
    
    def test_no_patchpack_with_insufficient_data(self):
        """Test that patchpack requires sufficient data."""
        patchpack = self.evolution.generate_patchpack()
        self.assertIsNone(patchpack)
    
    def test_generate_patchpack_on_high_failure(self):
        """Test patchpack generation on high failure rate."""
        # Generate logs with high failure rate
        for i in range(20):
            log = ExecutionLog(
                task_id=f"task_{i}",
                task_name="test",
                success=(i % 2 == 0),  # 50% failure rate
                time_taken=1.0
            )
            self.intelligence.record_execution(log)
        
        patchpack = self.evolution.generate_patchpack()
        self.assertIsNotNone(patchpack)
        self.assertEqual(patchpack["type"], "routing_adjustment")
    
    def test_apply_patchpack_requires_approval(self):
        """Test that patchpack requires approval."""
        patchpack = {
            "type": "routing_adjustment",
            "changes": {}
        }
        
        # Without approval
        result = self.evolution.apply_patchpack(patchpack, approved=False)
        self.assertFalse(result)
        
        # With approval
        result = self.evolution.apply_patchpack(patchpack, approved=True)
        self.assertTrue(result)


class TestCompanionMode(unittest.TestCase):
    """Test companion mode functionality."""
    
    def setUp(self):
        self.companion_mode = CompanionMode()
    
    def test_respond(self):
        """Test conversational response."""
        response = self.companion_mode.respond("Hello!")
        
        self.assertIn("Hello!", response)
        self.assertTrue(response.endswith("[CONVERSATION]"))
    
    def test_conversation_history(self):
        """Test conversation history tracking."""
        self.companion_mode.respond("First message")
        self.companion_mode.respond("Second message")
        
        self.assertEqual(len(self.companion_mode.conversation_history), 4)  # 2 user + 2 assistant


class TestOperatorMode(unittest.TestCase):
    """Test operator mode functionality."""
    
    def setUp(self):
        self.operator_mode = OperatorMode()
    
    def test_execute_task(self):
        """Test task execution in operator mode."""
        response, state = self.operator_mode.execute_task(
            "test task",
            {"param": "value"}
        )
        
        self.assertIn("SITUATION", response)
        self.assertIn("DECISION", response)
        self.assertIsInstance(state, CommitState)
    
    def test_execution_loop(self):
        """Test execution loop: INTAKE â†’ STRUCTURE â†’ DECIDE â†’ COMMIT â†’ EXECUTE â†’ VERIFY â†’ LOG â†’ EVOLVE."""
        response, state = self.operator_mode.execute_task(
            "complete task",
            {"data": "test"}
        )
        
        # Verify all steps are present
        self.assertIn("SITUATION", response)
        self.assertIn("DECISION", response)
        
        if state == CommitState.ACTION_READY:
            self.assertIn("EXECUTION", response)
            self.assertIn("VERIFY", response)
            self.assertIn("LOG", response)
    
    def test_worker_results_recorded(self):
        """Test that worker results are recorded."""
        initial_logs = len(self.operator_mode.intelligence.execution_logs)
        
        self.operator_mode.execute_task("test", {"key": "value"})
        
        self.assertGreater(
            len(self.operator_mode.intelligence.execution_logs),
            initial_logs
        )


class TestModeManager(unittest.TestCase):
    """Test mode manager and mode detection."""
    
    def setUp(self):
        self.manager = ModeManager()
    
    def test_detect_question_as_companion_mode(self):
        """Test questions route to companion mode."""
        mode = self.manager.detect_mode("What is the weather?")
        self.assertEqual(mode, SystemMode.COMPANION)
    
    def test_detect_command_as_operator_mode(self):
        """Test commands route to operator mode."""
        mode = self.manager.detect_mode("Create a new file")
        self.assertEqual(mode, SystemMode.OPERATOR)
    
    def test_mixed_intent_prioritizes_operator(self):
        """Test mixed intent defaults to operator mode."""
        mode = self.manager.detect_mode("What should I do to create a file?")
        self.assertEqual(mode, SystemMode.OPERATOR)
    
    def test_process_input_routes_correctly(self):
        """Test input routing to correct mode."""
        # Question to companion
        response = self.manager.process_input("What is this?")
        self.assertTrue(response.endswith("[CONVERSATION]"))
        
        # Command to operator
        response = self.manager.process_input("Execute task")
        self.assertTrue(
            "[ACTION_READY]" in response or 
            "[NEEDS_CONFIRM]" in response or 
            "[BLOCKED]" in response
        )
    
    def test_memory_persistence(self):
        """Test memory get and update."""
        memory = self.manager.get_memory()
        self.assertIsInstance(memory, Memory)
        
        updates = {
            "preferences": {"theme": "dark"},
            "caps": {"max_workers": 3}
        }
        self.manager.update_memory(updates)
        
        updated_memory = self.manager.get_memory()
        self.assertEqual(updated_memory.preferences["theme"], "dark")
        self.assertEqual(updated_memory.caps["max_workers"], 3)
    
    def test_metrics_calculation(self):
        """Test metrics calculation."""
        # Execute some tasks
        self.manager.process_input("Create file", {"name": "test.txt"})
        
        metrics = self.manager.get_metrics()
        
        self.assertIn("completed_verified_actions_per_day", metrics)
        self.assertIn("error_rate", metrics)
        self.assertIn("total_actions", metrics)


class TestSwarmzCompanion(unittest.TestCase):
    """Test main SWARMZ Companion system."""
    
    def setUp(self):
        self.companion = SwarmzCompanion()
    
    def test_initialization(self):
        """Test companion initialization."""
        self.assertIsNotNone(self.companion.mode_manager)
    
    def test_interact_companion_mode(self):
        """Test interaction in companion mode."""
        response = self.companion.interact("What is SWARMZ?")
        self.assertIn("[CONVERSATION]", response)
    
    def test_interact_operator_mode(self):
        """Test interaction in operator mode."""
        response = self.companion.interact("Run task", {"id": "123"})
        self.assertTrue(any(tag in response for tag in 
            ["[ACTION_READY]", "[NEEDS_CONFIRM]", "[BLOCKED]"]))
    
    def test_get_current_mode(self):
        """Test getting current mode."""
        self.companion.interact("What is this?")
        mode = self.companion.get_current_mode()
        self.assertIsInstance(mode, SystemMode)
    
    def test_get_metrics(self):
        """Test metrics retrieval."""
        metrics = self.companion.get_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("completed_verified_actions_per_day", metrics)
        self.assertIn("error_rate", metrics)
    
    def test_memory_persistence(self):
        """Test memory save and load."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            memory_file = f.name
        
        try:
            # Save memory
            self.companion.mode_manager.update_memory({
                "preferences": {"test": "value"}
            })
            self.companion.save_memory(memory_file)
            
            # Create new companion and load
            new_companion = SwarmzCompanion()
            new_companion.load_memory(memory_file)
            
            memory = new_companion.mode_manager.get_memory()
            self.assertEqual(memory.preferences.get("test"), "value")
        finally:
            Path(memory_file).unlink()


class TestTaskContext(unittest.TestCase):
    """Test task context data structure."""
    
    def test_task_context_creation(self):
        """Test creating task context."""
        context = TaskContext(
            task_id="test_123",
            intent="test intent",
            parameters={"key": "value"}
        )
        
        self.assertEqual(context.task_id, "test_123")
        self.assertEqual(context.intent, "test intent")
        self.assertEqual(context.parameters["key"], "value")
        self.assertEqual(context.commit_state, CommitState.ACTION_READY)
    
    def test_task_context_with_workers(self):
        """Test task context with worker results."""
        context = TaskContext(
            task_id="test",
            intent="test"
        )
        
        result = WorkerResult(
            result={"data": "test"},
            risks=["risk1"],
            next_action="continue"
        )
        
        context.worker_results.append(result)
        self.assertEqual(len(context.worker_results), 1)


def run_companion_tests():
    """Run all companion tests."""
    print("=" * 70)
    print("SWARMZ Companion Test Suite")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSystemModes))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkerSwarm))
    suite.addTests(loader.loadTestsFromTestCase(TestCommitEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligenceLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestEvolutionMechanism))
    suite.addTests(loader.loadTestsFromTestCase(TestCompanionMode))
    suite.addTests(loader.loadTestsFromTestCase(TestOperatorMode))
    suite.addTests(loader.loadTestsFromTestCase(TestModeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSwarmzCompanion))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskContext))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_companion_tests())

