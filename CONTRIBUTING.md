# Contributing to SWARMZ

Thank you for your interest in contributing to SWARMZ! This guide will help you get started.

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.10+ (3.13 recommended for CI compatibility)
- **Node.js**: 20+
- **Git**: Latest stable version

### Setup
```powershell
# Clone the repository
git clone https://github.com/darthvpirateking-afk/SWARMZV12.git
cd swarmz

# Install dependencies
pip install -r requirements-dev.txt
npm ci

# Initialize database
python scripts/init_db.py

# Run SWARMZ
./RUN.ps1  # Windows
./RUN.sh   # Linux/macOS
```

## 📋 Development Workflow

### 1. Branch Naming Convention
All branches **must** follow one of these patterns:

- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `build/<description>` - Build system changes
- `copilot/**` - System branches (auto-generated, protected)
- `main` - Production branch (protected)

**Examples:**
- ✅ `feature/add-memory-agent`
- ✅ `fix/database-connection-leak`
- ✅ `build/optimize-docker-image`
- ❌ `my-feature` (missing prefix)
- ❌ `bugfix/something` (use `fix/` instead)

### 2. Commit Message Convention
We follow **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code refactoring (no behavior change)
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `build` - Build system changes

**Examples:**
- ✅ `feat(agents): add reflection agent`
- ✅ `fix(api): handle null values in mission endpoint`
- ✅ `docs: update installation guide`
- ✅ `refactor(core): simplify state management`
- ❌ `added new feature` (no type prefix)
- ❌ `Fix bug` (not lowercase)

### 3. Making Changes

```bash
# Create a branch
git checkout -b feature/your-feature-name

# Make your changes...

# Run tests
python -m pytest tests/ -v

# Check formatting
black --check .
ruff check .

# Check types
mypy --ignore-missing-imports swarmz_runtime core addons

# For frontend changes
npm --prefix frontend run typecheck
npm --prefix frontend run test
```

### 4. Submitting a Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR** targeting `copilot/sub-pr-37` (current default branch)

3. **PR Requirements:**
   - All CI checks must pass
   - Follow commit message convention
   - Include description of changes
   - Add tests for new features
   - Update documentation if needed

## 🧪 Testing

### Run Tests
```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
npm --prefix frontend run test

# All tests
npm run test:ci
```

### Test Structure
- `tests/` - Backend Python tests
- `frontend/src/**/*.test.ts` - Frontend unit tests
- `test_*.py` (root) - Integration tests

## 🔍 Code Quality

### Linting
```bash
# Python
ruff check .
black .

# TypeScript/JavaScript
npm --prefix frontend run format:check
npm --prefix frontend run format  # auto-fix
```

### Type Checking
```bash
# Python
mypy --ignore-missing-imports swarmz_runtime core addons

# TypeScript
npm run typecheck
```

## 📦 Project Structure

```
swarmz/
├── swarmz/          # Core Python package
│   ├── backend/     # FastAPI backend
│   ├── runtime/     # Runtime engine
│   ├── config/      # Configuration
│   └── ui/          # Web UI server
├── frontend/        # React/TypeScript UI
├── apps/
│   └── gate-link/   # Isolated game project
├── tests/           # Test suite
├── scripts/         # Utility scripts
└── tools/           # Development tools
```

## 🛡️ CI/CD Pipeline

Our CI runs these checks on every push:
- ✅ Python tests (pytest)
- ✅ TypeScript tests (Jest/Vitest)
- ✅ Linting (ruff, ESLint)
- ✅ Type checking (mypy, tsc)
- ✅ Formatting (black, prettier)
- ✅ Security audit (pip-audit, npm audit)
- ✅ Build verification
- ✅ Import cycle detection
- ✅ Commit/branch policy enforcement

**All checks must pass before merge.**

## 🎯 Entry Points

Different ways to run SWARMZ:

- **`RUN.ps1/RUN.cmd/RUN.sh`** - Canonical launcher (production)
- **`run_swarmz.py`** - Python CLI entry point
- **`server.py`** - Direct FastAPI server
- **`swarmz_cli.py`** - Command-line interface
- **`companion.py`** - Companion mode

**For development, use `RUN.ps1` (Windows) or `RUN.sh` (Linux/macOS).**

## 📖 Documentation

Key docs to review:
- `README.md` - Project overview
- `ARCHITECTURE.md` - System architecture
- `USER_GUIDE.md` - End-user guide
- `docs/OPERATOR_PLAYBOOK.md` - Operator workflows
- `docs/RUNTIME_GUIDE.md` - Runtime details

## 🤝 Code Review Process

1. **Self-review** your changes before submitting
2. **Address all CI failures** before requesting review
3. **Respond to feedback** constructively
4. **Keep PRs focused** - one feature/fix per PR

## 📝 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see `LICENSE`).

## ❓ Questions?

- Check existing issues and PRs
- Review documentation in `docs/`
- Open a discussion issue if needed

---

**Thank you for contributing to SWARMZ! 🎯**
