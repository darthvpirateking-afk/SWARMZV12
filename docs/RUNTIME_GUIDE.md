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


