# NEXUSMON Runnability Report

## Entrypoints
- Backend: FastAPI `server:app` started by `run_server.py` (reads `config/runtime.json` for `bind` + `port`).
- UI: static PWA under `web_ui/` served by backend at `/app`; runtime config exposed at `/config/runtime.json` for the UI.
- Config: `config/runtime.json` (apiBaseUrl, uiBaseUrl, bind, port, uiPort, offlineMode) is the single source of truth.
- Data: `data/` (missions.jsonl, audit.jsonl, operator_pin.txt, daemon.log, runtime ledgers).

## Start Commands
- PowerShell: `./NEXUSMON_UP.ps1` (reads runtime config, runs self_check, opens browser, starts server).
- CMD: `NEXUSMON_UP.cmd` (same as above).
- Manual: `python run_server.py --host <bind> --port <port>` (defaults come from runtime config).

## Verified Health + Dispatch
- Health: `GET http://127.0.0.1:8012/v1/health` → `{ ok: true, version: 0.0.0, data_dir: ..., ui_expected: http://localhost:8012/app, offline_mode: false }` (tested via Invoke-RestMethod).
- Dispatch (category must be one of coin|forge|library|sanctuary):
	- Command: `python -c "import json,urllib.request; data=json.dumps({'goal':'status check','category':'coin','constraints':{}}).encode(); req=urllib.request.Request('http://127.0.0.1:8012/v1/dispatch', data=data, headers={'Content-Type':'application/json','X-Operator-Key':'<PIN>'}); print(urllib.request.urlopen(req).read().decode())"`
	- Result (sample): `{ "created": {"mission_id": "16e318aa", ...}, "run": {"status": "completed", ...} }`
- Data writes: new lines appended to `data/missions.jsonl` and `data/audit.jsonl` after dispatch.

## Ports and URLs
- Local API: `http://127.0.0.1:8012`
- Local UI: `http://127.0.0.1:8012/app`
- LAN UI/API: `http://<LAN_IP>:8012` (server binds to `bind` from runtime config; default 0.0.0.0).

## What Works
- self_check + doctor pass (doctor warns about nested package roots and shadow dirs but continues).
- Runtime config is consumed by server, startup scripts, and UI.
- Health and dispatch verified; data directory is writable and records missions.
- PWA shell + service worker served from backend.

## Warnings / Notes
- Existing nested package roots and duplicated directories (mobile/mobile, nexusmon-mobile/nexusmon-mobile) are reported as WARN; keep using repo root as authoritative.
- doctor reports WARN when the server is not running (health unreachable); start the server to clear it.
- Category validation is strict; use coin/forge/library/sanctuary to avoid 500s.

## Test Suite Status (2026-02-17)
- **93 tests, 100% pass** (`python -m pytest tests/ -v`)
- End-to-end harness: `tests/test_e2e.py` — 34 tests covering core imports, engine wiring, orchestrator/Crew, companion, API endpoints, dispatch round-trip, addons/plugins, and UI assets.
- Master SWARM AI: `tests/test_master_ai.py` — simulation mode and live API mode.
- Engine tests: core safety, engines, observability, safe execution, config loader, context pack, companion master, AI audit, promotion path.

## Checklist Completion
| # | Task | Status |
|---|------|--------|
| 1 | Capture truth snapshot | DONE |
| 2 | Restore base UI if drift | DONE |
| 3 | Verify/fix launch scripts | DONE |
| 4 | Clean up dependencies | DONE |
| 5 | Add profiling toggles | DONE |
| 6 | Verify new layers | DONE |
| 7 | Implement Master SWARM AI | DONE |
| 8 | Add end-to-end test harness | DONE |
| 9 | Prepare final deliverables | DONE |

## Bug Fixed During Checklist
- `nexusmon_runtime/api/server.py` line 6: missing `timezone` import from `datetime` — added `from datetime import datetime, timezone`.

