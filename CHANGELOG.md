# Changelog

All notable changes to NEXUSMON will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive security audit confirming no hardcoded secrets
- Enhanced .gitignore with .env file protection
- Audit report documentation (docs/audit_report.md)
- This CHANGELOG.md file

### Fixed
- **Breaking deprecation warning**: Replaced all `datetime.utcnow()` calls with `datetime.now(datetime.UTC)` for Python 3.14+ compatibility
  - Affected: `swarm_runner.py` (3 instances at lines 55, 208, 300)
  - Impact: Future-proof ISO 8601 timestamp generation
  
- **FastAPI duplicate operation ID warnings**: Added explicit `operation_id` parameters to 11 duplicate route definitions
  - Affected files:
    - `nexusmon/routes/entity.py` (get_nexusmon_entity_state)
    - `core/nexusmon_router.py` (get_entity_state_v1, nexusmon_health)
    - `swarmz_server.py` (swarmz_health, swarmz_health_v1, avatar_page_main)
    - `server_legacy_overlay.py` (legacy_health, avatar_page_legacy)
    - `swarmz_runtime/api/observability.py` (observability_health)
    - `swarmz_runtime/api/system.py` (system_health)
    - `swarmz_runtime/api/server.py` (runtime_health)
    - `api/claimlab_routes.py` (claimlab_health)
  - Impact: Clean OpenAPI specification generation, no more warnings in /docs

- **Syntax errors**: Fixed duplicate `if` statements in `tests/test_galileo.py` (lines 73, 93)
  - Impact: Test collection now succeeds without IndentationError

### Changed
- **Test suite reorganization**: Moved 15 test files from root directory to `tests/` directory
  - Files moved:
    - test_arena.py
    - test_companion.py
    - test_console_endpoints.py
    - test_ecosystem.py
    - test_galileo.py
    - test_integration.py
    - test_kernel_ignition.py
    - test_mission_jsonl_robust.py
    - test_operator_rank.py
    - test_runtime_infra.py
    - test_security_module.py
    - test_swarmz.py
    - test_swarmz_server.py
    - test_ui.py
    - test_verification_runner.py
  - Impact: pytest now discovers 806 tests (up from 548), 782 passing (97% pass rate)

### Removed
- Temporary files cleaned from root directory:
  - `nul` (Windows reserved filename artifact)
  - `.tmp_gemini_upgrade.py` (temporary upgrade script)

### Test Results
- **Before reorganization**: 547 passed, 1 skipped, 7 warnings
- **After reorganization**: 782 passed, 23 failed, 1 skipped, 1 warning
- **Note**: 23 failures are in previously-hidden tests for unimplemented features, not regressions

### Known Issues
- 23 tests failing (documented in audit report):
  - 7× test_ecosystem.py (AutoLoop, Ecosystem endpoints)
  - 10× test_verification_runner.py (Verification store queries)
  - 4× test_operator_rank.py (Rank S edge cases)  
  - 2× others (legacy routing, runtime infra)
- OTEL trace export failure (localhost:4317 unavailable) - non-blocking
- 13× console.log statements remain in frontend code - cosmetic issue

---

## [0.1.0] - 2026-02-26 (Baseline)

### Established
- Core sovereign governance system with P1.1 meta-policy classifier
- Mission execution engine with DAG topology and reversible transactions  
- Companion persona system with evolution state tracking
- Plugin architecture with worker registry
- FastAPI-based REST API with WebSocket support
- React TypeScript frontend cockpit
- React Native mobile companion app
- Comprehensive test suite (547 passing tests)
- Self-healing kernel backup system
- Multi-layer governance (permissions, budget, health, security, boundaries)

### Architecture
- Python 3.10+ backend
- FastAPI async framework
- Universal operator authority model
- JSONL-based mission storage
- Artifact vault for mission outputs
- Capability flag progression system
- Rank-based permissions (E→D→C→B→A→S→N)

---

## How to Read This Changelog

- **[Unreleased]**: Changes in current development, not yet released
- **Version numbers** follow [Semantic Versioning](https://semver.org/)
- **Categories**:
  - **Added**: New features
  - **Changed**: Changes to existing functionality  
  - **Deprecated**: Soon-to-be removed features
  - **Removed**: Removed features
  - **Fixed**: Bug fixes
  - **Security**: Vulnerability fixes

For upgrade instructions and migration guides, see [INSTALL.md](INSTALL.md).
