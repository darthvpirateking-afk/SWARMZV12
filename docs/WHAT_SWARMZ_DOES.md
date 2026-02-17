# What SWARMZ Does

> Plain-English explanation. No jargon. Current as of schema_version 2.

---

## One-Sentence Summary

SWARMZ is a **local-first AI mission control system** that runs on your Windows PC,
lets you dispatch tasks through a REST API or web UI, and can connect to any external
service (email, Slack, sheets, etc.) through a Zapier bridge.

## How It Works

1. **You start the server** by double-clicking `SWARMZ_UP.cmd` (or running `SWARMZ_UP.ps1`).
2. A **FastAPI web server** starts on port 8012 and binds to `0.0.0.0`
   (all network interfaces).
3. You can access it from:
   - Your PC: `http://localhost:8012`
   - Your phone (same Wi-Fi): `http://<your-PC-LAN-IP>:8012`
4. The **web UI** shows dashboards for missions, activity, forensics, shell, and market lab.
5. The **REST API** lets you:
   - Create and manage missions (`/v1/missions`)
   - Dispatch sovereign tasks (`/v1/sovereign/dispatch`)
   - View system logs (`/v1/system/log`)
   - Chat with the companion AI (`/v1/companion/message`)
   - Send/receive data from Zapier (`/v1/zapier/inbound`, `/v1/zapier/emit`)

## What Each Piece Does

| Component | What It Does |
|-----------|-------------|
| `server.py` | Main entry. Layers control endpoints on top of the core API. |
| `swarmz_server.py` | Core FastAPI app with missions, auth, middleware. |
| `swarmz.py` | Core logic: task planning, execution, model calls. |
| `companion.py` | AI companion that reviews/assists with tasks. |
| `config/runtime.json` | All settings (port, models, integrations). |
| `data/` | Append-only storage (missions, audit, Zapier logs). |
| `web/` | HTML/CSS/JS for the browser UI. |
| `core/` | Module implementations (activity, awareness, forensics, shell, market lab, Zapier bridge). |
| `addons/` | Security, rate limiting, auth, budget tracking. |
| `plugins/` | Data processing, filesystem, reality gate. |
| `tools/` | Diagnostic tools (doctor, smoke tests, Zapier test). |

## Key Design Principles

- **Local-first**: Everything runs on your machine. No cloud required (unless you connect Zapier).
- **Additive-only**: New features add files; existing code is never deleted.
- **Fail-open**: If a module fails to load, the server still starts without it.
- **Append-only logs**: All data files are append-only JSONL. Nothing is ever overwritten.
- **No new dependencies**: All new code uses Python standard library only.

## Who Is It For?

Anyone who wants a **personal AI operations center** they fully control,
running on their own hardware, accessible from any device on their network.
