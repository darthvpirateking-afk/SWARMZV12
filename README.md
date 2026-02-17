# SWARMZ - Operator-Sovereign "Do Anything" System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**SWARMZ** is an **Operator-Sovereign "Do Anything" System** - a flexible, extensible framework that empowers operators with complete control and sovereignty over all system operations.

### Core Principles

1. **Operator Sovereignty** - The operator maintains ultimate authority over all operations
2. **Extensibility** - Easy to add new capabilities through a plugin system
3. **Transparency** - All actions are logged and auditable
4. **Flexibility** - "Do anything" philosophy with unlimited extensibility
5. **Safety** - Built-in safeguards with operator override capability

## Features

- 🎯 **Task Execution Engine** - Execute any registered task with full control
- 🔌 **Plugin System** - Extend capabilities dynamically
- 📝 **Audit Logging** - Complete transparency of all operations
- 🛡️ **Operator Sovereignty** - You're always in control
- 🔧 **Built-in Tasks** - Core functionality out of the box
- 💻 **CLI Interface** - Command-line and interactive modes
- 🌐 **Web Server & REST API** - FastAPI-based API with OpenAPI docs
- 📱 **Progressive Web App** - Mobile-friendly PWA with offline support
- 🚀 **Cross-Platform** - Windows, Linux, macOS, and Android (Termux)
- 📦 **Easy Configuration** - JSON-based configuration

## Quick Start

### Web Server (Recommended)

```bash
# Windows: Double-click SWARMZ_UP.ps1 or SWARMZ_UP.cmd
# Or manually:
pip install -r requirements.txt
python run_server.py

# Access at:
# Local:  http://localhost:8012
# LAN:    http://192.168.x.x:8012 (shown on startup)
# API Docs: http://localhost:8012/docs
```

### Phone / LAN Access

1. Start the server with `SWARMZ_UP.ps1` (or `python run_server.py`).
2. Note the **LAN** URL printed at startup (e.g. `http://192.168.1.42:8012`).
3. Open that URL on any phone or tablet connected to the **same Wi-Fi**.
4. If blocked, allow **TCP port 8012** through your firewall:
   ```powershell
   # PowerShell (run as Admin once)
   New-NetFirewallRule -DisplayName "SWARMZ" -Direction Inbound -LocalPort 8012 -Protocol TCP -Action Allow
   ```
5. The HUD is a PWA — tap **"Add to Home Screen"** for native-app feel.

### Two Modes: COMPANION and BUILD

SWARMZ operates in two modes, toggled from the HUD header tabs:

| Mode | Purpose |
|------|---------|
| **COMPANION** | Conversational interface — ask questions, get status, request help. |
| **BUILD** | Mission dispatch — define an intent + spec, dispatch to the swarm runner. |

Mode persists across restarts in `data/state.json`.

### Swarm Runner

`run_server.py` starts a background **swarm runner** thread that:

- Ticks every 1 second looking for `PENDING` missions.
- Marks mission `RUNNING` → executes a worker → writes `packs/<id>/result.json`.
- Updates mission status to `SUCCESS` or `FAILURE`.
- Writes a heartbeat to `data/runner_heartbeat.json` (check via `GET /v1/swarm/status`).

### Smoke Test

After starting the server, verify the full dispatch→run→success flow:

```powershell
# PowerShell
.\SWARMZ_SMOKE_TEST.ps1

# Or CMD
SWARMZ_SMOKE_TEST.cmd
```

All 7 steps should pass: health, runner up, mode switch, dispatch, wait, confirm SUCCESS, result.json exists.

### CLI Usage

```bash
# Run the demo
python3 swarmz.py

# List all capabilities
python3 swarmz_cli.py --list

# Execute a task
python3 swarmz_cli.py --task echo --params '{"message": "Hello, SWARMZ!"}'

# Start interactive mode
python3 swarmz_cli.py --interactive
```

### Interactive Mode

```bash
$ python3 swarmz_cli.py --interactive
swarmz> list
  • echo                 - Echo a message back
  • system_info          - Get system information
  • execute_python       - Execute Python code (operator sovereignty)

swarmz> task echo {"message": "Hello!"}
✓ Result: Echo: Hello!

swarmz> audit
1. execute_task:echo - True

swarmz> exit
```

## Architecture

### Core Components

1. **SwarmzCore** - Main system coordinator
2. **OperatorSovereignty** - Ensures operator control and maintains audit logs
3. **TaskExecutor** - Executes registered tasks and manages plugins
4. **Plugin System** - Extends capabilities dynamically

### Plugin System

Plugins are Python modules that register new tasks with the system:

```python
# plugins/example.py
def register(executor):
    def my_task(param1, param2):
        return f"Processed {param1} and {param2}"
    
    executor.register_task("my_task", my_task, {
        "description": "Example task",
        "params": {"param1": "string", "param2": "string"}
    })
```

Load plugins:
```bash
python3 swarmz_cli.py --load-plugin plugins/example.py --task my_task --params '{"param1": "A", "param2": "B"}'
```

## Built-in Capabilities

