# SWARMZ — Smoke Tests

> How to run smoke tests, what they check, and pass/fail criteria.

---

## Available Test Runners

| Runner | Location | Description |
|--------|----------|-------------|
| Quick Smoke (CMD) | `SWARMZ_SMOKE_TEST.cmd` | 7-step fast test via CMD |
| Quick Smoke (PS1) | `SWARMZ_SMOKE_TEST.ps1` | Same, PowerShell |
| Legacy Smoke (CMD) | `SWARMZ_SMOKE.cmd` | 3-step basic smoke |
| Full Smoke (Python) | `tools/smoke/run_smoke.py` | 7-step Python runner with detailed output |
| Zapier Smoke | `tools/test_zapier_bridge.py` | 3-step Zapier bridge test |

## How to Run

### Fastest Way

```cmd
SWARMZ_SMOKE_TEST.cmd
```

### Full Python Smoke

```cmd
python tools\smoke\run_smoke.py
```

### Zapier Only

```cmd
python tools\test_zapier_bridge.py
```

## What Gets Tested

### Full Smoke (`tools/smoke/run_smoke.py`)

| Step | Endpoint | Pass Criteria |
|------|----------|--------------|
| 1 | `GET /health` | Returns `{"status":"ok"}` |
| 2 | `GET /` | Returns HTML or JSON |
| 3 | `GET /v1/runtime/status` | Returns 200 (WARN if 404) |
| 4 | `GET /v1/missions` | Returns list or dict |
| 5 | `POST /v1/sovereign/dispatch` | Returns 200/401/403 |
| 6 | `POST /v1/zapier/inbound` | Returns `ok:true` or `dedupe:skipped` |
| 7 | `GET /v1/system/log` | Returns 200 |

### Zapier Smoke (`tools/test_zapier_bridge.py`)

| Step | What | Pass Criteria |
|------|------|--------------|
| 1 | POST inbound | Returns `ok:true` with event_id |
| 2 | POST emit | Returns response (may report no hook URL) |
| 3 | POST inbound (dedupe) | Same dedupe_key → `dedupe:skipped` |

## Pass/Fail Criteria

- **PASS**: Step returns expected response
- **WARN**: Step returns a non-critical deviation (e.g., endpoint not found but not required)
- **FAIL**: Step throws an error or returns unexpected response

**Overall Verdict:**
- `ALL CLEAR` — all steps passed
- `N FAILURES` — N steps failed, investigate output

## Prerequisites

- Server must be running: `SWARMZ_UP.cmd` or `uvicorn server:app --host 0.0.0.0 --port 8012`
- Python 3.10+ (for Python test runners)
- No additional dependencies needed (stdlib only)
