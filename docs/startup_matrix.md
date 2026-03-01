# Startup Matrix

## Canonical ASGI Surface
- `backend.app:app`

## Entrypoints

| Script | Role | Runtime Surface |
|---|---|---|
| `run.py` | Primary operator boot path | `backend.app:app` |
| `run_server.py` | Compatibility wrapper | `backend.app:app` |
| `run_swarmz.py` | Compatibility wrapper with runtime flags/tools | `backend.app:app` |

## Migration Policy
- Additive-only migration in v0.1 alignment phase.
- No entrypoint deletions in this phase.
- Legacy wrappers remain until explicit operator-approved deprecation.
