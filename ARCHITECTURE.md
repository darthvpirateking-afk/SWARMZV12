# SWARMZ Architecture

## System Overview

SWARMZ is built as an Operator-Sovereign "do anything" system with three core layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Operator Interface                    │
│  (CLI, Interactive Mode, Python API, Configuration)     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                     Core System Layer                    │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  SwarmzCore │  │TaskExecutor  │  │OperatorSov.   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Capability Layer                       │
│  ┌───────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ Built-in  │  │ Plugins  │  │  Future Extensions │   │
│  │  Tasks    │  │ (Dynamic)│  │   (Unlimited)      │   │
│  └───────────┘  └──────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. OperatorSovereignty

**Purpose**: Enforce operator control over all operations

**Key Features**:
- Permission request system
- Audit logging
- Override capability
- Transparency

**Implementation**:
```python
class OperatorSovereignty:
    - request_permission(action, context) -> bool
    - get_audit_log() -> List[Dict]
    - override_enabled: bool
    - audit_log: List[Dict]
```

### 2. TaskExecutor

**Purpose**: Execute tasks and manage plugins

**Key Features**:
- Task registration
- Task execution with sovereignty checks
- Plugin loading
- Task listing

**Implementation**:
```python
class TaskExecutor:
    - register_task(name, func, metadata)
    - execute_task(name, **kwargs) -> Any
    - load_plugin(path) -> str
    - list_tasks() -> Dict
    - registered_tasks: Dict
    - plugins: Dict
```

### 3. SwarmzCore

**Purpose**: Main system coordinator

**Key Features**:
- System initialization
- Built-in task registration
- Unified interface
- Configuration management

**Implementation**:
```python
class SwarmzCore:
    - execute(task_name, **kwargs) -> Any
    - list_capabilities() -> Dict
    - load_plugin(path) -> str
    - get_audit_log() -> List
    - save_config(path)
    - load_config(path)
```

## Data Flow

### Task Execution Flow

```
User Request
     ↓
SwarmzCore.execute()
     ↓
TaskExecutor.execute_task()
     ↓
OperatorSovereignty.request_permission()
     ↓
[Permission Granted]
     ↓
Task Function Execution
     ↓
Result + Audit Log Entry
     ↓
Return to User
```

### Plugin Loading Flow

```
Load Plugin Request
     ↓
OperatorSovereignty.request_permission()
     ↓
TaskExecutor.load_plugin()
     ↓
Import Plugin Module
     ↓
Call plugin.register(executor)
     ↓
Plugin Registers Tasks
     ↓
Tasks Available for Execution
```

## Plugin System Architecture

### Plugin Structure

```python
# plugins/example.py

def register(executor):
    """
    Called by TaskExecutor when plugin is loaded.
    
    Args:
        executor: TaskExecutor instance to register tasks with
    """
    
    def my_task(param1, param2):
        """Task implementation."""
        # Do work
        return result
    
    executor.register_task("task_name", my_task, {
        "description": "What the task does",
        "params": {"param1": "type", "param2": "type"},
        "category": "plugin_category"
    })
```

### Built-in Plugins

1. **filesystem.py** - File system operations
   - fs_list, fs_read, fs_write, fs_mkdir, fs_info

2. **dataprocessing.py** - Data manipulation
   - JSON parsing/stringifying, hashing, transformations, encoding

## Operator Sovereignty Implementation

### Permission System

Every action goes through sovereignty checks:

```python
def execute_task(self, task_name, **kwargs):
    # Request permission
    if not self.sovereignty.request_permission(
        action=f"execute_task:{task_name}",
        context={"task": task_name, "args": kwargs}
    ):
        raise PermissionError("Operator denied execution")
    
    # Execute task
    return task["function"](**kwargs)
```

### Audit Trail

All operations are logged:

```python
self.audit_log.append({
    "action": action,
    "context": context,
    "approved": True,
    "timestamp": datetime.now()  # (simplified)
})
```

### Override Capability

Operators can override any restriction through:
- Configuration settings
- Direct code modification (operator sovereignty)
- Plugin customization

