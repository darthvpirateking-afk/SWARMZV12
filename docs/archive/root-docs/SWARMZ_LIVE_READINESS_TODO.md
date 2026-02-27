# NEXUSMON Live Readiness — Deferred Tasks

Status: **Deferred on purpose**. Core dev/test flow is already healthy.

## Current known-good
- Repo tests pass: `303 passed, 1 skipped`
- `tshark` found
- `qemu-img` found

## Deferred blockers (only needed for full live infra features)
- `qemu-system-x86_64` missing
- `virsh` missing
- `libvirtd` missing (via WSL/libvirt path)
- WSL Ubuntu launch failure observed (`Wsl/Service/CreateInstance/E_UNEXPECTED`)
- Cloud vars not set:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_DEFAULT_REGION`
  - `DO_TOKEN`
  - `LINODE_TOKEN`
  - `VULTR_API_KEY`
  - `PLAYWRIGHT_BROWSERS_PATH`

## Resume later (copy/paste)
```powershell
Set-Location "C:\Users\Gaming PC\Desktop\nexusmon"

# 1) Host repair (elevated)
Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\Gaming PC\Desktop\nexusmon\NEXUSMON_WSL_HOST_RECOVERY.ps1" -Apply'

# 2) WSL/libvirt bootstrap
& "C:\Users\Gaming PC\Desktop\nexusmon\NEXUSMON_V5_WSL_LIBVIRT_BOOTSTRAP.ps1" -Apply

# 3) Re-audit live deps
& "C:\Users\Gaming PC\Desktop\nexusmon\NEXUSMON_V5_LIVE_SETUP.ps1" -InstallSystemDeps

# 4) Verify repo state
python -m pytest tests/ -v --tb=short
```

## Note
If you are only doing normal local development/testing, you can keep this deferred.

