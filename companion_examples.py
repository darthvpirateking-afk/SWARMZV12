# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Companion Examples

Demonstrates various usage patterns for the SWARMZ Companion system.
"""

from companion import (
    SwarmzCompanion, CommitState,
    WorkerSwarm, TaskContext
)
from swarmz import SwarmzCore


def example_basic_interaction():
    """Example 1: Basic interaction with mode auto-detection."""
    print("=" * 70)
    print("Example 1: Basic Interaction")
    print("=" * 70)
    
    companion = SwarmzCompanion()
    
    # Question â†’ Companion Mode
    print("\n1. Question (Companion Mode):")
    response = companion.interact("What is SWARMZ?")
    print(f"Input: 'What is SWARMZ?'")
    print(f"Mode: {companion.get_current_mode().value}")
    print(f"Response: {response[:100]}...")
    
    # Command â†’ Operator Mode
    print("\n2. Command (Operator Mode):")
    response = companion.interact("Create a backup", {"name": "backup.txt"})
    print(f"Input: 'Create a backup'")
    print(f"Mode: {companion.get_current_mode().value}")
    print(f"Response:\n{response}")
    
    print("\n" + "=" * 70 + "\n")


def example_with_swarmz_core():
    """Example 2: Integration with SWARMZ Core."""
    print("=" * 70)
    print("Example 2: Integration with SWARMZ Core")
    print("=" * 70)
    
    # Initialize SWARMZ Core with plugins
    core = SwarmzCore()
    core.load_plugin("plugins/filesystem.py")
    
    # Create companion with core integration
    companion = SwarmzCompanion(swarmz_core=core)
    
    # Execute real task through core
    print("\nExecuting task through SWARMZ Core:")
    response = companion.interact("Run system info task")
    print(response)
    
    print("\n" + "=" * 70 + "\n")


def example_worker_swarm():
    """Example 3: Direct worker swarm usage."""
    print("=" * 70)
    print("Example 3: Worker Swarm System")
    print("=" * 70)
    
    # Create worker swarm
    swarm = WorkerSwarm()
    
    # Create task context
    task_context = TaskContext(
        task_id="demo_task",
        intent="Process data and generate report",
        parameters={"data": "sample data"}
    )
    
    print("\nExecuting Scout â†’ Builder â†’ Verify workflow:")
    results = swarm.execute_workflow(task_context)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.worker_type.value.upper()} Worker:")
        print(f"   Result: {result.result}")
        print(f"   Risks: {result.risks if result.risks else 'None'}")
        print(f"   Next Action: {result.next_action}")
    
    print("\n" + "=" * 70 + "\n")


def example_intelligence_learning():
    """Example 4: Intelligence layer and learning."""
    print("=" * 70)
    print("Example 4: Intelligence Layer & Learning")
    print("=" * 70)
    
    companion = SwarmzCompanion()
    
    # Execute several tasks
    print("\nExecuting tasks to build history:")
    for i in range(5):
        response = companion.interact(f"Task {i}", {"id": i})
        print(f"  Task {i}: {'âœ“' if '[ACTION_READY]' in response else 'â—‹'}")
    
    # Check metrics
    print("\nMetrics after execution:")
    metrics = companion.get_metrics()
    print(f"  Total actions: {metrics['total_actions']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    print(f"  Error rate: {metrics['error_rate']:.1%}")
    print(f"  Actions/day: {metrics['completed_verified_actions_per_day']:.2f}")
    
    # View execution logs
    print("\nExecution logs:")
    logs = companion.mode_manager.operator_mode.intelligence.execution_logs
    for log in logs[-3:]:  # Show last 3
        print(f"  â€¢ {log.task_name}: {log.success} ({log.time_taken:.3f}s)")
    
    print("\n" + "=" * 70 + "\n")


def example_memory_persistence():
    """Example 5: Memory persistence."""
    print("=" * 70)
    print("Example 5: Memory Persistence")
    print("=" * 70)
    
    companion = SwarmzCompanion()
    
    # Update memory
    print("\nUpdating memory:")
    companion.mode_manager.update_memory({
        "preferences": {
            "theme": "dark",
            "language": "en",
            "notifications": True
        },
        "caps": {
            "max_spend": 100.0,
            "max_workers": 3
        },
        "whitelist": [
            "api.example.com",
            "trusted-service.com"
        ]
    })
    
    # View memory
    memory = companion.mode_manager.get_memory()
    print(f"  Preferences: {memory.preferences}")
    print(f"  Caps: {memory.caps}")
    print(f"  Whitelist: {memory.whitelist}")
    
    # Save to file
    print("\nSaving memory to file...")
    companion.save_memory("example_memory.json")
    print("  âœ“ Saved to example_memory.json")
    
    # Load in new companion
    print("\nLoading memory in new companion...")
    new_companion = SwarmzCompanion()
    new_companion.load_memory("example_memory.json")
    new_memory = new_companion.mode_manager.get_memory()
    print(f"  âœ“ Loaded preferences: {new_memory.preferences}")
    
    print("\n" + "=" * 70 + "\n")


def example_commit_states():
    """Example 6: Commit engine states."""
    print("=" * 70)
    print("Example 6: Commit Engine States")
    print("=" * 70)
    
    companion = SwarmzCompanion()
    
    # ACTION_READY (default)
    print("\n1. ACTION_READY (safe operation):")
    response = companion.interact("Generate report", {"format": "pdf"})
    print(f"   State: {CommitState.ACTION_READY.value if '[ACTION_READY]' in response else 'other'}")
    
    # BLOCKED (missing parameters)
    print("\n2. BLOCKED (missing parameters):")
    response = companion.interact("Process data")  # No params
    print(f"   State: {CommitState.BLOCKED.value if '[BLOCKED]' in response else 'other'}")
    
    # NEEDS_CONFIRM (risky operation)
    print("\n3. NEEDS_CONFIRM (risky operation):")
    response = companion.interact("Delete files", {"pattern": "*.tmp"})
    print(f"   State detected from response")
    
    print("\n" + "=" * 70 + "\n")


def example_evolution_mechanism():
    """Example 7: Evolution mechanism."""
    print("=" * 70)
    print("Example 7: Evolution Mechanism")
    print("=" * 70)
    
    companion = SwarmzCompanion()
    
    # Generate many tasks with failures
    print("\nGenerating execution history...")
    for i in range(25):
        companion.interact(f"Task {i}", {"id": i})
    
    # Check for patchpack generation
    evolution = companion.mode_manager.operator_mode.evolution
    intelligence = companion.mode_manager.operator_mode.intelligence
    
    print(f"  Total executions: {len(intelligence.execution_logs)}")
    
    # Try to generate patchpack
    patchpack = evolution.generate_patchpack()
    if patchpack:
        print("\nâœ“ Patchpack generated!")
        print(f"  Type: {patchpack['type']}")
        print(f"  Description: {patchpack['description']}")
        print(f"  Changes: {patchpack['changes']}")
        print("\n  (Waiting for human approval before applying)")
    else:
        print("\nâ—‹ No patchpack needed yet (not enough data or performance is good)")
    
    print("\n" + "=" * 70 + "\n")


def example_custom_workers():
    """Example 8: Custom worker implementation."""
    print("=" * 70)
    print("Example 8: Custom Worker Implementation")
    print("=" * 70)
    
    from companion import Worker, WorkerType, WorkerResult
    
    class CustomAnalyzerWorker(Worker):
        """Custom worker that analyzes data."""
        
        def __init__(self):
            super().__init__(WorkerType.SCOUT)
        
        def execute(self, task_context: TaskContext) -> WorkerResult:
            # Custom analysis logic
            data = task_context.parameters.get("data", [])
            analysis = {
                "items_count": len(data) if isinstance(data, list) else 0,
                "has_data": bool(data),
                "analysis_complete": True
            }
            
            return WorkerResult(
                result=analysis,
                risks=["None identified"],
                next_action="proceed_with_confidence",
                worker_type=self.worker_type
            )
    
    # Use custom worker
    print("\nUsing custom analyzer worker:")
    task = TaskContext(
        task_id="analysis",
        intent="Analyze dataset",
        parameters={"data": [1, 2, 3, 4, 5]}
    )
    
    worker = CustomAnalyzerWorker()
    result = worker.execute(task)
    
    print(f"  Result: {result.result}")
    print(f"  Risks: {result.risks}")
    print(f"  Next Action: {result.next_action}")
    
    print("\n" + "=" * 70 + "\n")


def main():
    """Run all examples."""
    print("\n")
    print("#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + " " * 20 + "SWARMZ Companion Examples" + " " * 23 + "#")
    print("#" + " " * 68 + "#")
    print("#" * 70)
    print("\n")
    
    examples = [
        ("Basic Interaction", example_basic_interaction),
        ("SWARMZ Core Integration", example_with_swarmz_core),
        ("Worker Swarm System", example_worker_swarm),
        ("Intelligence & Learning", example_intelligence_learning),
        ("Memory Persistence", example_memory_persistence),
        ("Commit Engine States", example_commit_states),
        ("Evolution Mechanism", example_evolution_mechanism),
        ("Custom Workers", example_custom_workers),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{'=' * 70}")
        print(f"Running Example {i}/{len(examples)}: {name}")
        print(f"{'=' * 70}\n")
        
        try:
            func()
        except Exception as e:
            print(f"\nâŒ Error in {name}: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "#" * 70)
    print("# All examples completed!")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    main()