## "Do Anything" Capability

SWARMZ achieves "do anything" through:

### 1. Arbitrary Code Execution

Built-in `execute_python` task:
```python
def execute_python(code: str) -> Any:
    local_vars = {}
    exec(code, {"__builtins__": __builtins__}, local_vars)
    return local_vars.get("result", None)
```

### 2. Unlimited Extensibility

Plugin system allows:
- Any Python functionality
- External library integration
- Custom business logic
- No artificial restrictions

### 3. Dynamic Loading

Plugins loaded at runtime:
- No recompilation needed
- Immediate availability
- Operator-controlled

### 4. Complete Control

Operator can:
- Execute any Python code
- Load any plugin
- Override any restriction
- Modify the system itself

## Interface Layer

### 1. Command-Line Interface (CLI)

```bash
# Direct task execution
swarmz_cli.py --task <name> --params <json>

# Plugin loading
swarmz_cli.py --load-plugin <path>

# List capabilities
swarmz_cli.py --list

# Audit trail
swarmz_cli.py --audit
```

### 2. Interactive Mode

```bash
swarmz_cli.py --interactive
swarmz> list
swarmz> task echo {"message": "Hello"}
swarmz> audit
swarmz> exit
```

### 3. Python API

```python
from swarmz import SwarmzCore

swarmz = SwarmzCore(config)
result = swarmz.execute("task_name", param=value)
```

### 4. Configuration File

```json
{
  "system_name": "SWARMZ",
  "operator_sovereignty": {
    "enabled": true,
    "auto_approve": true
  },
  "plugins": {
    "auto_load": ["plugins/filesystem.py"]
  }
}
```

## Security Model

### Trust Model

SWARMZ operates on a **trusted operator model**:
- Operators are trusted completely
- No restrictions on capabilities
- Transparency through audit logs
- Operator responsibility for actions

### Design Philosophy

1. **Empowerment over Restriction**
   - Give operators tools, not limits
   - Trust in operator judgment
   - Provide information, not barriers

2. **Transparency over Obfuscation**
   - All actions logged
   - Clear audit trail
   - Visible decision making

3. **Flexibility over Rigidity**
   - "Do anything" philosophy
   - No artificial constraints
   - Operator-defined boundaries

## Extensibility Points

### 1. Custom Plugins

Create new capabilities:
```
plugins/
  └── my_plugin.py
```

### 2. Built-in Tasks

Add to core system:
```python
def _register_builtin_tasks(self):
    # Add new built-in task
    self.executor.register_task("new_task", func, metadata)
```

### 3. Configuration

Extend config.json:
```json
{
  "custom_settings": {
    "key": "value"
  }
}
```

### 4. Interfaces

Add new interfaces:
- Web interface
- REST API
- GUI
- Integration with other tools

## Performance Considerations

### Efficient Design

1. **Lazy Loading**: Plugins loaded on demand
2. **Minimal Overhead**: Direct function calls
3. **No Compilation**: Pure Python, interpreted
4. **Scalable**: Add capabilities without performance impact

### Optimization Opportunities

1. Task caching
2. Plugin preloading
3. Async execution
4. Parallel task processing

## Future Extensions

SWARMZ is designed for unlimited extension:

1. **Network Capabilities**: HTTP, websockets, APIs
2. **Database Integration**: SQL, NoSQL, ORM
3. **Cloud Services**: AWS, Azure, GCP integration
4. **AI/ML**: Model integration, data processing
5. **DevOps**: CI/CD, deployment, monitoring
6. **Security**: Encryption, authentication, authorization
7. **Monitoring**: Metrics, logging, alerting
8. **Workflow**: Task chaining, scheduling, automation

## Summary

SWARMZ architecture is built on three principles:

1. **Operator Sovereignty** - Complete operator control
2. **Unlimited Extensibility** - "Do anything" capability
3. **Full Transparency** - Complete visibility

This creates a system that:
- Trusts the operator completely
- Provides unlimited capabilities
- Maintains full transparency
- Scales infinitely through plugins
- Remains simple and maintainable

**The operator is always in control. SWARMZ is the tool.**
