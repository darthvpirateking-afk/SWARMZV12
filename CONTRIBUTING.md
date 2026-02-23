# Contributing to NEXUSMON / SWARMZ

Thank you for your interest in contributing!

## Quick Start

See [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for the
full developer guide including environment setup, how to run tests and lint, repo
structure, and coding conventions.

## Branch Naming

| Branch prefix | Use for |
|---|---|
| `feature/` | New features |
| `fix/` | Bug fixes |
| `build/` | Build / tooling changes |

`copilot/` branches are reserved for the GitHub Copilot agent.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(api): add trial list endpoint
fix(core): correct hologram level threshold
docs: update setup instructions
```

Allowed types: `feat`, `fix`, `build`, `chore`, `docs`, `perf`, `refactor`,
`test`, `ci`, `style`, `revert`.

## Pull Requests

1. Run the full test suite locally: `python -m pytest tests/ -v --tb=short`
2. Run linters: `ruff check core swarmz_runtime addons api` and `black --check .`
3. Fill in the PR template checklist before requesting review.
4. Keep PRs focused on a single logical change.

## Code of Conduct

Be respectful and professional.  This project is operator-sovereign tooling —
do not propose features that introduce undocumented surveillance, PII collection,
or unauthorized data exfiltration.
