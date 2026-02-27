# NEXUSMON Release Checklist — v0.1.0

## Go/No-Go
- [x] Working tree clean (`git status -sb`)
- [x] Branch synced with remote (`copilot/sub-pr-37...origin/copilot/sub-pr-37`)
- [x] Tests green (`217 passed, 1 skipped`)
- [x] Strict warning run green (`python -W error -m pytest tests/ -q`)
- [x] Build succeeded (`python -m build`)
- [x] License notice updated and pushed

## Release Commands
```bash
git checkout copilot/sub-pr-37
git pull --ff-only
python -m pytest tests/ -v --tb=short
python -m build
git tag -a v0.1.0 -m "NEXUSMON v0.1.0"
git push origin v0.1.0
```

## Optional GitHub Release Body
- Version: v0.1.0
- Scope: doctrine invariants + charter route + federation charter tests + proprietary licensing notice
- Validation: tests and package build passed

