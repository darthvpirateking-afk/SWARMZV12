# NEXUSMON Release Readiness

Date: 2026-02-23
Branch: copilot/sub-pr-37

## Verdict

- **Go for normal development release** (code + API/UI + mission-path regression coverage are passing).
- **Conditional/No-Go for full live-infra release** until optional external runtime prerequisites are completed.

## Validation Snapshot

- Full suite: **303 passed, 3 skipped** (`python -m pytest tests/ -v --tb=short`)
- Browser parity smoke: **2 passed** (`tests/test_dashboard_browser_smoke.py` for `/` and `/console`)
- Targeted mission/UI checks are already passing from prior runs.

## Required for Normal Release (Done)

- [x] Core backend/API tests green
- [x] V5 adapter endpoint tests green
- [x] UI route tests green (`/`, `/config/runtime.json`)
- [x] Browser smoke click-flow coverage added and passing (`/`, `/console`)
- [x] Full regression suite green on current branch

## Optional for Full Live-Infra Release (Deferred)

These are not blockers for normal dev release, but are needed for full externalized runtime parity:

- [ ] WSL host health fully restored if using WSL/libvirt mission path
- [ ] `qemu-system-x86_64` available on host
- [ ] `virsh` and `libvirtd` available (WSL Ubuntu/libvirt path)
- [ ] Cloud provider environment variables set if cloud mission execution is required:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `DO_TOKEN`
  - `LINODE_TOKEN`
  - `VULTR_API_KEY`

## Go/No-Go Matrix

- **Go**: Local/dev deployments, CI test-gated merges, API/UI validation, mission-path regression checks.
- **No-Go (until deferred items are done)**: Live VM/libvirt/cloud-backed mission operations requiring external providers.

## Fast Resume Commands

```powershell
# Full suite
python -m pytest tests/ -v --tb=short

# Browser smoke parity
python -m pytest tests/test_dashboard_browser_smoke.py -v --tb=short

# Optional infra readiness re-check
& ".\NEXUSMON_V5_LIVE_SETUP.ps1" -InstallPythonDeps -InstallSystemDeps
```

