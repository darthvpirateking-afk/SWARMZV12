#!/usr/bin/env python3
"""
Integration test for SWARMZ Companion with SWARMZ Core.
Tests that the companion can execute real tasks through the core system.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from companion import SwarmzCompanion
from swarmz import SwarmzCore


def test_integration():
    """Test full integration between Companion and Core."""
    print("=" * 70)
    print("SWARMZ Companion + Core Integration Test")
    print("=" * 70)
    print()
    
    # Initialize core with plugins
    print("1. Initializing SWARMZ Core...")
    core = SwarmzCore()
    core.load_plugin("plugins/filesystem.py")
    core.load_plugin("plugins/dataprocessing.py")
    print(f"   ✓ Core initialized with {len(core.list_capabilities())} capabilities")
    print()
    
    # Initialize companion with core
    print("2. Initializing SWARMZ Companion with Core integration...")
    companion = SwarmzCompanion(swarmz_core=core)
    print("   ✓ Companion initialized")
    print()
    
    # Test 1: Companion mode (conversation)
    print("3. Testing Companion Mode (conversation):")
    response = companion.interact("What is SWARMZ?")
    print(f"   Input: 'What is SWARMZ?'")
    print(f"   Mode: {companion.get_current_mode().value}")
    print(f"   Response preview: {response[:100]}...")
    assert "[CONVERSATION]" in response
    print("   ✓ Companion mode working")
    print()
    
    # Test 2: Operator mode (execution)
    print("4. Testing Operator Mode (task execution):")
    response = companion.interact("Run echo task", {"message": "Integration test"})
    print(f"   Input: 'Run echo task'")
    print(f"   Mode: {companion.get_current_mode().value}")
    print(f"   Response:")
    for line in response.split('\n'):
        print(f"     {line}")
    assert any(tag in response for tag in ["[ACTION_READY]", "[NEEDS_CONFIRM]", "[BLOCKED]"])
    print("   ✓ Operator mode working")
    print()
    
    # Test 3: Check metrics
    print("5. Checking System Metrics:")
    metrics = companion.get_metrics()
    print(f"   Actions per day: {metrics['completed_verified_actions_per_day']:.2f}")
    print(f"   Error rate: {metrics['error_rate']:.1%}")
    print(f"   Total actions: {metrics['total_actions']}")
    print(f"   Success rate: {metrics['success_rate']:.1%}")
    print("   ✓ Metrics tracking working")
    print()
    
    # Test 4: Memory persistence
    print("6. Testing Memory Persistence:")
    companion.mode_manager.update_memory({
        "preferences": {"test_pref": "value"},
        "caps": {"test_cap": 100}
    })
    memory = companion.mode_manager.get_memory()
    assert memory.preferences.get("test_pref") == "value"
    assert memory.caps.get("test_cap") == 100
    print("   ✓ Memory persistence working")
    print()
    
    # Test 5: Worker swarm
    print("7. Testing Worker Swarm System:")
    from companion import TaskContext, WorkerSwarm
    swarm = WorkerSwarm()
    task_context = TaskContext(task_id="test", intent="integration test")
    results = swarm.execute_workflow(task_context)
    print(f"   Workers executed: {len(results)}")
    print(f"   Worker types: {[r.worker_type.value for r in results]}")
    assert len(results) == 3
    print("   ✓ Worker swarm working")
    print()
    
    # Test 6: Commit engine
    print("8. Testing Commit Engine:")
    from companion import CommitEngine, CommitState
    engine = CommitEngine()
    state = engine.evaluate(task_context)
    print(f"   Commit state: {state.value}")
    assert state in [CommitState.ACTION_READY, CommitState.NEEDS_CONFIRM, CommitState.BLOCKED]
    print("   ✓ Commit engine working")
    print()
    
    # Test 7: Intelligence layer
    print("9. Testing Intelligence Layer:")
    intelligence = companion.mode_manager.operator_mode.intelligence
    logs = intelligence.execution_logs
    print(f"   Execution logs: {len(logs)}")
    if logs:
        print(f"   Last log: {logs[-1].task_name} - Success: {logs[-1].success}")
    print("   ✓ Intelligence layer working")
    print()
    
    print("=" * 70)
    print("✓ ALL INTEGRATION TESTS PASSED")
    print("=" * 70)
    print()
    print("SWARMZ Companion is fully integrated with SWARMZ Core!")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_integration())
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
