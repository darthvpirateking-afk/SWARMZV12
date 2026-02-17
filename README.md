SWARMZ — Local Operator Task Runtime
Summary

SWARMZ is a locally controlled task runtime designed for direct operator control over system actions.

The project provides a programmable execution environment where capabilities are added as modules and invoked through a consistent interface (CLI, API, or local web UI).

This repository is intended for controlled environments where the system owner defines behavior and trust boundaries.

Design Goals

Direct control over execution

Expandable capability surface through modules

Deterministic behavior (no remote dependencies required)

Observable execution via audit records

Minimal assumptions about allowed actions

This is not a sandboxed platform and is not designed for hostile environments.

Functional Components
Task Runtime

Registers callable actions and executes them with structured parameters.

Module Loader

Loads additional capabilities at runtime via Python modules.

Audit Log

Records each invocation and result status.

Interfaces

CLI

REST API

Local Web UI (PWA capable)

What It Does

Runs registered tasks

Adds capabilities dynamically

Tracks what was executed

Allows the operator to define behavior

What it does not do:

Enforce policy frameworks

Restrict trusted users

Provide multi-tenant isolation

Quick Start
Run Server
pip install -r requirements.txt
python3 swarmz_server.py


Access locally:

http://localhost:8000
http://localhost:8000/docs

CLI Examples

List available actions:

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
