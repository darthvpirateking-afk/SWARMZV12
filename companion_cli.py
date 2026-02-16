#!/usr/bin/env python3
"""
SWARMZ Companion CLI - Interactive Interface

Command-line interface for the SWARMZ Companion system.
Provides both conversational and operational capabilities.
"""

import sys
import argparse
import json
from pathlib import Path
from companion import SwarmzCompanion, SystemMode
from swarmz import SwarmzCore


def print_mode_indicator(mode: SystemMode):
    """Print visual indicator of current mode."""
    if mode == SystemMode.COMPANION:
        print("🗨️  [COMPANION MODE]", end=" ")
    else:
        print("⚙️  [OPERATOR MODE]", end=" ")


def interactive_mode(companion: SwarmzCompanion, use_core: bool = False):
    """Run interactive companion mode."""
    print("=" * 70)
    print("SWARMZ Companion - Interactive Mode")
    print("=" * 70)
    print()
    print("Dual-Mode Cognition System:")
    print("  🗨️  Companion Mode - Conversation, explanations, personality")
    print("  ⚙️  Operator Mode  - Real-world execution, spawns workers")
    print()
    print("Mode selection is automatic based on your input:")
    print("  - Questions → Companion Mode")
    print("  - Commands → Operator Mode")
    print()
    print("Commands: help, metrics, memory, mode, exit")
    print("=" * 70)
    print()
    
    while True:
        try:
            # Show mode indicator
            print_mode_indicator(companion.get_current_mode())
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            # Handle meta commands
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "help":
                print("\nAvailable Commands:")
                print("  help     - Show this help message")
                print("  metrics  - Show system performance metrics")
                print("  memory   - Show persistent memory")
                print("  mode     - Show current mode")
                print("  exit     - Exit interactive mode")
                print("\nJust type naturally - mode will be auto-detected!")
                print()
                continue
            
            if user_input.lower() == "metrics":
                metrics = companion.get_metrics()
                print("\n📊 System Metrics:")
                print(f"  Actions/day: {metrics['completed_verified_actions_per_day']:.2f}")
                print(f"  Success rate: {metrics['success_rate']:.1%}")
                print(f"  Error rate: {metrics['error_rate']:.1%}")
                print(f"  Total actions: {metrics['total_actions']}")
                print()
                continue
            
            if user_input.lower() == "memory":
                memory = companion.mode_manager.get_memory()
                print("\n💾 Persistent Memory:")
                print(f"  Preferences: {memory.preferences}")
                print(f"  Caps: {memory.caps}")
                print(f"  Whitelist: {memory.whitelist}")
                print(f"  Projects: {len(memory.ongoing_projects)}")
                print()
                continue
            
            if user_input.lower() == "mode":
                current_mode = companion.get_current_mode()
                print(f"\nCurrent mode: {current_mode.value.upper()}")
                print()
                continue
            
            # Process input through companion
            response = companion.interact(user_input)
            print()
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nUse 'exit' to quit")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="SWARMZ Companion - Personal AI Companion with Dual-Mode Cognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  companion_cli.py --interactive              Start interactive mode
  companion_cli.py --input "What is SWARMZ?"  Process single input
  companion_cli.py --use-core --interactive   Use full SWARMZ core
  companion_cli.py --metrics                  Show system metrics
        """
    )
    
    parser.add_argument('--interactive', action='store_true',
                       help='Start interactive mode')
    parser.add_argument('--input', type=str,
                       help='Process a single input')
    parser.add_argument('--params', type=str,
                       help='JSON parameters for the input')
    parser.add_argument('--use-core', action='store_true',
                       help='Integrate with full SWARMZ core')
    parser.add_argument('--metrics', action='store_true',
                       help='Show system metrics')
    parser.add_argument('--memory-file', type=str,
                       default='companion_memory.json',
                       help='Path to memory persistence file')
    
    args = parser.parse_args()
    
    # Initialize companion
    swarmz_core = None
    if args.use_core:
        swarmz_core = SwarmzCore()
        print("✓ Integrated with SWARMZ Core")
    
    companion = SwarmzCompanion(swarmz_core)
    
    # Load memory if exists
    if Path(args.memory_file).exists():
        companion.load_memory(args.memory_file)
        print(f"✓ Loaded memory from {args.memory_file}")
    
    # Show metrics
    if args.metrics:
        print("SWARMZ Companion Metrics")
        print("=" * 60)
        metrics = companion.get_metrics()
        print(f"Completed Verified Actions/Day: {metrics['completed_verified_actions_per_day']:.2f}")
        print(f"Error Rate: {metrics['error_rate']:.1%}")
        print(f"Total Actions: {metrics['total_actions']}")
        print(f"Success Rate: {metrics['success_rate']:.1%}")
        return 0
    
    # Process single input
    if args.input:
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON in params: {args.params}")
                return 1
        
        response = companion.interact(args.input, params)
        print(response)
        
        # Save memory
        companion.save_memory(args.memory_file)
        return 0
    
    # Interactive mode
    if args.interactive:
        interactive_mode(companion, args.use_core)
        
        # Save memory on exit
        companion.save_memory(args.memory_file)
        print(f"💾 Memory saved to {args.memory_file}")
        return 0
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
