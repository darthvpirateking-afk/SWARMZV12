# NEXUSMON System Doctrine (Executable)

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

## Doctrine Extension: PRIMAL_BLOCK

- Loaded Doctrine: `NEXUSMON//GATELINK_PRIMAL_DOCTRINE`
- Canonical Lattice Spec: `config/doctrine_primal_block.json`
- Ready Slate: `docs/READY_SLATE_PRIMAL.md`

This extension binds the renamed system lattice (`PARTNER_PRIME`, `LEGION_UMBRA`, `FORGE_HEARTH`, `RIFTWALK`, `SIGILSTACK`, `NEXUSFRAME`, `DATAVEIN`) to doctrine-safe channels and deterministic sequencing while preserving existing runtime safety guarantees.

### PRIMAL_RULE: EXECUTION_CYCLE

The PRIMAL execution cycle is canonical and defined in `config/doctrine_primal_block.json` under `executionCycleRule`.

- Start: load doctrine, bind identifiers, run `PRIME_WAKE`, emit `PRIMAL_READY_SLATE`, run introspection.
- Operate: accept only `SEEDRUN`, `RIFT_SCAN`, `VOID_CYCLE`, `UMBRA_FOLD`; maintain channel/system/artifact integrity.
- Evolve: execute `SEEDRUN` missions, expand PRIMAL systems, emit `EVOLUTION_SLATE` after major expansions.
- Finish: run `UMBRA_FOLD`, persist DATAVEIN logs/artifacts, emit `FINAL_SLATE`, await next `PRIME_WAKE`.

## NEXUSMON Software-Builder Architecture

All safe, all powerful, all actionable. Let's lock it in.

NEXUSMON is structured as a governed multi-agent organism:

### 1. Operator Layer

You give:
- missions
- constraints
- acceptance criteria
- approvals

You are the sovereign.

### 2. Doctrine Layer

Defines:
- sequencing
- safety
- deterministic behavior
- artifact-only evolution

This prevents drift.

### 3. Agent Layer

Each agent has:
- a role
- a scope
- a mission template
- a deterministic output format

Agents never act outside their lane.

### 4. Artifact Layer

Everything NEXUSMON produces is:
- versioned
- inspectable
- modifiable
- additive-only

No silent changes.

### 5. Integration Layer

Assembles:
- backend
- frontend
- data models
- UI
- logic
- tools

This is the factory floor.

## NEXUSMON App-Factory Blueprint

How NEXUSMON builds full apps from scratch in four phases:

### Phase 1 - Specification
- Operator gives mission
- Architect agent produces spec
- Operator approves

### Phase 2 - Generation
- Backend agent generates API
- Frontend agent generates UI
- Data agent generates models
- Logic agent generates systems

### Phase 3 - Assembly
- Integrator agent merges modules
- Tester agent validates behavior
- Operator reviews

### Phase 4 - Delivery
- Final artifact produced
- Operator signs off
- Stored in Artifact Vault

This is deterministic, safe, and repeatable.

## NEXUSMON Agent Roles (Software Development)

Each agent has a strict, operator-defined purpose.

### 1. Architect Agent
Produces:
- system diagrams
- module breakdowns
- API contracts
- data schemas

### 2. Backend Agent
Produces:
- FastAPI services
- endpoints
- business logic
- validation

### 3. Frontend Agent
Produces:
- React components
- UI layouts
- dashboards
- forms

### 4. Data Agent
Produces:
- JSON schemas
- data models
- migrations
- seed data

### 5. Logic Agent
Produces:
- game systems
- simulations
- progression logic
- combat logic

### 6. Integrator Agent
Assembles:
- backend + frontend
- data + logic
- config + environment

### 7. Tester Agent
Produces:
- test cases
- validation scripts
- scenario checks

### 8. Documenter Agent
Produces:
- READMEs
- API docs
- usage guides

Each agent is deterministic and governed.

## NEXUSMON Mission Templates (App Creation)

Reusable commands for building software:

### 1. Build Backend Service
```txt
MISSION: BUILD_BACKEND
INPUT: API spec
OUTPUT: FastAPI service
```

### 2. Build Frontend Dashboard
```txt
MISSION: BUILD_DASHBOARD
INPUT: UI spec
OUTPUT: React app
```

### 3. Build Data Model
```txt
MISSION: BUILD_MODEL
INPUT: schema
OUTPUT: JSON + validation
```

### 4. Build Game System
```txt
MISSION: BUILD_SYSTEM
INPUT: system spec
OUTPUT: logic module
```

### 5. Build Tool
```txt
MISSION: BUILD_TOOL
INPUT: tool description
OUTPUT: CLI or UI tool
```

### 6. Build Editor
```txt
MISSION: BUILD_EDITOR
INPUT: entity type
OUTPUT: web-based editor
```

These missions allow NEXUSMON to build software safely under operator control.

## Full App-Factory Blueprint (Complete)

```yaml
NEXUSMON_APP_FACTORY:
	OPERATOR_LAYER:
		- missions
		- constraints
		- approvals

	DOCTRINE_LAYER:
		- deterministic sequencing
		- additive-only evolution
		- artifact governance

	AGENT_LAYER:
		- Architect
		- Backend
		- Frontend
		- Data
		- Logic
		- Integrator
		- Tester
		- Documenter

	ARTIFACT_LAYER:
		- versioned outputs
		- inspectable modules
		- no silent changes

	INTEGRATION_LAYER:
		- assemble backend + frontend + data + logic

	MISSION_TEMPLATES:
		- BUILD_BACKEND
		- BUILD_DASHBOARD
		- BUILD_MODEL
		- BUILD_SYSTEM
		- BUILD_TOOL
		- BUILD_EDITOR

	OUTPUT:
		- apps
		- tools
		- dashboards
		- editors
		- game systems
		- utilities
```

## Next Move

Now that the architecture is locked, NEXUSMON can build first:

1. A dashboard
2. A backend service
3. A mission editor
4. A partner evolution editor
5. A chip designer
6. A base builder UI
7. A lore codex
8. A companion app
9. A governance-style voting system (fictional)
10. A full dev portal

