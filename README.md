
# SWARMZ - Operator-Sovereign "Do Anything" System

> 🟢 **Status: SHIP NOW** — All blocking criteria met. See [SWARMZ_RELEASE_READINESS.md](SWARMZ_RELEASE_READINESS.md).

**License:** Proprietary - All Rights Reserved (see `LICENSE`).

**Copyright:** Copyright (c) 2026 SWARMZ. No use, copying, modification, distribution, hosting, resale, or derivative works without explicit written permission.

## Overview

**SWARMZ** is an **Operator-Sovereign "Do Anything" System** - a flexible, extensible framework that empowers operators with complete control and sovereignty over all system operations.

## What SWARMZ Is

### Lore + Technical (Operator Definition)

#### THE LIVING ORGANISM
- A Partner (embodied intelligence, visible, evolving)
- A Shadow (tactical executor, high-risk, gated)
- A Swarm (4-6+ agents running missions)
- A Ledger (append-only truth spine)
- A NetGrid (your mission world)

#### THE RUNTIME
- Deterministic
- Snapshot-based
- Mission-driven
- Multi-agent
- Governed
- Auditable
- Extensible

#### THE PURPOSE
To run:
- automations
- product pipelines
- simulations
- code generation
- fulfillment
- learning loops
- evolution cycles

All under your control.

## SWARMZ Build Matrix v1.0

| Layer | What It Contains |
|---|---|
| 0. FOUNDATION | create_app(), Postgres, JSONL ledger, health/ready, logs, metrics, deterministic startup, object storage. |
| 1. AGENTS | Planner, Coder, Tester, Verifier, Formatter, Governance Agent, Memory Agent, Reflection Agent, optional Grok specialist node. |
| 2. ORCHESTRATOR | LangGraph 1.0.8 StateGraph, checkpoints, retries, idempotency, run history. |
| 3. MEMORY | Vector DB (Chroma), semantic recall, experience archive, nightly reflection loop. |
| 4. SAFETY | NIST RMF, OECD Due Diligence, AUS 8 Principles, Governance Agent scoring, human-in-loop, policy engine. |
| 5. BLUEPRINTS | Registry, versions, artifacts, validations, approvals. |
| 6. STORE | Offers, SKUs, listings, checkout, payment webhook, cart, catalog. |
| 7. FULFILLMENT | Digital delivery + 1 physical provider, tracking, jobs. |
| 8. LEDGER | Revenue, COGS, fees, credits, withdrawals, optional token bridge. |
| 9. AUTONOMY | Sensors, policy engine, learning loop, reproduction rules, KPI-based evolution. |

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

## Runtime Boundary

- `apps/gate-link` is an isolated game project for separate Play Store packaging.
- Core SWARMZ backend/runtime builds and deploys do not load or bundle `apps/gate-link`.
- Keep game release pipeline separate from SWARMZ runtime release pipeline.

## Quick Start

### NEXUSMON Space Pivot (Week 1)

Moon transit worker runbook:
- [docs/NEXUSMON_SPACE_WEEK1_RUNBOOK.md](docs/NEXUSMON_SPACE_WEEK1_RUNBOOK.md)

Optional dependency for high-fidelity orbit math:

```powershell
pip install -r requirements-space.txt
```

## Ship Now Status (2026-02-23)

- **Go** for normal development release (core API/UI/mission-path regression coverage is green).
- Latest full suite: **303 passed, 3 skipped**.
- Browser parity smoke (`/` + `/console`): **2 passed**.
- Full release readiness and deferred live-infra items: [SWARMZ_RELEASE_READINESS.md](SWARMZ_RELEASE_READINESS.md).

Quick verification commands:

```powershell
python -m pytest tests/ -v --tb=short
python -m pytest tests/test_dashboard_browser_smoke.py -v --tb=short
```

### Fastest Windows Start (Canonical)

```powershell
# 1) Start SWARMZ
./RUN.ps1

# 2) Open UI
# http://localhost:8012

# 3) Create desktop app icon shortcut (one-time)
./CREATE_SWARMZ_APP_ICON.ps1
```

Then double-click the `SWARMZ` icon on your desktop.

### Phone Mode (Same Wi-Fi)

```powershell
# One-click phone-ready launcher
./PHONE_MODE.ps1

# Or double-click PHONE_MODE.cmd
```

Then open the printed LAN URL on your phone (example: `http://192.168.x.x:8012/`).

### Web Server (Recommended)

```bash
# Windows: Double-click RUN.cmd or RUN.ps1
# Or manually:
pip install -r requirements.txt
python run_server.py

# Access at:
# Local:  http://localhost:8000
# Local:  http://localhost:8012
# LAN:    http://192.168.x.x:8012 (shown on startup)
# API Docs: http://localhost:8012/docs
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

Render (recommended config):

- Build command: `pip install -r requirements.txt`
- Start command: `python run_server.py --host 0.0.0.0 --port $PORT`
- Health check path: `/v1/health`
- Required env vars for live model routing:
  - `OPENAI_API_KEY=<your key>` (if using OpenAI provider)
  - `ANTHROPIC_API_KEY=<your key>` (if using Anthropic provider)
  - `OFFLINE_MODE=false`
  - `MODEL_PROVIDER=openai` or `MODEL_PROVIDER=anthropic`
- Optional env vars:
  - `SWARMZ_MODEL=gpt-4.1` (or your allowed model)
  - `OPENAI_BASE_URL=https://api.openai.com/v1`

Post-deploy verification:

```bash
python tools/render_post_deploy_check.py --base https://swarmzV10-.onrender.com
```

Project Position

This repository provides a controllable execution runtime.
It is a tool, not a platform service.

Behavior is defined by the operator and loaded modules.

Notice

The system executes exactly what it is instructed to execute.
Responsibility for usage and exposure rests with the operator.
