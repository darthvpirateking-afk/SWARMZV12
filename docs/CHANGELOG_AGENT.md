# SWARMZ — Agent Changelog

> Append-only log of all changes made by automated agents.  
> Each entry records WHAT changed, WHEN, and WHY.

---

## Session: 2025-02 — OS-Layer Modules

### Added
- `core/awareness_api.py` — Awareness module API (system metrics, alerts)
- `core/forensics_api.py` — Forensics module API (event timeline, evidence)
- `core/shell_api.py` — Shell module API (command execution, history)
- `core/market_lab_api.py` — Market La`b module API (strategies, backtesting)
- `web/app.css`, `web/app.js` — Core UI styling and logic
- `web/hologram.css`, `web/hologram.html`, `web/hologram.js` — Hologram dashboard
- `web/trials.css`, `web/trials.html`, `web/trials.js` — Trials/testing UI
- `web/market_lab.html` — Market Lab UI
- `web/shell.html` — Shell UI
- `web/activity_viewer.html` — Activity stream viewer
- Module registrations added to `server.py` (all fail-open)

---

## Session: 2025-02 — Zapier Bridge + Infrastructure

### Added
- `core/zapier_bridge.py` — Zapier Universal Connector Bridge
  - `POST /v1/zapier/inbound` — Zapier → SWARMZ mission creation
  - `POST /v1/zapier/emit` — SWARMZ → Zapier Catch Hook
  - In-memory dedupe (10-min TTL), append-only JSONL logging
  - stdlib-only (urllib.request for outbound)
- `data/zapier/inbound.jsonl` — Inbound event log (seed)
- `data/zapier/outbound.jsonl` — Outbound event log (seed)
- `tools/test_zapier_bridge.py` — Zapier bridge smoke test (3 steps)
- `tools/smoke/run_smoke.py` — Full 7-step smoke test runner
- `tools/doctor/doctor.py` — Enhanced diagnostic tool
- `docs/ZAPIER_BRIDGE.md` — Zapier bridge documentation with setup instructions
- `docs/RUNNABILITY_REPORT.md` — What runs, what fails, known issues
- `docs/WHAT_SWARMZ_DOES.md` — Plain-English system explanation
- `docs/QUICKSTART.md` — 5-minute setup guide with LAN + phone access
- `docs/SMOKE_TESTS.md` — Smoke test documentation
- `docs/UPGRADE_CONTRACT.md` — Invariants and versioning rules
- `docs/CHANGELOG_AGENT.md` — This file

### Modified
- `config/runtime.json` — Added `integrations.zapier` block, `schema_version: 2`
- `server.py` — Added Zapier bridge registration (fail-open)

### Known Issues Documented
- `run_swarmz.py` imports `swarmz_runtime.api.server` which doesn't exist → use `SWARMZ_UP.cmd` instead
- Zapier `shared_secret` is placeholder `"change-me-to-a-real-secret"` → operator must change
- No HTTPS → LAN only without tunnel

---

*To add a new entry: append a new section below with date, what changed, and why.*
