# SWARMZ System Doctrine (Executable)

This codifies the architecture doctrine as enforceable runtime checks.

## Core Laws

- `STATE != TRUTH`
- `HISTORY == TRUTH`
- Truth is an ordered immutable event log
- State is a cache built from replay
- Change is append-only

## Execution Defaults

- Event-driven by default
- In-memory data passing preferred
- Replayable transitions required
- External verification required for accepted actions

## Versioning Law

- New change => new version
- Never modify prior versions
- Snapshot + append log is the base pattern

## Operating Matrix

- No artifact => nonexistent
- No verification => rejected
- No outcome => ignored
- External verification => accepted
- Irreversible action => operator approval required

## Runtime Endpoints

- `GET /v1/charter/doctrine`
- `POST /v1/charter/evaluate/change-flow`
- `POST /v1/charter/evaluate/operating-matrix`

## Notes

This does not replace existing policy engine checks; it adds a doctrine-level gate to preserve immutable history, replayability, and operator sovereignty.
