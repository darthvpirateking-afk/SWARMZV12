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
# Windows: Double-click RUN.cmd or RUN.ps1
# Or manually:
pip install -r requirements.txt
python run_server.py

# Access at:
# Local:  http://localhost:8000
# LAN:    http://192.168.x.x:8000 (shown on startup)
# API Docs: http://localhost:8000/docs
```

### CLI Usage

```bash
# Run the demo
python3 swarmz.py

# List all capabilities
python3 swarmz_cli.py --list


Execute:

python3 swarmz_cli.py --task echo --params '{"message":"hello"}'


Interactive:

python3 swarmz_cli.py --interactive

Module System

Modules register tasks into the runtime.

Example:

def register(executor):

    def my_task(a, b):
        return f"{a}-{b}"

    executor.register_task(
        "my_task",
        my_task,
        {"description": "example"}
    )


Load:

python3 swarmz_cli.py --load-plugin plugins/example.py

Included Capabilities

Core:

echo

system_info

execute_python

Filesystem module:

list

read

write

mkdir

info

Data module:

json parse/stringify

hashing

transforms

encoding

Configuration

config.json

{
  "audit_enabled": true,
  "auto_load": [
    "plugins/filesystem.py",
    "plugins/dataprocessing.py"
  ]
}

Python Usage
from swarmz import SwarmzCore

swarmz = SwarmzCore()

swarmz.execute("echo", message="hi")
swarmz.load_plugin("plugins/filesystem.py")
swarmz.list_capabilities()
swarmz.get_audit_log()

Security Model

SWARMZ assumes a trusted operator.

Important implications:

Code execution is unrestricted

Modules have full local access

No isolation boundary exists

Audit exists for traceability, not prevention

Do not expose directly to untrusted users.

Intended Uses

Personal automation runtime

Local admin tooling

Data manipulation workspace

Rapid capability prototyping

Operator-controlled integrations

Requirements

Core:
Python 3.6+

Web UI:
FastAPI + Uvicorn

Deployment

Runs on:

Windows

Linux

macOS

Android (Termux)

Project Position

This repository provides a controllable execution runtime.
It is a tool, not a platform service.

Behavior is defined by the operator and loaded modules.

Notice

The system executes exactly what it is instructed to execute.
Responsibility for usage and exposure rests with the operator.
