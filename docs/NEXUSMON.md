# NEXUSMON — Agent Summary

## What Is NEXUSMON?

NEXUSMON is the **conversational interface layer** of the NEXUSMON system. It is an evolution-aware AI companion that allows operators (humans) to interact with the NEXUSMON runtime through natural language. Rather than clicking through dashboards alone, an operator can type a message such as "Help me plan a mission" or "What is happening right now?" and NEXUSMON replies with contextualised, structured intelligence.

NEXUSMON has strict **operator sovereignty invariants**: it never takes autonomous action, never deceives, never flatters, and never pretends to be human. Every reply is grounded in missions, audit trails, or visible system state.

---

## System Integration

NEXUSMON is mounted on the NEXUSMON FastAPI server (`nexusmon_server.py`) under the prefix `/v1/nexusmon`. The router import is guarded so the server stays functional even if NEXUSMON dependencies are unavailable:

```python
# nexusmon_server.py
from core.nexusmon_router import router as nexusmon_router
app.include_router(nexusmon_router)
```

All runtime data is stored as append-only JSONL files under `data/` (which is git-ignored).

---

## File Map

| File | Role |
|------|------|
| `core/nexusmon_models.py` | Pydantic data models for all NEXUSMON concepts |
| `core/nexusmon_router.py` | FastAPI router — HTTP endpoints |
| `core/conversation_engine.py` | Intent classification, mode selection, reply generation |
| `core/persona_engine.py` | Evolution-aware persona and LLM system-prompt builder |
| `core/memory_engine.py` | Short-term (conversation turns) and long-term (operator memory) JSONL storage |
| `web/nexusmon_console.html` | Standalone HTML shell for the browser UI |
| `web/nexusmon_console.js` | Vanilla-JS `NexusmonConsole` module that drives the chat UI |

---

## Key Concepts

### NexusForm — Operator Evolution State

Every operator has a `NexusForm` that represents their current level of mastery in NEXUSMON. NEXUSMON adjusts its tone and abstraction based on this form.

| Form | Description | Persona Tone |
|------|-------------|--------------|
| `Operator` (default) | Grounded, learning the system | Direct, practical, low metaphor |
| `Cosmology` | Pattern-seeker, sees complexity | Abstract, metaphorical |
| `Overseer` | Strategic, commanding | Structural, commanding |
| `Sovereign` | Transcendent mastery | Minimal, nuanced, high abstraction |

### ChatMode — Response Modes

Each incoming message is classified by intent and mapped to one of six response modes:

| Mode | Triggered When | NEXUSMON Behaviour |
|------|---------------|--------------------|
| `Reflect` | Operator is stuck, confused, or asking about their own patterns | Mirrors patterns without prescribing |
| `Plan` | Operator wants to structure or design a mission | Co-structures a mission draft |
| `Explain` | "Why", "how does", "what is" questions | Teaches with concrete examples |
| `Nudge` | High drift detected | Gentle structural suggestion, never overrides autonomy |
| `MissionDraft` | "Create", "task", "goal" keywords | Formalises the conversation into a `MissionDraft` payload |
| `Status` | "Status", "what is happening" | Summarises running missions and health metrics |

### OperatorProfile — Behavioural Metrics

Stored in `data/operator_profiles.jsonl`. Key fields (all `float` in `[0, 1]` unless stated):

| Field | Meaning |
|-------|---------|
| `drift_score` | How far the operator has strayed from effective patterns |
| `friction` | Resistance or avoidance detected in recent behaviour |
| `coherence` | How internally consistent the operator's decisions are |
| `cognitive_bandwidth` | Estimated available mental capacity |
| `fatigue_level` | Detected fatigue (increases warmth in persona) |
| `risk_baseline` / `risk_current` | `low \| medium \| high` — informs directness |
| `mission_success_rate` | Historical rate of completed missions |
| `blind_spots` | List of known pattern gaps |
| `leverage_preferences` | Preferred problem-solving approaches |
| `explanation_preference` | `short \| detailed \| structural` |
| `directness_preference` | `low \| medium \| high` |

### SystemHealth

Computed at request time (stub in current code, production would derive from real metrics):

| Field | Meaning |
|-------|---------|
| `entropy` | System unpredictability / disorder |
| `drift` | Aggregate operator drift across the system |
| `coherence` | System-wide coherence score |

