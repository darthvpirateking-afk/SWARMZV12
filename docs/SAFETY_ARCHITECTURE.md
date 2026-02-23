# SWARMZ Safety Architecture

This document describes the layered safety system built into the SWARMZ runtime. Each layer addresses a distinct class of risk, and together they form a defense-in-depth architecture.

## Overview

```
 ┌─────────────────────────────────────────────┐
 │              Operator Charter               │  ← Governance / Doctrine
 ├─────────────────────────────────────────────┤
 │              Guardrails (Bucket B)          │  ← Behavioral Observables
 ├─────────────────────────────────────────────┤
 │              Schema Guard                   │  ← Input Validation
 ├─────────────────────────────────────────────┤
 │              System Primitives              │  ← Error Classification & Constraint Solving
 ├─────────────────────────────────────────────┤
 │              Audit / Decision Ledger        │  ← Immutable Append-Only History
 └─────────────────────────────────────────────┘
```

## Layer 1 — Operator Charter

**Location**: `swarmz_runtime/core/operator_charter.py`

The Operator Charter is the top-level governance contract. It defines:

- **Prime Directive** — the operator's mission statement, enforced at runtime.
- **Operating Matrix** — maps action types to validity criteria.
- **Doctrine Gates** — immutability and replayability invariants that cannot be overridden.

### Charter Sections

1. Identity — system name and operator binding
2. Safety & Governance — enforcement rules
3. Value System — decision priority ordering
4. Capabilities — allowed action space
5. Constraints — hard and soft limits
6. Communication Protocol — output format and escalation paths
7. Evolution Policy — versioning and mutation rules
8. Override Policy — conditions under which operator overrides are accepted

**Threat addressed**: Uncontrolled operator escalation, doctrine drift, unauthorized override.

## Layer 2 — Guardrails (Bucket B)

**Location**: `addons/guardrails.py`

Behavioral observables translated from high-level risk principles into enforceable runtime checks.

| Guardrail | Purpose |
|-----------|---------|
| Counterfactual Baseline | Compares actual outcomes against a simulated baseline to detect systematic deviation |
| Decision Pressure Map | Tracks conditions that increase the probability of unsafe decisions |
| Interference / Coupling Graph | Maps dependencies between missions to detect unsafe coupling |
| Template Half-life / Decay | Flags stale templates that may produce incorrect outputs |
| Irreversibility Tagging | Marks actions as reversible or irreversible; enforces delay windows before irreversible actions execute |
| Cheap Falsification First | Ensures low-cost checks are run before expensive operations |
| Negative Capability Map | Documents what the system cannot do to prevent false-confidence failures |
| Silence-as-Signal | Treats missing output as an observable event, not an absence of data |
| Surprise Detector | Compares current behavior against shadow replays to detect unexpected divergence |
| Adversarial Input Stability | Checks that outputs remain stable under perturbed inputs |
| Opportunity Cost Shadow | Tracks the cost of not choosing alternative options (regret tracking) |
| Saturation Monitor | Detects resource or attention saturation before it causes failures |

**Threat addressed**: Behavioral drift, adversarial inputs, compounding errors, runaway resource usage.

## Layer 3 — Schema Guard

**Location**: `core/schema_guard.py`

Lightweight JSON schema validation with no external dependencies. All incoming API payloads are validated against declared schemas before processing.

**Threat addressed**: Malformed input, injection via unexpected field types, schema drift.

## Layer 4 — System Primitives

**Location**: `swarmz_runtime/core/system_primitives.py`

Provides two key safety utilities:

### Error Taxonomy

All runtime errors are classified into a structured taxonomy:

| Code | Severity | Category |
|------|----------|---------|
| `constraint_violation` | high | policy |
| `compile_failed` | high | compiler |
| `reality_sync_conflict` | medium | sync |
| `override_denied` | high | override |
| `unknown_error` | medium | unknown |

Classification is performed by `classify_error(code, message, details)`. Every classified error includes a timestamp and structured details payload.

### Real-Time Constraint Solver

`RealTimeConstraintSolver` enforces hard constraints during mission execution. Constraints are evaluated before any irreversible action is taken.

**Threat addressed**: Unclassified errors obscuring root cause, constraint violations reaching execution.

## Layer 5 — Audit / Decision Ledger

**Location**: `swarmz_runtime/decision_ledger/decision_ledger.py`

An append-only, thread-safe ledger that records every significant decision. Key properties:

- Uses `threading.Lock` for concurrent write safety.
- Persists entries as JSONL to `data/audit_decisions.jsonl`.
- Provides `read_jsonl` / `append_jsonl` helpers (`swarmz_runtime/storage/jsonl_utils.py`).
- Entries are never modified or deleted — only appended.

**Threat addressed**: Audit gaps, non-repudiation failures, inability to replay history.

## Safety Invariants

The following invariants are enforced across all layers:

1. **STATE != TRUTH** — system state is always derived from history, never the source of truth.
2. **HISTORY == TRUTH** — the audit log is the authoritative record.
3. **Append-only writes** — no data file is ever overwritten; only appended.
4. **Irreversible actions require delay windows** — enforced by the Irreversibility Tagger guardrail.
5. **No verification → rejected** — actions without a verification signal are not accepted.
6. **No artifact → nonexistent** — unverified artifacts are treated as not present.

## How the Layers Interact

```
Incoming request
       │
       ▼
  Schema Guard ──── invalid ──→ 400 Bad Request
       │ valid
       ▼
  Operator Charter ── doctrine violation ──→ 403 Forbidden
       │ allowed
       ▼
  Guardrails ── adversarial / surprise ──→ halt + audit entry
       │ pass
       ▼
  System Primitives (constraint check)
       │ satisfied
       ▼
  Mission Execution
       │
       ▼
  Audit Ledger (append entry) ←── always runs
```

## Extending the Safety System

- Add new guardrails in `addons/guardrails.py` by implementing a check function and registering it in the guardrails configuration.
- Extend the error taxonomy in `swarmz_runtime/core/system_primitives.py` by adding entries to `ERROR_TAXONOMY`.
- Add new charter sections in `swarmz_runtime/core/operator_charter.py` following the existing section pattern.
- All extensions should have corresponding test coverage in `tests/`.
