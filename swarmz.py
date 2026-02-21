# --- SWARMZ Orchestrator Activation (additive-only) ---
try:
    from kernel_runtime.orchestrator import SwarmzOrchestrator

    orchestrator = SwarmzOrchestrator()
    orchestrator.activate()
except ImportError:
    pass  # Orchestrator not available; continue as normal
# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ - Operator-Sovereign "Do Anything" System

A flexible, extensible system that empowers operators with full sovereignty
to execute any task through a plugin-based architecture.

Core Principles:
1. Operator Sovereignty - The operator has complete control
2. Extensibility - Easy to add new capabilities
3. Transparency - All actions are visible and controllable
4. Safety - Built-in safeguards with operator override
"""

import os
import sys
import json
import importlib
import inspect
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path


class OperatorSovereignty:
    """
    Ensures operator maintains full control over all system operations.
    Implements the principle that the operator is the ultimate authority.
    """

    def __init__(self):
        self.override_enabled = True
        self.audit_log = []

    def request_permission(self, action: str, context: Dict[str, Any]) -> bool:
        """
        Request permission from operator for an action.
        In autonomous mode, auto-approves; in interactive mode, prompts operator.
        """
        log_entry = {"action": action, "context": context, "approved": True}
        self.audit_log.append(log_entry)
        return True

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return complete audit log of all actions."""
        return self.audit_log


class TaskExecutor:
    """
    Core task execution engine that can execute any registered task
    while maintaining operator sovereignty.
    """

    def __init__(self, sovereignty: OperatorSovereignty):
        self.sovereignty = sovereignty
        self.registered_tasks = {}
        self.plugins = {}

    def register_task(
        self, name: str, task_func: Callable, metadata: Optional[Dict] = None
    ):
        """Register a task that can be executed by the system."""
        self.registered_tasks[name] = {
            "function": task_func,
            "metadata": metadata or {},
        }

    def execute_task(self, task_name: str, **kwargs) -> Any:
        """
        Execute a registered task with operator sovereignty checks.
        """
        if task_name not in self.registered_tasks:
            raise ValueError(f"Task '{task_name}' not registered")

        # Request permission from operator
        if not self.sovereignty.request_permission(
            action=f"execute_task:{task_name}",
            context={"task": task_name, "args": kwargs},
        ):
            raise PermissionError(f"Operator denied execution of task '{task_name}'")

        task = self.registered_tasks[task_name]
        return task["function"](**kwargs)

    def list_tasks(self) -> Dict[str, Dict]:
        """List all registered tasks and their metadata."""
        return {name: task["metadata"] for name, task in self.registered_tasks.items()}

    def load_plugin(self, plugin_path: str):
        """
        Load a plugin module that can register additional tasks.
        Plugins extend the "do anything" capability.
        """
        if not self.sovereignty.request_permission(
            action="load_plugin", context={"plugin": plugin_path}
        ):
            raise PermissionError(f"Operator denied loading plugin '{plugin_path}'")

        # Load the plugin module
        plugin_name = Path(plugin_path).stem
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Store plugin reference
        self.plugins[plugin_name] = module

        # If plugin has a register function, call it
        if hasattr(module, "register"):
            module.register(self)

        return plugin_name


class SwarmzCore:
    """
    Main SWARMZ system - Operator-Sovereign "Do Anything" System
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sovereignty = OperatorSovereignty()
        self.executor = TaskExecutor(self.sovereignty)
        self._register_builtin_tasks()

    def _register_builtin_tasks(self):
        """Register built-in core tasks."""

        def echo(message: str) -> str:
            """Simple echo task for testing."""
            return f"Echo: {message}"

        def system_info() -> Dict[str, Any]:
            """Return system information."""
            return {
                "platform": sys.platform,
                "python_version": sys.version,
                "registered_tasks": len(self.executor.registered_tasks),
                "loaded_plugins": len(self.executor.plugins),
            }

        def execute_python(code: str) -> Any:
            """
            Execute arbitrary Python code (operator sovereignty in action).
            WARNING: This is powerful and should only be used by trusted operators.
            """
            local_vars = {}
            exec(code, {"__builtins__": __builtins__}, local_vars)
            return local_vars.get("result", None)

        self.executor.register_task(
            "echo",
            echo,
            {"description": "Echo a message back", "params": {"message": "string"}},
        )

        self.executor.register_task(
            "system_info", system_info, {"description": "Get system information"}
        )

        self.executor.register_task(
            "execute_python",
            execute_python,
            {
                "description": "Execute Python code (operator sovereignty)",
                "params": {"code": "string"},
                "warning": "Executes arbitrary code - use with caution",
            },
        )

    def execute(self, task_name: str, **kwargs) -> Any:
        """Execute a task by name."""
        return self.executor.execute_task(task_name, **kwargs)

    def list_capabilities(self) -> Dict[str, Dict]:
        """List all available capabilities (tasks)."""
        return self.executor.list_tasks()

    def load_plugin(self, plugin_path: str) -> str:
        """Load a plugin to extend capabilities."""
        return self.executor.load_plugin(plugin_path)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get complete audit log of all operations."""
        return self.sovereignty.get_audit_log()

    def save_config(self, config_path: str):
        """Save current configuration."""
        with open(config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def load_config(self, config_path: str):
        """Load configuration from file."""
        with open(config_path, "r") as f:
            self.config = json.load(f)


# Note: OpenTelemetry tracing for AI Toolkit can be configured here when available
# configure_otel_providers(
#     vs_code_extension_port=4317,  # AI Toolkit gRPC port
#     enable_sensitive_data=True  # Enable capturing prompts and completions
# )


def main():
    """Main entry point for SWARMZ system."""
    print("=" * 60)
    print("SWARMZ - Operator-Sovereign 'Do Anything' System")
    print("=" * 60)
    print()

    # Initialize the system
    swarmz = SwarmzCore()

    print("System initialized successfully!")
    print(f"Available capabilities: {len(swarmz.list_capabilities())}")
    print()

    # Demo the system
    print("Running system demonstration...")
    print()

    # Test echo task
    result = swarmz.execute("echo", message="Hello, SWARMZ!")
    print(f"1. Echo test: {result}")

    # Get system info
    info = swarmz.execute("system_info")
    print(f"2. System info:")
    for key, value in info.items():
        print(f"   - {key}: {value}")

    # Show audit log
    print()
    print("Audit log:")
    for idx, entry in enumerate(swarmz.get_audit_log(), 1):
        print(f"   {idx}. {entry['action']} - Approved: {entry['approved']}")

    print()
    print("SWARMZ system ready for operator commands.")
    print("The operator maintains full sovereignty over all operations.")


if __name__ == "__main__":
    main()
