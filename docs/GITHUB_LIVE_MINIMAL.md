# NEXUSMON GitHub Minimal Live Guide

## Frontend (where it is)
- Main web UI: [web_ui/index.html](web_ui/index.html)
- UI logic: [web_ui/app.js](web_ui/app.js)
- UI styles: [web_ui/styles.css](web_ui/styles.css)
- PWA worker: [web_ui/sw.js](web_ui/sw.js)

## Server + runtime entrypoints
- Launcher: [run_server.py](run_server.py)
- FastAPI app: [nexusmon_runtime/api/server.py](nexusmon_runtime/api/server.py)
- API docs at runtime: `/docs`

## API surfaces (what each does)
- Core missions/system/admin/meta/factory: [nexusmon_runtime/api/server.py](nexusmon_runtime/api/server.py)
- Operational pipeline (blueprint -> offer -> checkout -> fulfillment -> ledger): [nexusmon_runtime/api/operational_routes.py](nexusmon_runtime/api/operational_routes.py)
- Operator OS + Artifact Vault + Identity: [nexusmon_runtime/api/operator_ecosystem_routes.py](nexusmon_runtime/api/operator_ecosystem_routes.py)
- Federation mode: [nexusmon_runtime/api/federation_routes.py](nexusmon_runtime/api/federation_routes.py)
- Charter + Prime Directive: [nexusmon_runtime/api/charter_routes.py](nexusmon_runtime/api/charter_routes.py)
- Fusion provenance registry: [nexusmon_runtime/api/fusion_routes.py](nexusmon_runtime/api/fusion_routes.py)

## Live run (desktop + phone)
1. `python run_server.py`
2. Desktop: open `http://127.0.0.1:8012/`
3. Phone (same Wi-Fi): open the LAN URL printed by server startup (e.g. `http://192.168.x.x:8012/`)

## Build + test status gates
- Tests: `python -W error -m pytest tests/ -q`
- Package: `python -m build`

## Copyright and license
- Canonical license: [LICENSE](LICENSE)
- Source headers enforce source-available restrictions.
- Repository docs and runtime should reference the same license text to avoid drift.

## Product positioning (minimal truth)
- NEXUSMON is production-capable for operator-governed automation and orchestration.
- It is not equivalent to frontier foundation-model scale (e.g., xAI/Grok/OpenAI) by default.
- It can become highly competitive in your target domain through focused tooling, data, and operator workflows.

