# SWARMZ Release Notes — v0.1.0

Date: 2026-02-20
Branch: copilot/sub-pr-37

## Summary
This release is focused, low-risk, and release-ready.

## Included Changes
- Added future-contract invariants to doctrine.
- Wired charter route behavior for those invariants.
- Added federation charter tests for the new invariants.
- Updated repository licensing notice to proprietary, all-rights-reserved.

## Validation
- Test suite: `217 passed, 1 skipped`.
- Strict warning mode test run passed (`python -W error -m pytest tests/ -q`).
- Packaging build passed (`python -m build`).

## Artifacts
- `dist/swarmz-0.1.0.tar.gz`
- `dist/swarmz-0.1.0-py3-none-any.whl`

## Notes
- Runtime test/build commands can update operational JSON/JSONL files under `data/` and `prepared_actions/`; these were restored to keep branch clean.
- Final branch status verified clean and synced with origin.
