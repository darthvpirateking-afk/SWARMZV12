# NEXUSMON

**Governed autonomy organism. One operator. One system. No limits except the ones you set.**

NEXUSMON is an open-source autonomous execution system built on six real infrastructure layers — mission orchestration, worker execution, artifact memory, governance, evolution state, and operator control surface. The aesthetics are inspired by MegaMan Battle Network, Digimon, and Solo Leveling. The architecture is not.

---

## What It Is

A system that accepts missions, decomposes them into tasks, executes them with workers, stores every output as a versioned artifact, and evolves its own capabilities based on your history — governed entirely by you.

Not a chatbot. Not an agent wrapper. Not a dashboard over someone else's API.

An organism that belongs to one operator and grows through use.

---

## The Six Core Systems

| System | What It Does |
|--------|-------------|
| **Mission Engine** | Accept → decompose → assign → track → complete |
| **Worker Layer** | Tool runners, script executors, API connectors, plugin workers |
| **Artifact Vault** | Versioned outputs, logs, snapshots, operator review trails |
| **Governance** | Capability flags, risk tiers, approval gates, full audit log |
| **Evolution State** | Unlocked capabilities, not personality — traits are permissions |
| **Cockpit UI** | Mission feed, worker monitor, artifact vault, evolution tree |

---

## Evolution Is a Permissions System

```
DORMANT   → AWAKENING  (1 mission)    unlocks RECALL, COMPANION
AWAKENING → FORGING    (10 missions)  unlocks WORKER_SPAWN, BELIEF_TRACK
FORGING   → SOVEREIGN  (50 missions)  unlocks AUTONOMOUS_CHAIN, OPERATOR_FUSION
SOVEREIGN → APEX       (200 missions) unlocks everything
```

Completing missions earns XP. XP unlocks capabilities. Capabilities change what the system can do autonomously. Digimon philosophy as a real permissions system.

---

## Mission Ranks

| Rank | Risk | Execution |
|------|------|-----------|
| E | Trivial | Auto-execute |
| D | Low | Auto-execute |
| C | Medium | Log + flag for review |
| B | Elevated | Log + flag for review |
| A | High | Requires operator approval |
| S | Critical | Requires operator approval |

---

## Plugin Interface

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

## API Surface

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

## Stack

- **Backend**: Python + FastAPI
- **Storage**: SQLite + JSONL (fully local, no cloud dependency)
- **AI**: Anthropic Claude (optional — graceful fallback if unavailable)
- **Deploy**: Docker + Railway / any VPS

---

## Run Locally

```bash
git clone https://github.com/darthvpirateking-afk/NEXUSMON
cd NEXUSMON
pip install -r requirements.txt
cp .env.example .env
# set ANTHROPIC_API_KEY, OPERATOR_KEY, SWARMZ_JWT_SECRET
uvicorn swarmz_server:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/organism`

---

## Deploy to Railway

```bash
railway up
```

Set in dashboard: `ANTHROPIC_API_KEY`, `OPERATOR_KEY`, `SWARMZ_JWT_SECRET`

Add volume at `/app/data` — required for evolution persistence across deploys.

---

## Phases

- **Phase 1 — Core Engine** ✅
- **Phase 2 — Cockpit UI** ✅
- **Phase 3 — Evolution Layer** ✅
- **Phase 4 — Plugin Ecosystem** 🔲

---

## License

MIT. Run your own. Own your data. Own your organism.
