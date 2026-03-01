# NEXUSMON Runtime Guide

A practical reference for running, configuring, and extending the NEXUSMON runtime.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python run_nexusmon.py
```

Server listens on `http://127.0.0.1:8012` by default.
Interactive API docs available at `http://127.0.0.1:8012/docs`.

## Runtime Health Check

Validate the runtime and its telemetry wiring before use:

```bash
python tools/runtime_check.py
```

Machine-readable output:

```bash
python tools/runtime_check.py --json
```

## Core Modules

### Engine (`nexusmon_runtime/core/engine.py`)

Central execution engine. Provides:
- `NexusmonEngine` — mission lifecycle management, sovereign decision API.

### Orchestrator (`kernel_runtime/orchestrator.py`)

Coordinates missions across the engine, emitting telemetry and audit events.

### Session (`nexusmon_runtime/session/`)

Manages per-operator sessions:

| Module | Purpose |
|--------|---------|
| `operator_session.py` | In-memory session state (cockpit, active mission, command log) |
| `session_router.py` | FastAPI router for `/session/start`, `/session/state`, `/session/end` |
| `session_store.py` | Persistent session log to `session_logs.json` |

`SessionStore` is lazy-initialized on first use to avoid import-time file I/O.

### Bootstrap (`nexusmon/backend/runtime/bootstrap.py`)

Initializes the database and runtime prerequisites. Run once before starting the server:

```bash
python scripts/init_db.py
```

## API Endpoints

### Missions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/missions/create` | Create a new mission |
| `POST` | `/v1/missions/run` | Execute a mission |
| `GET`  | `/v1/missions/list` | List all missions |
| `POST` | `/v1/missions/approve` | Approve a borderline mission |

### Session

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/session/start` | Open an operator session |
| `GET`  | `/api/session/state` | Retrieve current session state |
| `POST` | `/api/session/end` | Close and persist the session |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/system/health` | Runtime health |
| `GET` | `/v1/system/omens` | Detected pattern warnings |
| `GET` | `/v1/system/predictions` | Failure predictions |

### Meta / Sovereign

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/meta/decide` | Sovereign decision (full lattice flow) |
| `GET`  | `/v1/meta/lattice` | Lattice flow status |
| `POST` | `/v1/meta/kernel-ignition` | Execute kernel ignition sequence |

## Mission Lifecycle

```
create → [safety gate] → approve (if borderline) → run → audit log
```

### Decision Outcomes

| Score | Outcome | Action |
|-------|---------|--------|
| ≥ 60 | **SAFE** | Auto-execute |
| 30–59 | **BORDERLINE** | Requires operator approval |
| < 30 | **FAILING** | Suggestion only, execution blocked |

### Mission Categories

| Category | Purpose |
|----------|---------|
| `coin` | Revenue-generating (highest priority) |
| `forge` | Build / create |
| `library` | Research / learning |
| `sanctuary` | Maintenance / stability |

## Data Storage

All runtime data is stored in `data/`:

| File | Content |
|------|---------|
| `missions.jsonl` | Mission history (append-only) |
| `audit.jsonl` | Full event log |
| `telemetry.jsonl` | Runtime metrics |
| `runes.json` | Reusable mission templates |
| `system_state.json` | Pattern counters and system state |

## Six-Axis Validation

Every mission is scored across six dimensions:

1. **Compute Cost** — Resource usage
2. **Maintainability** — Long-term sustainability
3. **Attention** — Operator effort required
4. **Economic Value** — Expected ROI
5. **Trust** — Reliability and consistency
6. **Prediction Confidence** — Certainty of outcome

## Pattern Detection (Omens)

The runtime tracks repeated event patterns:

| Threshold | Action |
|-----------|--------|
| 1 occurrence | Ignore |
| 3 occurrences | Warn |
| 7 occurrences | Intervene |
| 13 occurrences | Lock module |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `mission_run_failed` | Ensure operator key is valid and runtime is fully initialized |
| `missing_runtime_metrics` | Run a mission to emit metrics |
| `missing_telemetry` | Verify `data/telemetry.jsonl` is writable |
| `busy_loops_detected` | Add sleep/backoff to polling loops |
| Import errors | Run `pip install -r requirements.txt` |

## Extending the Runtime

- **Plugins**: Add new capabilities in `plugins/`.
- **Addons**: Extend guardrails and observables in `addons/`.
- **Custom metrics**: Register via `tests/test_trials.py::test_register_custom_metric` pattern.



## Self-Diagnosis: CI & Dev Environment

### Quick health check

```bash
# 1. Install all dependencies
pip install -r requirements-dev.txt

# 2. Initialize database
python scripts/init_db.py

# 3. Run tests (requires pytest-timeout to be installed)
python -m pytest tests/ -v --tb=short

# 4. Run linter
ruff check core swarmz_runtime addons api swarmz_server.py run_server.py

# 5. Check formatting
black --check . --exclude 'tools/vscode-scaffold-bot/templates/'

# 6. Build frontend
npm --prefix frontend ci && npm --prefix frontend run build
```

### Key startup log lines

When the server starts successfully via `python run.py` or `python run_server.py`,
you should see these lines (in order):

```
[COLD START] data — OK
[ENGINES] All engines loaded.
[NEXUSMON] Boot #N — ...
[DAILY SCHEDULER] Background scheduler started.
[SWARM RUNNER] Background runner started.
LOCAL: http://127.0.0.1:8000/
LAN:   http://<ip>:8000/
```

If any `WARNING:` lines appear, the component is optional and the server can still
start. Only fatal import errors or `uvicorn` binding failures prevent startup.

### Common CI failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `unrecognized arguments: --timeout=30` | `pytest-timeout` not installed | `pip install pytest-timeout` or check `requirements-dev.txt` |
| `E902 No such file or directory` in ruff | File path in CI ruff command is wrong | Verify paths in `.github/workflows/ci.yml` |
| `123 files would be reformatted` by black | Code not formatted | Run `black . --exclude 'tools/vscode-scaffold-bot/templates/'` |
| Frontend `tsc` errors | TypeScript types missing | Run `npm --prefix frontend ci` first |
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed | Run `pip install -r requirements-dev.txt` |

### Environment variables

| Variable | Purpose | Required |
|----------|---------|---------|
| `ALLOWED_ORIGINS` | CORS allowed origins | Production only |
| `OPERATOR_KEY` | Auth password | Production only |
| `JWT_SECRET` | JWT signing key | Production only |
| `PORT` | Server port (default: 8000) | Optional |
| `HOST` | Server bind address (default: 0.0.0.0) | Optional |
| `VITE_API_BASE_URL` | Frontend API base URL | Dev/prod if not same-origin |

### Frontend (Vite) proxy setup

During local development, the frontend proxies `/v1` and `/health` to
`http://localhost:8000`. Start both services:

```bash
# Terminal 1: backend
python run.py --port 8000

# Terminal 2: frontend dev server
npm --prefix frontend run dev
```

The frontend will be available at `http://localhost:5173`.
