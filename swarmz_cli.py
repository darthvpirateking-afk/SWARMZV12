# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Command Line Interface

Operator-sovereign interface for interacting with the SWARMZ system.
"""

import sys
import argparse
import json
from pathlib import Path
from swarmz import SwarmzCore


def main():
    parser = argparse.ArgumentParser(
        description="SWARMZ - Operator-Sovereign 'Do Anything' System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  swarmz_cli.py --list                              List all capabilities
  swarmz_cli.py --task echo --params '{"message": "Hello"}'
  swarmz_cli.py --load-plugin plugins/filesystem.py
  swarmz_cli.py --task fs_list --params '{"path": "."}'
  swarmz_cli.py --interactive                       Start interactive mode
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all available tasks')
    parser.add_argument('--task', type=str,
                       help='Task name to execute')
    parser.add_argument('--params', type=str,
                       help='JSON string of parameters for the task')
    parser.add_argument('--load-plugin', type=str,
                       help='Path to plugin file to load')
    parser.add_argument('--config', type=str,
                       help='Path to configuration file')
    parser.add_argument('--audit', action='store_true',
                       help='Show audit log')
    parser.add_argument('--interactive', action='store_true',
                       help='Start interactive mode')
    
    args = parser.parse_args()
    
    # Initialize SWARMZ
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    swarmz = SwarmzCore(config)
    
    # Load plugin if specified
    if args.load_plugin:
        plugin_path = Path(args.load_plugin)
        if plugin_path.exists():
            plugin_name = swarmz.load_plugin(str(plugin_path))
            print(f"âœ“ Loaded plugin: {plugin_name}")
        else:
            print(f"âœ— Plugin not found: {args.load_plugin}")
            return 1
    
    # List capabilities
    if args.list:
        print("Available SWARMZ Capabilities:")
        print("=" * 60)
        capabilities = swarmz.list_capabilities()
        
        # Group by category
        categories = {}
        for name, meta in capabilities.items():
            category = meta.get('category', 'core')
            if category not in categories:
                categories[category] = []
            categories[category].append((name, meta))
        
        for category, tasks in sorted(categories.items()):
            print(f"\n{category.upper()}:")
            for name, meta in sorted(tasks):
                desc = meta.get('description', 'No description')
                print(f"  â€¢ {name:20s} - {desc}")
        
        print(f"\nTotal capabilities: {len(capabilities)}")
        return 0
    
    # Execute task
    if args.task:
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"âœ— Invalid JSON in params: {args.params}")
                return 1
        
        try:
            result = swarmz.execute(args.task, **params)
            print(f"âœ“ Task '{args.task}' executed successfully")
            print(f"Result: {result}")
            return 0
        except Exception as e:
            print(f"âœ— Error executing task '{args.task}': {e}")
            return 1
    
    # Show audit log
    if args.audit:
        print("SWARMZ Audit Log:")
        print("=" * 60)
        for idx, entry in enumerate(swarmz.get_audit_log(), 1):
            print(f"{idx}. {entry['action']}")
            print(f"   Context: {entry['context']}")
            print(f"   Approved: {entry['approved']}")
        return 0
    
    # Interactive mode
    if args.interactive:
        print("=" * 60)
        print("SWARMZ Interactive Mode")
        print("Operator maintains full sovereignty")
        print("=" * 60)
        print("Commands: list, task <name> [params], load <plugin>, audit, help, exit")
        print()
        
        while True:
            try:
                command = input("swarmz> ").strip()
                
                if not command:
                    continue
                
                if command == "exit":
                    print("Goodbye!")
                    break
                
                if command == "help":
                    print("Available commands:")
                    print("  list              - List all capabilities")
                    print("  task <name>       - Execute a task")
                    print("  load <plugin>     - Load a plugin")
                    print("  audit             - Show audit log")
                    print("  help              - Show this help")
                    print("  exit              - Exit interactive mode")
                    continue
                
                if command == "list":
                    capabilities = swarmz.list_capabilities()
                    for name, meta in sorted(capabilities.items()):
                        print(f"  â€¢ {name:20s} - {meta.get('description', '')}")
                    continue
                
                if command == "audit":
                    for idx, entry in enumerate(swarmz.get_audit_log(), 1):
                        print(f"{idx}. {entry['action']} - {entry['approved']}")
                    continue
                
                if command.startswith("load "):
                    plugin_path = command[5:].strip()
                    try:
                        name = swarmz.load_plugin(plugin_path)
                        print(f"âœ“ Loaded plugin: {name}")
                    except Exception as e:
                        print(f"âœ— Error loading plugin: {e}")
                    continue
                
                if command.startswith("task "):
                    parts = command[5:].strip().split(None, 1)
                    task_name = parts[0]
                    params = json.loads(parts[1]) if len(parts) > 1 else {}
                    
                    try:
                        result = swarmz.execute(task_name, **params)
                        print(f"âœ“ Result: {result}")
                    except Exception as e:
                        print(f"âœ— Error: {e}")
                    continue
                
                print("Unknown command. Type 'help' for available commands.")
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"âœ— Error: {e}")
        
        return 0
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

