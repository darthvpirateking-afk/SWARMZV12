# Layer-Weaver Control Plane

Self-contained, event-driven control plane embedded inside Swarmz.

## Quick Start

### Prerequisites

- Python 3.11+
- `jsonschema` package (sole dependency)

### Running

**One-shot cycle:**
```bash
cd control_plane/layer_weaver
pip install -r requirements.txt
python -m control_plane.layer_weaver.weaver_service
```

**Continuous loop (30s interval):**
```bash
python -m control_plane.layer_weaver.weaver_service --loop --interval 30
```

**With verification runner (separate terminal):**
```bash
python -m control_plane.layer_weaver.verification_runner --loop
```

**Windows (venv auto-created):**
```cmd
run_weaver.cmd --loop --interval 30
```

**PowerShell:**
```powershell
.\run_weaver.ps1 -Loop -Interval 30
```

## Architecture

### Core Invariants

- **One unified STATE schema** – all state in `data/state.jsonl`
- **One scoring rule** – `Benefit − penalties(risk, coupling, irreversibility, uncertainty)`
- **One ACTION contract** – every action MUST include `verification` + `rollback`
- **Event-driven execution** – no polling loops as primary trigger
- **Regime-based objectives** with hysteresis
- **Suppression** – `NO_ACTION` emitted when best score ≤ 0

### Control Cycle

1. **Validate configs** – `objectives.json`, `coupling.json`, `actions.json` checked
   against JSON schemas. If invalid → `CONFIG_INVALID` event, cycle aborted.
2. **Collect state** from all registered layers.
3. **Evaluate regimes** – objectives activate/deactivate based on conditions with
   hysteresis (min_duration_active, cooldown_after_exit).
4. **Score actions** – deterministic scoring with tie-breaking.
5. **Select or suppress** – best positive score wins; otherwise `NO_ACTION`.
6. **Execute** – publish task via SwarmzAdapter.
7. **Log** – append decision to `data/decision_log.jsonl` with config_hash.

### Verification & Rollback

When `ACTION_SELECTED` fires, the `VerificationRunner`:
1. Captures baseline metric value.
2. Schedules check at the action's verification deadline.
3. At deadline: computes delta, evaluates pass/fail.
4. Emits `VERIFY_PASSED` or `VERIFY_FAILED`.
5. On failure: triggers rollback per the action's rollback spec:
   - `action_ref` → looks up rollback action, emits `ROLLBACK_TRIGGERED`
   - `instruction` → emits `ROLLBACK_TRIGGERED` with manual steps
   - `none` → only failure event

## Config Files

All in `data/`:

| File | Purpose |
|------|---------|
| `state.jsonl` | Append-only state records |
| `objectives.json` | Regimes with hysteresis, global lambdas, target ranges |
| `coupling.json` | Causal coupling edges between variables |
| `actions.json` | Action catalog with effects, rollback, verification |
| `decision_log.jsonl` | Decision outcomes (created at runtime) |
| `verification_log.jsonl` | Verification outcomes (created at runtime) |

### Config Validation

At every cycle start, all three config files are validated against their
JSON schemas in `schemas/`. If any fail validation, a `CONFIG_INVALID`
event is emitted with the list of errors and the cycle is aborted.

### Config Hash

Each decision and verification log entry includes a `config_hash` computed
from the SHA-256 of `objectives.json`, `coupling.json`, and `actions.json`.
This enables reproducibility and audit trail.

## Adding a New Layer

1. Create `layers/my_layer.py`:
```python
from .base import BaseLayer

class MyLayer(BaseLayer):
    name = "MyDomain"
    variables = ["my_domain.metric_a", "my_domain.metric_b"]

    def collect(self):
        return [
            self.make_record("MyDomain", "my_domain.metric_a", 42,
                             "count", 0.9, "higher_better"),
            self.make_record("MyDomain", "my_domain.metric_b", 0.5,
                             "ratio", 0.85, "lower_better"),
        ]
```

2. Register in `weaver_service.py`:
```python
from .layers.my_layer import MyLayer
# In WeaverService.__init__:
self.layers.append(MyLayer())
```

3. Add variables to `objectives.json` target_ranges.

## Adding a New Action

Every action in `data/actions.json` MUST include:
- `rollback` – how to undo (`action_ref`, `instruction`, or `none`)
- `verification` – metric, operator, target_delta, deadline

Example:
```json
{
  "id": "my_new_action",
  "target_layer": "MyDomain",
  "actuator": "my_actuator",
  "magnitude": {"type": "absolute", "value": 10},
  "duration": {"type": "hours", "value": 4},
  "irreversibility_cost": 0.2,
  "expected_effects": [
    {"variable": "my_domain.metric_a", "delta": 5, "units": "count",
     "horizon": {"type": "hours", "value": 4}, "confidence": 0.8}
  ],
  "rollback": {"type": "action_ref", "action_id": "undo_my_action"},
  "verification": {
    "metric": "my_domain.metric_a",
    "op": ">=",
    "target_delta": 3,
    "deadline": {"type": "hours", "value": 4},
    "data_requirement": "my_domain.metric_a"
  }
}
```

## Reading Logs

- **Decision log:** `data/decision_log.jsonl` – one JSON per line
- **Verification log:** `data/verification_log.jsonl` – one JSON per line
- **State history:** `data/state.jsonl` – append-only state records

```bash
# Latest decisions
tail -5 data/decision_log.jsonl | python -m json.tool --no-ensure-ascii

# Verification outcomes
tail -5 data/verification_log.jsonl | python -m json.tool --no-ensure-ascii
```

## Events

| Event | Source | Description |
|-------|--------|-------------|
| `WEAVER_CYCLE_STARTED` | weaver | Cycle begins |
| `WEAVER_CYCLE_COMPLETED` | weaver | Cycle ends |
| `CONFIG_INVALID` | weaver | Schema validation failed |
| `ACTION_SELECTED` | weaver | Action chosen and executed |
| `NO_ACTION` | weaver | Suppressed (score ≤ 0 or no objectives) |
| `VERIFY_SCHEDULED` | runner | Verification queued |
| `VERIFY_PASSED` | runner | Metric delta met target |
| `VERIFY_FAILED` | runner | Metric delta missed target |
| `ROLLBACK_TRIGGERED` | runner | Rollback initiated |

## Safe Expression Evaluation

Activation conditions in objectives use a restricted expression evaluator:
- Allowed: numbers, booleans, variable names, `and`/`or`/`not`, parentheses, comparisons
- **NO** attribute access, function calls, or imports
- Unknown variables → condition evaluates to `False`
