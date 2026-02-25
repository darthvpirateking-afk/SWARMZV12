# NEXUSMON Runtime System

## Quick Start

Start the server:
```bash
python run_nexusmon.py
```

Server will be available at: http://127.0.0.1:8012

API Documentation: http://127.0.0.1:8012/docs

## Runtime Check (Recommended)

Run a quick self-check to validate the runtime and telemetry wiring:

```bash
python tools/runtime_check.py
```

Machine-readable output:

```bash
python tools/runtime_check.py --json
```

Use a custom data directory:

```bash
python tools/runtime_check.py --data-dir data
```

Example output (human):

```text
=== RUNTIME CHECK ===
status: ok
wall_ms: 123.45
mission create/run: {"created": {"mission_id": "..."}, "ran": {"status": "ok"}}
last_runtime_metric: {"ts": 1739999999, "cpu_ms": 42}
last_telemetry: {"ts": 1739999999, "event": "mission_ran"}
busy_loops_detected: none
```

## API Endpoints

### Missions

- `POST /v1/missions/create` - Create new mission
- `POST /v1/missions/run` - Execute mission
- `GET /v1/missions/list` - List all missions
- `POST /v1/missions/approve` - Approve mission with operator key

### System

- `GET /v1/system/health` - System health status
- `GET /v1/system/omens` - Pattern detection results
- `GET /v1/system/predictions` - Failure predictions
- `GET /v1/system/templates` - Reusable templates (runes)

### Admin

- `POST /v1/admin/maintenance` - Schedule maintenance tasks

## Additional Notes

- **Operator Key**: Ensure the operator key is stored securely in `data/operator_pin.txt`.
- **Logs**: All actions are logged for transparency.
- **Extensibility**: Add new capabilities via plugins in the `plugins/` directory.
- **Health Check**: Use `/v1/health` to verify the system is running.

## Troubleshooting

Common runtime check issues and fixes:

- **mission_run_failed**: Ensure the operator key is valid and the runtime is fully initialized.
- **missing_runtime_metrics**: Start the server once and run a mission to emit metrics.
- **missing_telemetry**: Verify telemetry is enabled and `data/telemetry.jsonl` is writable.
- **busy_loops_detected**: Review polling loops and add sleep/backoff.

If the runtime check fails immediately, reinstall dependencies:

```bash
pip install -r requirements.txt
```

## Example Requests

### Create Mission
```bash
curl -X POST http://127.0.0.1:8012/v1/missions/create \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Optimize lead conversion process",
    "category": "coin",
    "constraints": {"max_time_seconds": 60, "max_steps": 3}
  }'
```

### List Missions
```bash
curl http://127.0.0.1:8012/v1/missions/list
```

### Get Health Status
```bash
curl http://127.0.0.1:8012/health
```

### Run Mission
```bash
curl -X POST http://127.0.0.1:8012/v1/missions/run \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "abc123",
    "operator_key": "nexusmon_sovereign_key"
  }'
```

## Mission Categories

- `coin` - Revenue-generating missions (highest value)
- `forge` - Build/create missions
- `library` - Research/learning missions
- `sanctuary` - Maintenance/stability missions

## Six-Axis Validation

Every mission is evaluated across:

1. **Compute Cost** - Runtime resources
2. **Maintainability** - Long-term sustainability
3. **Attention** - Operator effort required
4. **Economic Value** - Expected ROI
5. **Trust** - Reliability and consistency
6. **Prediction Confidence** - Certainty of outcome

## Decision Outcomes

- **SAFE** (score >= 60) - Execute automatically
- **BORDERLINE** (30-59) - Requires operator approval
- **FAILING** (< 30) - Suggestion only, blocked from execution

## Data Storage

All data stored locally in `data/` directory:

- `missions.jsonl` - Mission history
- `audit.jsonl` - Event log
- `runes.json` - Reusable templates
- `system_state.json` - System state and pattern counters

## Pattern Detection (Omens)

System automatically detects repeated patterns:

- 1 occurrence - Ignore
- 3 occurrences - Warn
- 7 occurrences - Intervene
- 13 occurrences - Lock module

## Operator Sovereignty

Operator key: `nexusmon_sovereign_key`

Use for approving borderline missions or overriding restrictions.

