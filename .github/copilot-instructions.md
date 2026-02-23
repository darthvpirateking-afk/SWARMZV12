# Copilot Instructions for NEXUSMON / SWARMZ

## Project Purpose

SWARMZ is an **operator-sovereign "do anything" runtime** — a multi-agent orchestration
framework with a FastAPI backend, a React/Vite frontend, a PWA, and a TypeScript
tooling layer.  The project goal is to give operators complete, auditable control over
automated missions, plugins, and agent pipelines.

## Dev Environment Setup

Requirements: **Python ≥ 3.10**, **Node.js 20**, npm.

```bash
# Python backend
pip install -r requirements-dev.txt   # includes test, lint and build tools
python scripts/init_db.py             # initialise the runtime database

# TypeScript / JavaScript (root tooling)
npm ci

# React frontend
npm --prefix frontend ci

# Phaser game sub-project (isolated; only needed when working on apps/gate-link)
npm --prefix apps/gate-link ci
```

Copy `.env.example` to `.env` and fill in any API keys you need
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.).  Most CI steps run with
`OFFLINE_MODE=true` and do not require live keys.

## Running the App

```bash
# Start backend (defaults to http://localhost:8012)
python run_server.py

# Start frontend dev server
npm --prefix frontend run dev

# Windows one-click start
./RUN.ps1         # or double-click RUN.cmd
```

Health check: `GET /v1/health` → `{"ok": true, "status": "ok"}`

## Running Tests and Lint

```bash
# Backend unit + integration tests
python -m pytest tests/ -v --tb=short

# Root JS tests
npm run test:ci

# Frontend Vitest
npm --prefix frontend run test

# Python linter (ruff) – must pass in CI
ruff check core swarmz_runtime addons api server.py swarmz_server.py run_server.py

# Python formatter (black) – must pass in CI
black --check .

# Type checking (mypy) – non-blocking in CI but should be addressed
mypy --ignore-missing-imports swarmz_runtime core addons

# TypeScript type checks
npm run typecheck
npm --prefix frontend run typecheck
npm --prefix apps/gate-link run typecheck

# Validate marketplace metadata
npm run plugin:validate
npm run skill:validate
```

## Repository Structure

```
.github/            GitHub Actions workflows, issue templates
addons/             Optional capability add-ons (guardrails, etc.)
api/                FastAPI route modules shared across entry points
apps/gate-link/     Isolated Phaser game sub-project (separate build pipeline)
core/               Core domain logic (hologram levels, trials, mission engine)
frontend/           React + Vite PWA (TypeScript)
kernel_runtime/     Low-level runtime kernel
plugins/            Dynamically loadable task plugins
scripts/            DB init, marketplace generation, validation helpers
skills/             Declarative skill manifests (JSON)
swarmz_runtime/     FastAPI app factory, routes, middleware
tests/              Pytest test suite (mirrors source structure)
tools/              Developer utilities (release gate, import cycle finder, etc.)
web_ui/             Static PWA assets
```

## Coding Conventions

- **Python**: `black` for formatting, `ruff` for linting.  All Python files must
  start with the SWARMZ licence header (see any existing `.py` file).  Use
  `str | None` union syntax (Python 3.10+), not `Optional[str]`.
- **TypeScript / JavaScript**: Prettier for formatting (`npm --prefix frontend run format:check`).
- **Naming**: snake_case for Python, camelCase for TypeScript/JavaScript.
- **Imports**: avoid circular imports between `core.*` modules — check with
  `python tools/find_import_cycles.py .`.
- **Performance-critical paths**: use `set` for membership checks (O(1)), not `list`.
- **Error handling**: prefer explicit error types; use fail-open defaults only where
  documented (e.g. trial auto-baseline).
- **API routes**: use `Query()` with `ge`/`le` validators for bounded numeric params.
- **Tests**: every new backend route requires a pytest test using `TestClient`.

## Commit and Branch Policy

- Follow **Conventional Commits**: `type(scope): description`
  - Allowed types: `feat`, `fix`, `build`, `chore`, `docs`, `perf`, `refactor`,
    `test`, `ci`, `style`, `revert`
  - `Merge pull request …` and `Merge branch …` messages are also accepted.
- Branch prefixes: `feature/`, `fix/`, `build/` for contributor branches.
  `copilot/` branches are reserved for the Copilot agent.

## PR Expectations

- All CI jobs must pass before merging (tests, lint, typecheck, format, build).
- Add or update tests for every changed code path.
- Update relevant documentation when behaviour changes.
- Keep PRs focused: one logical change per PR.
- Marketplace metadata (`README.md` Marketplace section) is auto-generated —
  run `npm run marketplace:generate` if you add/remove plugins or skills.

## Security and Privacy Notes

- SWARMZ assumes a **trusted operator**.  Do not expose the runtime directly to
  untrusted users without an authentication layer.
- Do **not** add features that silently collect, transmit, or log personally
  identifiable information (PII) about end-users.
- Do **not** add surveillance, tracking, or telemetry without explicit operator
  opt-in and clear documentation.
- All Python source files carry the SWARMZ Source Available License header.
  Commercial use, hosting, and resale are prohibited — see `LICENSE`.
- Respect existing authorisation boundaries: the `addons/guardrails.py` module and
  the `reality_gate` plugin enforce hard preflight constraints; do not bypass them.
