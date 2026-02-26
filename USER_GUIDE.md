# NEXUSMON User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Plugin Development](#plugin-development)
6. [Best Practices](#best-practices)

## Introduction

NEXUSMON is an Operator-Sovereign "Do Anything" System that gives you complete control over system operations through a flexible, extensible architecture.

### What Makes NEXUSMON Different?

- **Operator Sovereignty**: You're always in control
- **No Artificial Limits**: "Do anything" philosophy
- **Full Transparency**: Complete audit trail
- **Unlimited Extensibility**: Plugin system for any capability

## Core Concepts

### Operator Sovereignty

Every action in NEXUSMON goes through the operator sovereignty system:
- Actions are logged in an audit trail
- Operator can override any restriction
- Complete transparency of operations

### Task Execution

Tasks are the fundamental units of work in NEXUSMON:
- Registered with the system
- Executed on demand
- Can be built-in or from plugins

### Plugin System

Plugins extend NEXUSMON capabilities:
- Python modules with a `register()` function
- Can add any number of tasks
- Loaded dynamically at runtime

## Basic Usage

### Running Tasks

**Command Line:**
```bash
python3 nexusmon_cli.py --task echo --params '{"message": "Hello"}'
```

**Python API:**
```python
from nexusmon import NexusmonCore

nexusmon = NexusmonCore()
result = nexusmon.execute("echo", message="Hello")
```

### Interactive Mode

```bash
python3 nexusmon_cli.py --interactive
```

Commands:
- `list` - Show all capabilities
- `task <name> [params]` - Execute a task
- `load <plugin>` - Load a plugin
- `audit` - View audit log
- `exit` - Quit

### Loading Plugins

**Command Line:**
```bash
python3 nexusmon_cli.py --load-plugin plugins/filesystem.py --list
```

**Python API:**
```python
nexusmon.load_plugin("plugins/filesystem.py")
```

## Advanced Features

### Arbitrary Code Execution

NEXUSMON allows trusted operators to execute arbitrary Python code:

```bash
python3 nexusmon_cli.py --task execute_python --params '{"code": "result = 10 * 5"}'
```

This demonstrates true operator sovereignty.

### Audit Trail

View all operations:

```bash
python3 nexusmon_cli.py --audit
```

Or in Python:
```python
audit_log = nexusmon.get_audit_log()
for entry in audit_log:
    print(f"{entry['action']}: {entry['approved']}")
```

### Configuration

Create `config.json`:
```json
{
  "system_name": "NEXUSMON",
  "operator_sovereignty": {
    "enabled": true,
    "auto_approve": true,
    "audit_enabled": true
  },
  "plugins": {
    "auto_load": ["plugins/filesystem.py"]
  }
}
```

Load it:
```bash
python3 nexusmon_cli.py --config config.json
```

## Plugin Development

### Basic Plugin Structure

Create `plugins/myplugin.py`:

```python
def register(executor):
    """Register tasks with the executor."""
    
    def my_task(param1, param2):
        """Task implementation."""
        return f"Result: {param1} + {param2}"
    
    executor.register_task("my_task", my_task, {
        "description": "Description of my task",
        "params": {"param1": "string", "param2": "string"},
        "category": "custom"
    })
```

### Plugin Best Practices

1. **Clear Naming**: Use descriptive task names
2. **Documentation**: Add good descriptions and metadata
3. **Categories**: Group related tasks
4. **Error Handling**: Handle errors gracefully
5. **Dependencies**: Document any required libraries

### Example: Network Plugin

```python
# plugins/network.py
import requests

def register(executor):
    def http_get(url):
        """Fetch content from URL."""
        response = requests.get(url)
        return {
            "status_code": response.status_code,
            "content": response.text[:1000]  # First 1000 chars
        }
    
    executor.register_task("http_get", http_get, {
        "description": "HTTP GET request",
        "params": {"url": "string"},
        "category": "network"
    })
```

## Built-in Capabilities

### Core Tasks

- **echo**: Echo a message back
- **system_info**: Get system information
- **execute_python**: Execute arbitrary Python code

### Filesystem Plugin

- **fs_list**: List directory contents
- **fs_read**: Read file contents
- **fs_write**: Write to file
- **fs_mkdir**: Create directory
- **fs_info**: Get file information

### Data Processing Plugin

- **data_json_parse**: Parse JSON
- **data_json_stringify**: Convert to JSON
- **data_hash**: Generate hash
- **data_transform**: Transform data
- **data_encode**: Encode/decode text

## Best Practices

### Security

1. **Trust**: NEXUSMON is designed for trusted operators
2. **Code Execution**: Use `execute_python` carefully
3. **Plugin Sources**: Only load plugins from trusted sources
4. **Audit**: Regularly review audit logs

### Performance

1. **Plugin Loading**: Load plugins once at startup
2. **Task Design**: Keep tasks focused and efficient
3. **Error Handling**: Handle errors to prevent crashes

### Organization

1. **Plugin Categories**: Organize tasks by category
2. **Naming Conventions**: Use consistent naming
3. **Documentation**: Document all custom tasks
4. **Version Control**: Track plugin changes

## Examples

See `examples.py` for comprehensive examples:

```bash
python3 examples.py
```

## Troubleshooting

### Plugin Won't Load

- Check file path is correct
- Ensure plugin has `register()` function
- Check for syntax errors in plugin

### Task Execution Fails

- Verify task name is correct
- Check required parameters
- Review audit log for details

### Import Errors

- Ensure you're in the correct directory
- Check Python path includes NEXUSMON directory

## Support

For issues and questions:
- Check the examples in `examples.py`
- Review the test suite in `test_nexusmon.py`
- Read the source code (it's well documented)

## Philosophy

Remember: NEXUSMON embodies operator sovereignty. You have complete control. The system trusts you to make the right decisions. Use this power responsibly.


