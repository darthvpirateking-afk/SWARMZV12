# Integration TODOs

This file tracks integration hooks that were skipped due to risk.

## Trials Inbox — Wired & Working

| Component | Path | Status |
|-----------|------|--------|
| Data model + storage | `core/trials.py` | Done |
| Background worker | `core/trials_worker.py` | Done |
| API endpoints (14) | `core/trials_api.py` | Done |
| Server registration | `server.py` (bottom) | Done |
| Inbox UI HTML | `web/trials.html` | Done |
| Inbox UI CSS | `web/trials.css` | Done |
| Inbox UI JS | `web/trials.js` | Done |
| Route `/trials` | `server.py` | Done |
| Test suite | `tests/test_trials.py` | Done |

## Trials — Integration Points Not Yet Connected

### 1. Gate enforcement in mission dispatch
- **File**: `swarmz_server.py` `/v1/missions/create`
- **What**: Call `require_trial()` before executing meaningful changes
- **Risk**: Low — fail-open gate

### 2. Metric resolvers pulling live telemetry
- **File**: `core/trials.py` built-in resolvers
- **What**: 6 built-in metrics read JSONL in `data/`; return 0.0 if no data
- **Risk**: Medium — scores meaningless until real telemetry flows

### 3. Worker thread lifecycle
- **File**: `server.py` bottom block
- **What**: Worker starts on import; multiple restarts could stack threads
- **Risk**: Low — each check cycle is idempotent

### 4. Link from main HUD
- **File**: `web/index.html` or `web/app.js`
- **What**: Add nav link to `/trials` from console
- **Risk**: None — purely additive

### 5. Survival scores in suggestion ranking
- **What**: Call `rank_suggestions()` from any suggestion-producing module
- **Risk**: Low — pure function, no side effects

### 6. Revert actually undoing changes
- **File**: `core/trials.py` `revert_trial()`
- **What**: Currently marks reverted + creates follow-up; no actual undo
- **Risk**: Medium — operator must manually revert

## Other TODO Entries

- **File Path**: TBD
- **Function Name**: TBD
- **What to Wrap**: TBD
- **What Data to Pass**: TBD
- **Why It Was Risky**: TBD

## Pending Tasks

- Implement macOS and Linux service installers in `tools/install_service.py`.
- Add SFTP and rsync support to `tools/sync_logs.py`.
