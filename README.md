# NEXUSMON

**MISSION EXECUTION INFRASTRUCTURE FOR OPERATORS WHO NEED OUTPUT, CONTROL, AND TRACEABILITY.**

NEXUSMON is an open-source mission operations stack. It converts objectives into executable task graphs, runs worker pipelines, stores artifacts with full lineage, and enforces governance before high-risk actions.

```text
OBJECTIVE -> TASK DAG -> WORKER EXECUTION -> VERSIONED ARTIFACTS -> OPERATOR REVIEW -> CAPABILITY GROWTH
```

---

## WHAT NEXUSMON DOES

A mission-native execution system for operators who need output, control, and auditability in one loop.

You provide objective → NEXUSMON decomposes it into a DAG → workers execute → artifacts are versioned → approvals gate critical actions → capability expands from proven outcomes.

Not a chatbot. Not an agent wrapper. Not a thin panel over someone else's cloud.

Local-first ownership. Plugin-extensible architecture. Governance-by-default execution.

> Real work. Real controls. Real memory.

---

## SIX CORE SYSTEMS

| System | What It Does |
|--------|-------------|
| **Mission Engine** | Accept → decompose → assign → track → complete |
| **Worker Layer** | Tool runners, script executors, API connectors, plugin workers |
| **Artifact Vault** | Versioned outputs, logs, snapshots, operator review trails |
| **Governance** | Capability flags, risk tiers, approval gates, full audit log |
| **Evolution State** | Unlocked capabilities, not personality — traits are permissions |
| **Cockpit UI** | Mission feed, worker monitor, artifact vault, evolution tree |

---

## CAPABILITY PROGRESSION

```
DORMANT   → AWAKENING  (1 mission)    unlocks RECALL, COMPANION
AWAKENING → FORGING    (10 missions)  unlocks WORKER_SPAWN, BELIEF_TRACK
FORGING   → SOVEREIGN  (50 missions)  unlocks AUTONOMOUS_CHAIN, OPERATOR_FUSION
SOVEREIGN → APEX       (200 missions) unlocks everything
```

Completing missions earns XP. XP unlocks capabilities. Capabilities change what the system can do autonomously. Progression acts as a real permissions system.

---

## MISSION RANKS

| Rank | Risk | Execution |
|------|------|-----------|
| E | Trivial | Auto-execute |
| D | Low | Auto-execute |
| C | Medium | Log + flag for review |
| B | Elevated | Log + flag for review |
| A | High | Requires operator approval |
| S | Critical | Requires operator approval |

---

## PLUGIN INTERFACE

```python
class WorkerPlugin:
    name: str
    capabilities: List[str]
    risk_level: str  # E D C B A S
    requires_approval: bool

    async def execute(self, task: Task) -> Result:
        ...
```

Add workers without touching core code.

---

## WHY TEAMS USE IT

- ⚙️ Executes work, not just chat.
- 🧾 Keeps full artifact history and review trails.
- 🛡️ Enforces approval gates for high-risk actions.
- 📊 Improves capability based on actual mission outcomes.
- 👤 Stays operator-owned from development to deployment.

---

## API SURFACE

```
POST /v1/engine/missions              create mission
GET  /v1/engine/missions              list missions
POST /v1/engine/missions/{id}/approve operator approval gate
POST /v1/engine/missions/{id}/run     execute
GET  /v1/vault/artifacts              artifact vault
GET  /v1/nexusmon/organism/status     full organism readout
GET  /v1/cognition/status             cognitive instrumentation
GET  /organism                        cockpit UI
GET  /landing                         public landing page
```

---

## STACK

- **Backend**: Python + FastAPI
- **Storage**: SQLite + JSONL (fully local, no cloud dependency)
- **AI**: Anthropic Claude (optional — graceful fallback if unavailable)
- **Deploy**: Docker + Railway / any VPS

---

## RUN LOCALLY

```bash
git clone https://github.com/darthvpirateking-afk/NEXUSMON
cd NEXUSMON
pip install -r requirements.txt
cp .env.example .env
# set ANTHROPIC_API_KEY, OPERATOR_KEY, NEXUSMON_JWT_SECRET
uvicorn nexusmon_server:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/organism`

---

## DEPLOY TO RAILWAY

```bash
railway up
```

Set in dashboard: `ANTHROPIC_API_KEY`, `OPERATOR_KEY`, `NEXUSMON_JWT_SECRET`

Add volume at `/app/data` — required for evolution persistence across deploys.

---

## PHASES

- **Phase 1 — Core Engine** ✅
- **Phase 2 — Cockpit UI** ✅
- **Phase 3 — Evolution Layer** ✅
- **Phase 4 — Plugin Ecosystem** 🔲

---

## LICENSE

MIT. Run your own. Own your data. Own your organism.

`◇ NEXUSMON: abstract form, concrete execution.`

