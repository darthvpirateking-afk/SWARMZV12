# SWARMZ Runtime System

## Quick Start

Start the server:
```bash
python run_swarmz.py
```

Server will be available at: http://127.0.0.1:8012

API Documentation: http://127.0.0.1:8012/docs

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
    "operator_key": "swarmz_sovereign_key"
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

Operator key: `swarmz_sovereign_key`

Use for approving borderline missions or overriding restrictions.