### Core Tasks
- **echo** - Echo a message back
- **system_info** - Get system information
- **execute_python** - Execute arbitrary Python code (operator sovereignty)

### File System Plugin (`plugins/filesystem.py`)
- **fs_list** - List directory contents
- **fs_read** - Read file contents
- **fs_write** - Write content to file
- **fs_mkdir** - Create a directory
- **fs_info** - Get file information

### Data Processing Plugin (`plugins/dataprocessing.py`)
- **data_json_parse** - Parse JSON string
- **data_json_stringify** - Convert object to JSON
- **data_hash** - Generate hash of string
- **data_transform** - Transform data collection
- **data_encode** - Encode or decode text

## Configuration

Create a `config.json` file:

```json
{
  "system_name": "SWARMZ",
  "operator_sovereignty": {
    "enabled": true,
    "auto_approve": true,
    "audit_enabled": true
  },
  "plugins": {
    "auto_load": [
      "plugins/filesystem.py",
      "plugins/dataprocessing.py"
    ]
  }
}
```

Use configuration:
```bash
python3 swarmz_cli.py --config config.json --list
```

## Advanced Usage

### Python API

```python
from swarmz import SwarmzCore

# Initialize system
swarmz = SwarmzCore()

# Execute tasks
result = swarmz.execute("echo", message="Hello!")
info = swarmz.execute("system_info")

# Load plugins
swarmz.load_plugin("plugins/filesystem.py")

# List capabilities
capabilities = swarmz.list_capabilities()

# Get audit log
audit = swarmz.get_audit_log()
```

### Creating Custom Plugins

1. Create a Python file in the `plugins/` directory
2. Implement a `register(executor)` function
3. Register your tasks using `executor.register_task()`
4. Load the plugin via CLI or API

Example:
```python
# plugins/network.py
import requests

def register(executor):
    def http_get(url):
        response = requests.get(url)
        return response.text
    
    executor.register_task("http_get", http_get, {
        "description": "Fetch content from URL",
        "params": {"url": "string"},
        "category": "network"
    })
```

## Operator Sovereignty in Action

SWARMZ embodies operator sovereignty through:

1. **Permission System** - All actions go through sovereignty checks
2. **Audit Trail** - Complete log of all operations
3. **Override Capability** - Operator can override any restriction
4. **Code Execution** - Trusted operators can execute arbitrary code
5. **Plugin Control** - Operator decides what capabilities to load

### Example: Arbitrary Code Execution

```bash
python3 swarmz_cli.py --task execute_python --params '{"code": "result = 2 + 2"}'
```

This demonstrates true operator sovereignty - the system trusts the operator completely.

## Security Considerations

- **Operator Trust** - The system is designed for trusted operators
- **Code Execution** - `execute_python` task allows arbitrary code execution
- **Plugin Loading** - Plugins have full system access
- **Audit Logging** - All actions are logged for accountability

## Use Cases

- **Automation** - Automate any task through the plugin system
- **DevOps** - System administration and management
- **Data Processing** - Transform and manipulate data
- **Prototyping** - Quickly add capabilities as needed
- **Personal Tools** - Build your own operator-controlled toolset

## Philosophy

SWARMZ is built on the principle that **the operator knows best**. Rather than restricting what can be done, SWARMZ empowers operators with complete control while maintaining transparency through audit logs.

The "do anything" capability comes from:
- Unlimited extensibility through plugins
- Built-in arbitrary code execution for trusted operators
- No artificial restrictions on capabilities
- Complete operator sovereignty over all operations

## Requirements

### Core System
- Python 3.6+
- No external dependencies for core functionality (swarmz.py, swarmz_cli.py)

### Web Server & PWA
- FastAPI and Uvicorn (install with: `pip install -r requirements.txt`)
- Modern web browser for PWA features

### Development
- PyInstaller for building executables
- pytest for testing (install with: `pip install -r requirements-dev.txt`)

## Deployment Options

### Windows
- **RUN.cmd** - Double-click to auto-setup and start (Command Prompt)
- **RUN.ps1** - Double-click to auto-setup and start (PowerShell)
- **PACK_EXE.ps1** - Build standalone .exe with PyInstaller

### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python swarmz_server.py
```

### Android (Termux)
```bash
# One-time setup
./termux_setup.sh

# Start server
./termux_run.sh
```

### Progressive Web App (PWA)
1. Start the server (any method above)
2. Open the LAN URL on your mobile device
3. Tap "Install" or "Add to Home Screen"
4. Access SWARMZ like a native app!

For detailed examples and usage, see **EXAMPLES.txt**.

## Contributing

To add new built-in tasks or plugins:

1. For core tasks: Edit `swarmz.py` and add to `_register_builtin_tasks()`
2. For plugins: Create a new file in `plugins/` directory
3. Follow the plugin registration pattern

## License

MIT License - See LICENSE file for details

## Project Status

SWARMZ is an operator-sovereign system designed for maximum flexibility and control. It is production-ready for trusted operator environments.

---

**Remember: With SWARMZ, the operator maintains complete sovereignty. You're in control.**
