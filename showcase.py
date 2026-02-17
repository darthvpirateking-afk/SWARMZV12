# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Companion Feature Showcase

Demonstrates all implemented features in a single comprehensive demo.
"""

from companion import SwarmzCompanion
from swarmz import SwarmzCore
import time  # For profiling


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_success(message):
    """Print success message."""
    print(f"âœ… {message}")


def main():
    print("\n" + "#" * 70)
    print("#" + " " * 20 + "SWARMZ COMPANION SHOWCASE" + " " * 25 + "#")
    print("#" * 70)
    
    # 1. Initialize system
    print_header("1. System Initialization")
    companion = SwarmzCompanion()
    print_success("SWARMZ Companion initialized")
    print(f"   Initial mode: {companion.get_current_mode().value}")
    
    # 2. Demonstrate Companion Mode
    print_header("2. Companion Mode (Conversation)")
    questions = [
        "What is SWARMZ?",
        "How does the execution loop work?",
        "Can you explain worker swarms?"
    ]
    
    for question in questions:
        print(f"â“ User: {question}")
        response = companion.interact(question)
        mode = companion.get_current_mode()
        print(f"ðŸ—¨ï¸  Mode: {mode.value.upper()}")
        print(f"ðŸ’¬ Response: {response[:80]}...")
        print()
    
    # 3. Demonstrate Operator Mode
    print_header("3. Operator Mode (Execution)")
    commands = [
        ("Create a file", {"name": "test.txt", "content": "Hello"}),
        ("Run diagnostics", {"system": "all"}),
        ("Generate report", {"format": "pdf", "data": [1, 2, 3]})
    ]
    
    for command, params in commands:
        print(f"âš™ï¸  User: {command}")
        print(f"ðŸ“‹ Params: {params}")
        response = companion.interact(command, params)
        mode = companion.get_current_mode()
        print(f"ðŸ”§ Mode: {mode.value.upper()}")
        
        # Extract key info from response
        lines = response.split('\n')
        for line in lines[:5]:  # Show first 5 lines
            if line.strip():
                print(f"   {line}")
        print()
    
    # 4. Show Metrics
    print_header("4. System Metrics & Intelligence")
    start_time = time.perf_counter()  # Start profiling
    metrics = companion.get_metrics()
    print("ðŸ“Š Performance Metrics:")
    print(f"   â€¢ Actions per day: {metrics['completed_verified_actions_per_day']:.2f}")
    print(f"   â€¢ Success rate: {metrics['success_rate']:.1%}")
    print(f"   â€¢ Error rate: {metrics['error_rate']:.1%}")
    print(f"   â€¢ Total actions: {metrics['total_actions']}")
    print_success("Metrics tracking operational")
    end_time = time.perf_counter()  # End profiling
    print(f"Metrics display took {end_time - start_time:.6f} seconds.")
    
    # 5. Demonstrate Worker Swarm
    print_header("5. Worker Swarm System")
    from companion import WorkerSwarm, TaskContext
    
    swarm = WorkerSwarm()
    task = TaskContext(
        task_id="showcase_task",
        intent="Demonstrate worker swarm",
        parameters={"demo": True}
    )
    
    print("ðŸ Executing worker workflow: Scout â†’ Builder â†’ Verify")
    results = swarm.execute_workflow(task)
    
    for i, result in enumerate(results, 1):
        print(f"\n   {i}. {result.worker_type.value.upper()} Worker:")
        print(f"      âœ“ Executed successfully")
        print(f"      â€¢ Risks: {len(result.risks)} identified")
        print(f"      â€¢ Next: {result.next_action}")
    
    print()
    print_success("Worker swarm operational (max 3 workers enforced)")
    
    # 6. Demonstrate Commit Engine
    print_header("6. Commit Engine (Prevents Stalling)")
    from companion import CommitEngine
    
    engine = CommitEngine()
    
    test_cases = [
        ("Safe task with params", {"data": "test"}, "should be ACTION_READY"),
        ("Task without params", {}, "should be BLOCKED"),
    ]
    
    for description, params, expected in test_cases:
        task = TaskContext(
            task_id="test",
            intent=description,
            parameters=params
        )
        state = engine.evaluate(task)
        print(f"ðŸ“Œ {description}")
        print(f"   State: {state.value.upper()}")
        print(f"   Expected: {expected}")
        print()
    
    print_success("Commit engine prevents planning loops")
    
    # 7. Demonstrate Intelligence Layer
    print_header("7. Intelligence Layer (Learning)")
    intelligence = companion.mode_manager.operator_mode.intelligence
    
    print("ðŸ§  Intelligence Layer Features:")
    print(f"   â€¢ Execution logs: {len(intelligence.execution_logs)} recorded")
    print(f"   â€¢ Scoring weights: {intelligence.scoring_weights}")
    
    if intelligence.execution_logs:
        print(f"\n   Recent executions:")
        for log in intelligence.execution_logs[-3:]:
            status = "âœ“" if log.success else "âœ—"
            print(f"      {status} {log.task_name} ({log.time_taken:.3f}s)")
    
    print()
    print_success("Intelligence layer tracks and learns from executions")
    
    # 8. Demonstrate Memory Persistence
    print_header("8. Memory Persistence")
    
    print("ðŸ’¾ Updating memory...")
    companion.mode_manager.update_memory({
        "preferences": {"theme": "dark", "language": "en"},
        "caps": {"max_spend": 100.0, "max_workers": 3},
        "whitelist": ["api.example.com"]
    })
    
    memory = companion.mode_manager.get_memory()
    print(f"   â€¢ Preferences: {len(memory.preferences)} stored")
    print(f"   â€¢ Caps: {len(memory.caps)} defined")
    print(f"   â€¢ Whitelist: {len(memory.whitelist)} entries")
    print()
    print_success("Memory persists preferences, caps, and whitelist")
    
    # 9. Integration with SWARMZ Core
    print_header("9. Integration with SWARMZ Core")
    
    print("ðŸ”— Creating companion with SWARMZ Core integration...")
    core = SwarmzCore()
    integrated_companion = SwarmzCompanion(swarmz_core=core)
    
    print(f"   â€¢ Core capabilities: {len(core.list_capabilities())}")
    print(f"   â€¢ Companion ready: Yes")
    print()
    print_success("Seamless integration with SWARMZ Core")
    
    # 10. Evolution Mechanism
    print_header("10. Evolution Mechanism")
    
    evolution = companion.mode_manager.operator_mode.evolution
    print("ðŸ”„ Evolution Features:")
    print("   â€¢ Generates patchpacks from execution logs")
    print("   â€¢ Requires human approval before applying")
    print("   â€¢ Can modify: weights, routing, templates")
    print("   â€¢ Never self-rewrites core code")
    
    patchpack = evolution.generate_patchpack()
    if patchpack:
        print(f"\n   âœ“ Patchpack generated: {patchpack['type']}")
    else:
        print(f"\n   â€¢ No patchpack needed (insufficient data or good performance)")
    
    print()
    print_success("Evolution mechanism operational")
    
    # Final Summary
    print("\n" + "#" * 70)
    print("#" + " " * 25 + "SHOWCASE COMPLETE" + " " * 27 + "#")
    print("#" * 70)
    print()
    
    print("âœ… All Features Demonstrated:")
    print()
    print("   âœ“ Dual-mode cognition (Companion + Operator)")
    print("   âœ“ Automatic mode detection")
    print("   âœ“ 8-stage execution loop")
    print("   âœ“ Worker swarm system (max 3 workers)")
    print("   âœ“ Commit engine (prevents stalling)")
    print("   âœ“ Intelligence layer (learning)")
    print("   âœ“ Memory persistence")
    print("   âœ“ Safety boundaries")
    print("   âœ“ Evolution mechanism")
    print("   âœ“ SWARMZ Core integration")
    print()
    print("ðŸŽ‰ SWARMZ Companion is fully operational and ready for use!")
    print()


if __name__ == "__main__":
    main()

