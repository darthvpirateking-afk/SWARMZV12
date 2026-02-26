# NEXUSMON — Upgrade Contract

> Invariants that every future change MUST respect.  
> Breaking these rules degrades operator trust and system reliability.

---

## Core Invariants

### 1. Additive Only

New features **add** files, endpoints, and config keys.  
Existing code, files, and config keys are **never deleted or renamed**.

### 2. Fail-Open

Every optional module is loaded inside a `try/except` block.  
If a module fails, the server **must still start** without it.

```python
try:
    from core.some_module import register
    register(app)
except Exception:
    pass  # fail-open
```

### 3. No New Dependencies

All new code uses the **Python standard library only** (plus `fastapi`, `uvicorn`, `pyjwt` which are already in `requirements.txt`).  
Adding a new pip package requires explicit operator approval.

### 4. Append-Only Logs

All data files (`.jsonl`) are **append-only**. Lines are added, never removed or overwritten.  
This includes: `missions.jsonl`, `audit.jsonl`, `zapier/inbound.jsonl`, `zapier/outbound.jsonl`.

### 5. Single Config Source

All runtime configuration lives in **`config/runtime.json`**.  
New features add keys to this file. No separate config files without good reason.

### 6. Schema Version

The `schema_version` field in `config/runtime.json` is incremented when the config schema changes.  
Code must handle missing keys gracefully (use `.get()` with defaults).

### 7. Backward Compatibility

- New API endpoints are added under `/v1/` (or a new version prefix).
- Existing endpoint behavior is never changed in a breaking way.
- New response fields may be added; existing fields keep their meaning.

### 8. Windows-First

- All scripts have `.cmd` + `.ps1` variants.
- Path separators work on Windows.
- No Unix-only assumptions (no `#!/bin/bash` as the only option).

---

## Versioning Rules

| What | How |
|------|-----|
| Config schema | `schema_version` in `config/runtime.json` (integer, increment) |
| API version | URL prefix (`/v1/`, future `/v2/` etc.) |
| Agent changes | Append to `docs/CHANGELOG_AGENT.md` |

## How to Add a New Module

1. Create `core/your_module.py` with a `register_your_module(app)` function.
2. Add a fail-open registration block in `server.py`:
   ```python
   try:
       from core.your_module import register_your_module
       register_your_module(app)
   except Exception:
       pass
   ```
3. If it needs config, add keys under `config/runtime.json` → `integrations.your_module`.
4. If it writes data, create a subdirectory under `data/` with JSONL files.
5. Increment `schema_version` if you change the config schema.
6. Add a note in `docs/CHANGELOG_AGENT.md`.
7. Add a smoke test step in `tools/smoke/run_smoke.py`.

## What NOT To Do

- Do not rename or move existing files
- Do not change the meaning of existing config keys
- Do not add `import` statements that crash if a package is missing (use try/except)
- Do not write code that only works on Linux/Mac
- Do not overwrite or truncate JSONL log files
- Do not remove existing API endpoints

