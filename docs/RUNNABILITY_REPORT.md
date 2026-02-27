# NEXUSMON — Runnability Report

> Auto-generated context document. Describes what runs, what fails, and where
> the known edges are.

---

## Entry Points

| Script | Method | Status |
|--------|--------|--------|
| `NEXUSMON_UP.ps1` | PowerShell launcher (venv, deps, port check, uvicorn) | **WORKS** |
| `NEXUSMON_UP.cmd` | CMD launcher (same logic) | **WORKS** |
| `uvicorn server:app --host 0.0.0.0 --port 8012` | Direct uvicorn | **WORKS** |
| `run_nexusmon.py` | CLI launcher | **BROKEN** — imports `nexusmon_runtime.api.server` which doesn't match the actual layout. Use `server.py` instead. |

## What Runs

- **FastAPI app** via `server.py` → imports `app` from `nexusmon_server.py`, layers control endpoints
- **Port 8012**, bind `0.0.0.0` (configurable in `config/runtime.json`)
- **LAN access** confirmed — phone on same Wi-Fi can reach `http://<LAN_IP>:8012`
- **Modules loaded** (all fail-open):
  - Missions CRUD (`/v1/missions`)
  - Sovereign dispatch (`/v1/sovereign/dispatch`)
  - System log (`/v1/system/log`)
  - Companion (`/v1/companion/message`)
  - Build dispatch (`/v1/build/dispatch`)
  - Swarm status (`/v1/swarm/status`)
  - Awareness, Forensics, Shell, Market Lab (OS-layer modules)
  - Activity stream & viewer
  - Zapier bridge (`/v1/zapier/inbound`, `/v1/zapier/emit`)

## What Fails / Known Issues

| Issue | Impact | Workaround |
|-------|--------|------------|
| `run_nexusmon.py` imports `nexusmon_runtime.api.server` | Crashes on startup | Use `NEXUSMON_UP.ps1` or `uvicorn server:app` directly |
| Zapier `shared_secret` is placeholder | Security | Change in `config/runtime.json` |
| No HTTPS | LAN only, not internet-safe | Use ngrok/cloudflared for remote access |
| `nexusmon_runtime/` package incomplete | `run_nexusmon.py` broken | Does not affect `server.py` path |

## Dependencies

- Python 3.10+
- `fastapi>=0.115.0`
- `uvicorn[standard]>=0.32.0`
- `pyjwt>=2.9.0`
- No other external dependencies required (all addons use stdlib)

## Config

Single source of truth: **`config/runtime.json`**

```json
{
  "port": 8012,
  "bind": "0.0.0.0",
  "offlineMode": false,
  "schema_version": 2
}
```

## Data

All persistent data in **`data/`** — append-only JSONL files:
- `data/missions.jsonl` — mission records
- `data/audit.jsonl` — audit trail
- `data/zapier/inbound.jsonl` — Zapier inbound events
- `data/zapier/outbound.jsonl` — Zapier outbound events

