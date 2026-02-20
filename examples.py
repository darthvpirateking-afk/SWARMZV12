# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Examples - Demonstrating Operator Sovereignty

This script demonstrates various features of the SWARMZ system.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swarmz import SwarmzCore


def example_basic_tasks():
    """Demonstrate basic task execution."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Task Execution")
    print("=" * 60)
    
    swarmz = SwarmzCore()
    
    # Echo task
    result = swarmz.execute("echo", message="Hello from SWARMZ!")
    print(f"Echo result: {result}")
    
    # System info
    info = swarmz.execute("system_info")
    print(f"\nSystem Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")


def example_operator_sovereignty():
    """Demonstrate operator sovereignty features."""
    print("\n" + "=" * 60)
    print("Example 2: Operator Sovereignty")
    print("=" * 60)
    
    swarmz = SwarmzCore()
    
    # Execute some tasks
    swarmz.execute("echo", message="Task 1")
    swarmz.execute("echo", message="Task 2")
    swarmz.execute("system_info")
    
    # Show audit log
    print("\nAudit Log (demonstrating transparency):")
    for idx, entry in enumerate(swarmz.get_audit_log(), 1):
        print(f"{idx}. Action: {entry['action']}")
        print(f"   Approved: {entry['approved']}")


def example_code_execution():
    """Demonstrate arbitrary code execution (operator sovereignty)."""
    print("\n" + "=" * 60)
    print("Example 3: Arbitrary Code Execution (Operator Sovereignty)")
    print("=" * 60)
    
    swarmz = SwarmzCore()
    
    # Example 1: Simple calculation
    code1 = "result = sum([1, 2, 3, 4, 5])"
    result1 = swarmz.execute("execute_python", code=code1)
    print(f"Sum calculation: {result1}")
    
    # Example 2: String manipulation
    code2 = """
text = "SWARMZ"
result = text.lower() + " - operator sovereign"
"""
    result2 = swarmz.execute("execute_python", code=code2)
    print(f"String manipulation: {result2}")
    
    # Example 3: List comprehension
    code3 = "result = [x**2 for x in range(5)]"
    result3 = swarmz.execute("execute_python", code=code3)
    print(f"Squares: {result3}")


def example_plugin_system():
    """Demonstrate plugin system."""
    print("\n" + "=" * 60)
    print("Example 4: Plugin System (Extensibility)")
    print("=" * 60)
    
    swarmz = SwarmzCore()
    
    # Load filesystem plugin
    fs_plugin = Path(__file__).parent / "plugins" / "filesystem.py"
    if fs_plugin.exists():
        plugin_name = swarmz.load_plugin(str(fs_plugin))
        print(f"âœ“ Loaded plugin: {plugin_name}")
        
        # Use filesystem tasks
        files = swarmz.execute("fs_list", path=".")
        print(f"\nFiles in current directory: {len(files)} items")
        print("Sample:", files[:5])
    
    # Load data processing plugin
    data_plugin = Path(__file__).parent / "plugins" / "dataprocessing.py"
    if data_plugin.exists():
        plugin_name = swarmz.load_plugin(str(data_plugin))
        print(f"\nâœ“ Loaded plugin: {plugin_name}")
        
        # Use data processing tasks
        text = "SWARMZ - Operator Sovereign System"
        hash_result = swarmz.execute("data_hash", text=text, algorithm="sha256")
        print(f"\nHash of '{text}':")
        print(f"  {hash_result}")
    
    # Show all capabilities
    print(f"\nTotal capabilities after loading plugins: {len(swarmz.list_capabilities())}")


def example_custom_plugin():
    """Demonstrate creating and loading a custom plugin."""
    print("\n" + "=" * 60)
    print("Example 5: Custom Plugin Creation")
    print("=" * 60)
    
    import tempfile
    
    # Create a custom plugin
    plugin_code = '''
"""Custom Math Plugin"""

def register(executor):
    def factorial(n):
        """Calculate factorial of n."""
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    
    def fibonacci(n):
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    executor.register_task("math_factorial", factorial, {
        "description": "Calculate factorial",
        "params": {"n": "integer"},
        "category": "math"
    })
    
    executor.register_task("math_fibonacci", fibonacci, {
        "description": "Calculate Fibonacci number",
        "params": {"n": "integer"},
        "category": "math"
    })
'''
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(plugin_code)
        plugin_path = f.name
    
    try:
        swarmz = SwarmzCore()
        
        # Load the custom plugin
        plugin_name = swarmz.load_plugin(plugin_path)
        print(f"âœ“ Loaded custom plugin: {plugin_name}")
        
        # Use the custom tasks
        factorial_5 = swarmz.execute("math_factorial", n=5)
        print(f"\nFactorial of 5: {factorial_5}")
        
        fibonacci_10 = swarmz.execute("math_fibonacci", n=10)
        print(f"10th Fibonacci number: {fibonacci_10}")
        
    finally:
        # Clean up
        Path(plugin_path).unlink()


def example_do_anything():
    """Demonstrate 'do anything' capability."""
    print("\n" + "=" * 60)
    print("Example 6: 'Do Anything' Capability")
    print("=" * 60)
    
    swarmz = SwarmzCore()
    
    print("The 'do anything' philosophy means SWARMZ can:")
    print("1. Execute arbitrary Python code")
    print("2. Load plugins dynamically")
    print("3. Extend capabilities on-the-fly")
    print("4. Integrate with any Python library")
    print()
    
    # Example: Complex operation combining multiple capabilities
    print("Complex Example: Data analysis workflow")
    
    # Step 1: Generate data
    code = """
import random
result = [random.randint(1, 100) for _ in range(10)]
"""
    data = swarmz.execute("execute_python", code=code)
    print(f"Generated data: {data}")
    
    # Step 2: Process data
    code2 = f"""
data = {data}
result = {{
    'sum': sum(data),
    'average': sum(data) / len(data),
    'min': min(data),
    'max': max(data)
}}
"""
    stats = swarmz.execute("execute_python", code=code2)
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")


def show_examples():
    """Minimal scaffold for examples."""
    pass


def main():
    """Run all examples."""
    print("=" * 60)
    print("SWARMZ Examples - Operator-Sovereign 'Do Anything' System")
    print("=" * 60)
    
    try:
        example_basic_tasks()
        example_operator_sovereignty()
        example_code_execution()
        example_plugin_system()
        example_custom_plugin()
        example_do_anything()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("â€¢ SWARMZ gives operators complete sovereignty")
        print("â€¢ Extensible through plugins")
        print("â€¢ Transparent through audit logs")
        print("â€¢ 'Do anything' through code execution and plugins")
        print("â€¢ Built for trusted operators who need flexibility")
        
    except Exception as e:
        print(f"\nâœ— Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