If `entropy > 0.7`, NEXUSMON automatically switches to `Reflect` mode regardless of intent.

---

## Request / Response Data Flow

```
Browser → POST /v1/nexusmon/chat
          {operator_id, message, context:{screen, mission_id}}

  1. Load/create OperatorProfile from JSONL
  2. Load/create NexusForm from JSONL
  3. Fetch recent ConversationTurns (last 20) from MemoryEngine
  4. Compute SystemHealth (stub)
  5. Build ConversationContext (all of the above)
  6. ConversationEngine.generate_reply():
       a. IntentClassifier  → intent string
       b. ModeSelector      → ChatModeType
       c. PersonaEngine     → Persona (tone params + system prompt)
       d. Mode handler      → reply text + SuggestedActions + optional MissionDraft
       e. StateSnapshot     → nexus_form + health + active_missions count
  7. MemoryEngine stores the ConversationTurn
  8. AuditEvent emitted to data/audit.jsonl

          ← ChatReply {reply, mode, suggested_actions, mission_draft, state_snapshot}
```

---

## API Endpoints (all under `/v1/nexusmon`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Main chat endpoint — processes a message and returns a structured reply |
| `GET` | `/health` | Simple liveness check |
| `GET` | `/operators/{id}/profile` | Retrieve or auto-create an OperatorProfile |
| `GET` | `/operators/{id}/nexus-form` | Retrieve or auto-create a NexusForm |
| `GET` | `/operators/{id}/conversation-history` | Recent conversation turns (default: last 20) |
| `GET` | `/operators/{id}/memory` | Long-term compressed operator memory |
| `POST` | `/operators/{id}/memory/update` | Write a new memory summary with tags and patterns |
| `GET` | `/system/health` | Returns current SystemHealth metrics |

---

## Persona Engine — LLM System Prompt

The `PersonaEngine` builds a system prompt that encodes:
- The operator's current NexusForm and character description
- Tone parameters: warmth, directness, abstraction, metaphor (each `0–1`)
- The full conversation context summary
- Hard constraints (no deception, no emotional manipulation, no autonomous action)
- Mode-specific guidance injected by each mode handler

The prompt is currently prepared for LLM integration but replies are generated by stub functions (`_generate_stub_reply`). Swapping in an actual LLM call requires only replacing the stub in `conversation_engine.py`.

---

## Memory Engine — Storage

| File | Content |
|------|---------|
| `data/conversation_turns.jsonl` | Every `ConversationTurn` (id, operator_id, message, reply, mode, tags, timestamp) |
| `data/operator_memory.jsonl` | Compressed long-term `OperatorMemory` (summary, tags, patterns) per operator |
| `data/operator_profiles.jsonl` | `OperatorProfile` objects — one record per operator |
| `data/nexus_forms.jsonl` | `NexusForm` objects — current evolution state per operator |
| `data/audit.jsonl` | All `AuditEvent` records (chat turns, errors, evolution changes) |

All files are append-only. The most recent record wins for profile/form lookups.

---

## Frontend — Browser UI

`web/nexusmon_console.html` is a self-contained HTML page that:
- Renders a two-pane layout: a sidebar (navigation, quick actions, operator info) and a main chat pane.
- Loads `web/nexusmon_console.js` which exports a `NexusmonConsole` module.
- Initialises with `NexusmonConsole.init(operatorId, {apiBase, screen, missionId})`.
- Updates operator form badge and system health indicators after each message.
- Dispatches `nexusmon:action` custom DOM events when suggested actions are clicked (e.g., `CreateMission`, `OpenMission`, `ViewMetrics`).

The JS module is a vanilla IIFE with a public API: `init`, `sendMessage`, `addMessage`, `loadProfile`, `loadForm`.

---

## Operator Sovereignty Invariants (Hard Constraints)

These are enforced at the prompt level and in the `PersonaConstraints` model. NEXUSMON must:

1. **Never** pretend to be human or emotionally independent.
2. **Never** make promises of exclusivity or irreplaceability.
3. **Never** undermine the operator's relationships or decision-making.
4. **Never** deceive about capabilities or limitations.
5. **Never** use flattery or emotional manipulation.
6. **Always** ground responses in missions, audit trails, or system structure.
7. **Never** initiate autonomous actions without operator consent.
8. **Always** be transparent about uncertainty and its own limits.

