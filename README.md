# NEXUSMON

**⚡ Quantum-geometric autonomy infrastructure. Built to run real missions.**

```text
                ◇      △      ◯
            ◢────────────────────◣
            │      NEXUSMON       │
            │   OPERATOR SYSTEM   │
            │    EXECUTION CORE   │
            ◥────────────────────◤
                ◯      ✶      ◇
```

NEXUSMON is an open-source autonomy stack engineered for real execution: mission orchestration, worker operations, artifact memory, governance, evolution state, and a live operator control surface.

**Design language:** abstract geometry, high-signal interfaces, operator sovereignty.

---

## 🧠 What NEXUSMON Does

A mission-native execution system that accepts intent, decomposes it into tasks, runs those tasks through workers, records every output as versioned artifacts, and upgrades capabilities based on proven history — under explicit operator control.

Not a chatbot. Not an agent wrapper. Not a thin panel over someone else's cloud.

It is an autonomous operations stack owned by one operator, hardened by usage, and designed to compound over time.

> Geometry in the shell. Precision in the engine.

---

## 🧩 Six Core Systems

| System | What It Does |
|--------|-------------|
| **Mission Engine** | Accept → decompose → assign → track → complete |
| **Worker Layer** | Tool runners, script executors, API connectors, plugin workers |
| **Artifact Vault** | Versioned outputs, logs, snapshots, operator review trails |
| **Governance** | Capability flags, risk tiers, approval gates, full audit log |
| **Evolution State** | Unlocked capabilities, not personality — traits are permissions |
| **Cockpit UI** | Mission feed, worker monitor, artifact vault, evolution tree |

---

## 📈 Capability Progression

```
DORMANT   → AWAKENING  (1 mission)    unlocks RECALL, COMPANION
AWAKENING → FORGING    (10 missions)  unlocks WORKER_SPAWN, BELIEF_TRACK
FORGING   → SOVEREIGN  (50 missions)  unlocks AUTONOMOUS_CHAIN, OPERATOR_FUSION
SOVEREIGN → APEX       (200 missions) unlocks everything
```

Completing missions earns XP. XP unlocks capabilities. Capabilities change what the system can do autonomously. Progression acts as a real permissions system.

---

## 🎯 Mission Ranks

| Rank | Risk | Execution |
|------|------|-----------|
| E | Trivial | Auto-execute |
| D | Low | Auto-execute |
| C | Medium | Log + flag for review |
| B | Elevated | Log + flag for review |
| A | High | Requires operator approval |
| S | Critical | Requires operator approval |

---

## 🔌 Plugin Interface

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

## 💥 Why Teams Use It

- ⚙️ Executes work, not just chat.
- 🧾 Keeps full artifact history and review trails.
- 🛡️ Enforces approval gates for high-risk actions.
- 📊 Improves capability based on actual mission outcomes.
- 👤 Stays operator-owned from development to deployment.

---

## 📡 API Surface

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

## 🛠️ Stack

- **Backend**: Python + FastAPI
- **Storage**: SQLite + JSONL (fully local, no cloud dependency)
- **AI**: Anthropic Claude (optional — graceful fallback if unavailable)
- **Deploy**: Docker + Railway / any VPS

---

## 🚀 Run Locally

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

## ☁️ Deploy to Railway

```bash
railway up
```

Set in dashboard: `ANTHROPIC_API_KEY`, `OPERATOR_KEY`, `SWARMZ_JWT_SECRET`

Add volume at `/app/data` — required for evolution persistence across deploys.

---

## 🧭 Phases

- **Phase 1 — Core Engine** ✅
- **Phase 2 — Cockpit UI** ✅
- **Phase 3 — Evolution Layer** ✅
- **Phase 4 — Plugin Ecosystem** 🔲

---

## 📜 License

MIT. Run your own. Own your data. Own your organism.

`◇ NEXUSMON: abstract form, concrete execution.`
