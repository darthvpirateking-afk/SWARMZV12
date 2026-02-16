# Layer-Weaver Control Plane

A self-contained, autonomous control-plane subsystem for the **swarmz** project.

## Architecture

| Component | File | Purpose |
|-----------|------|---------|
| **State Store** | `state_store.py` | Append-only JSONL state with schema validation |
| **Decision Logger** | `decision_logger.py` | Append-only decision log |
| **Verification Store** | `verification_store.py` | Append-only verification log |
| **Expression Eval** | `expression_eval.py` | Safe comparison evaluator |
| **Scoring** | `scoring.py` | Deterministic action scoring with configurable λ weights |
| **Regime Manager** | `regime.py` | Objective regimes with hysteresis |
| **Event Debouncer** | `event_debouncer.py` | Pub/sub event bus with debouncing |
| **Swarmz Adapter** | `swarmz_adapter.py` | In-process adapter abstraction |
| **Weaver Service** | `weaver_service.py` | Main event-driven control loop |
| **Verification Runner** | `verification_runner.py` | Post-action verification + rollback |

### Layers

Each layer module (in `layers/`) owns a set of state variables and provides a
`collect()` method:

- `money.py` – Budget / financial tracking
- `health.py` – System health
- `build.py` – CI build pass-rate
- `swarm_health.py` – Swarm node availability
- `permissions.py` – Access-scope tracking
- `memory.py` – Context-window / memory usage

### Data Files

All persistent state lives under `data/` as append-only JSONL or JSON configs:

| File | Format | Purpose |
|------|--------|---------|
| `state.jsonl` | JSONL | Append-only state log |
| `decision_log.jsonl` | JSONL | Every scoring decision |
| `verification_log.jsonl` | JSONL | Verification outcomes |
| `objectives.json` | JSON | Regime-based objectives |
| `coupling.json` | JSON | Directed coupling graph (EDGEs) |
| `actions.json` | JSON | Action catalogue with rollback & verification |

### Schemas

JSON Schema definitions live under `schemas/`:

- `state.schema.json`
- `edge.schema.json`
- `action.schema.json`
- `objective.schema.json`

## Scoring Rule

```
Score = Benefit − (λ_risk × Risk + λ_coupling × CouplingDamage
                   + λ_irr × Irreversibility + λ_uncertainty × Uncertainty)
```

- All deltas are normalised.
- Deterministic tie-breaking by `action_id` (lexicographic).
- If best score ≤ 0 → `NO_ACTION`.

## Regime Hysteresis

Each objective belongs to a **regime** with:

- `min_duration_active` – minimum seconds before deactivation
- `cooldown_after_exit` – cooldown before reactivation

## Quick Start

### Install dependencies

```bash
pip install -r control_plane/requirements.txt
```

### Run the weaver service (one-shot)

```bash
python control_plane/weaver_service.py
```

### Run the weaver service (continuous loop)

```bash
python control_plane/weaver_service.py --loop --interval 5
```

### Run the verification runner

```bash
python control_plane/verification_runner.py
```

### Run in continuous verification mode

```bash
python control_plane/verification_runner.py --loop --interval 2
```

## Dependencies

- Python 3.10+
- `jsonschema` (see `requirements.txt`)
