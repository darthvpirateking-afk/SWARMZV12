# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/memory/__init__.py -- NexusmonDB: unified SQLite persistence layer.

Tables
------
entity_state        -- singleton entity state row
entity_traits       -- per-entity trait scores (7 traits)
evolution_events    -- append-only evolution event log
operator_sessions   -- per-operator session tracking
system_metrics      -- telemetry snapshots
conversation_history -- full exchange log per operator
operator_profile    -- operator rank, metrics, and session history
artifacts           -- artifact vault (all artifact objects)
chronicle_entries   -- append-only narrative chronicle
dream_log           -- dream state entries generated during absence
missions            -- mission definitions and outcomes
swarm_units         -- swarm unit registry
factory_jobs        -- factory queue and completed jobs
conflict_log        -- disagreements and their resolutions
"""

import os
import sqlite3

# Canonical column set for entity_state -- used to detect stale schema
_ENTITY_STATE_REQUIRED_COLS = {
    "id",
    "operator_id",
    "operator_name",
    "bond_established_at",
    "total_seconds_alive",
    "current_form",
    "evolution_xp",
    "interaction_count",
    "mood",
    "boot_count",
    "last_boot",
    "last_interaction",
    "greeting",
}


class NexusmonDB:
    """Unified SQLite persistence layer for the NEXUSMON entity system.

    Opens db_path with check_same_thread=False and row_factory=sqlite3.Row.
    All five canonical tables are created by ensure_schema().
    Stale entity_state schemas (from prior versions) are migrated automatically.
    """

    def __init__(self, db_path: str = "data/nexusmon.db") -> None:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.ensure_schema()

    def _migrate_entity_state(self) -> None:
        """Drop entity_state if its columns do not match the spec schema."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entity_state'"
        )
        if cur.fetchone() is None:
            return  # table does not exist yet -- nothing to migrate
        cur.execute("PRAGMA table_info(entity_state)")
        existing_cols = {row[1] for row in cur.fetchall()}
        if not _ENTITY_STATE_REQUIRED_COLS.issubset(existing_cols):
            self.conn.execute("DROP TABLE entity_state")
            self.conn.commit()

    def ensure_schema(self) -> None:
        """Create all tables if they do not already exist.

        Automatically drops entity_state when detected as stale.
        """
        self._migrate_entity_state()
        self.conn.executescript(
            # ── Core entity ────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS entity_state ("
            "id TEXT PRIMARY KEY, "
            "operator_id TEXT, "
            "operator_name TEXT, "
            "bond_established_at TEXT, "
            "total_seconds_alive INT NOT NULL DEFAULT 0, "
            "current_form TEXT NOT NULL DEFAULT 'ROOKIE', "
            "evolution_xp REAL NOT NULL DEFAULT 0.0, "
            "interaction_count INT NOT NULL DEFAULT 0, "
            "mood TEXT NOT NULL DEFAULT 'CALM', "
            "boot_count INT NOT NULL DEFAULT 0, "
            "last_boot TEXT, "
            "last_interaction TEXT, "
            "greeting TEXT); "
            "CREATE TABLE IF NOT EXISTS entity_traits ("
            "entity_id TEXT PRIMARY KEY, "
            "curiosity REAL NOT NULL DEFAULT 0.7, "
            "loyalty REAL NOT NULL DEFAULT 1.0, "
            "aggression REAL NOT NULL DEFAULT 0.3, "
            "creativity REAL NOT NULL DEFAULT 0.6, "
            "autonomy REAL NOT NULL DEFAULT 0.5, "
            "patience REAL NOT NULL DEFAULT 0.7, "
            "protectiveness REAL NOT NULL DEFAULT 0.8); "
            "CREATE TABLE IF NOT EXISTS evolution_events ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "entity_id TEXT NOT NULL, "
            "from_form TEXT NOT NULL, "
            "to_form TEXT NOT NULL, "
            "occurred_at TEXT NOT NULL, "
            "trigger TEXT); "
            "CREATE TABLE IF NOT EXISTS operator_sessions ("
            "operator_id TEXT PRIMARY KEY, "
            "session_count INT NOT NULL DEFAULT 0, "
            "last_seen TEXT, "
            "nexus_form TEXT, "
            "drift REAL NOT NULL DEFAULT 0.0); "
            "CREATE TABLE IF NOT EXISTS system_metrics ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp TEXT NOT NULL, "
            "entropy REAL, "
            "drift REAL, "
            "coherence REAL); "
            # ── Conversation memory ────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS conversation_history ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "operator_id TEXT NOT NULL, "
            "role TEXT NOT NULL, "
            "content TEXT NOT NULL, "
            "timestamp TEXT NOT NULL); "
            # ── Operator profile ───────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS operator_profile ("
            "operator_id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL DEFAULT 'Regan Stewart Harris', "
            "rank TEXT NOT NULL DEFAULT 'RECRUIT', "
            "coherence REAL NOT NULL DEFAULT 0.8, "
            "fatigue REAL NOT NULL DEFAULT 0.0, "
            "drift REAL NOT NULL DEFAULT 0.0, "
            "focus REAL NOT NULL DEFAULT 1.0, "
            "total_sessions INT NOT NULL DEFAULT 0, "
            "total_commands INT NOT NULL DEFAULT 0, "
            "message_count INT NOT NULL DEFAULT 0, "
            "mission_success_rate REAL NOT NULL DEFAULT 0.0, "
            "last_updated TEXT); "
            # ── Artifact vault ─────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS artifacts ("
            "id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "type TEXT NOT NULL, "
            "rarity TEXT NOT NULL DEFAULT 'COMMON', "
            "version INT NOT NULL DEFAULT 1, "
            "created_by TEXT NOT NULL DEFAULT 'NEXUSMON', "
            "created_at TEXT NOT NULL, "
            "tags TEXT NOT NULL DEFAULT '[]', "
            "metadata TEXT NOT NULL DEFAULT '{}', "
            "payload TEXT NOT NULL DEFAULT '{}', "
            "equipped_to TEXT, "
            "synergy_ids TEXT NOT NULL DEFAULT '[]'); "
            # ── Chronicle ──────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS chronicle_entries ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event_type TEXT NOT NULL, "
            "title TEXT NOT NULL, "
            "content TEXT NOT NULL, "
            "occurred_at TEXT NOT NULL, "
            "form TEXT NOT NULL DEFAULT 'ROOKIE', "
            "significance REAL NOT NULL DEFAULT 0.5); "
            # ── Dream log ──────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS dream_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "entered_at TEXT NOT NULL, "
            "exited_at TEXT, "
            "dream_type TEXT NOT NULL DEFAULT 'SIMULATION', "
            "content TEXT NOT NULL, "
            "significance REAL NOT NULL DEFAULT 0.5, "
            "shared INT NOT NULL DEFAULT 0); "
            # ── Missions ───────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS missions ("
            "id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "type TEXT NOT NULL, "
            "difficulty INT NOT NULL DEFAULT 1, "
            "status TEXT NOT NULL DEFAULT 'PENDING', "
            "assigned_units TEXT NOT NULL DEFAULT '[]', "
            "created_at TEXT NOT NULL, "
            "started_at TEXT, "
            "completed_at TEXT, "
            "outcome TEXT, "
            "loot TEXT NOT NULL DEFAULT '[]', "
            "xp_reward REAL NOT NULL DEFAULT 10.0); "
            # ── Swarm units ────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS swarm_units ("
            "id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "type TEXT NOT NULL, "
            "level INT NOT NULL DEFAULT 1, "
            "xp REAL NOT NULL DEFAULT 0.0, "
            "evolution_tier INT NOT NULL DEFAULT 1, "
            "status TEXT NOT NULL DEFAULT 'IDLE', "
            "specialization TEXT, "
            "abilities TEXT NOT NULL DEFAULT '[]', "
            "missions_completed INT NOT NULL DEFAULT 0, "
            "missions_failed INT NOT NULL DEFAULT 0, "
            "created_at TEXT NOT NULL, "
            "personal_lore TEXT NOT NULL DEFAULT ''); "
            # ── Factory jobs ───────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS factory_jobs ("
            "id TEXT PRIMARY KEY, "
            "recipe_id TEXT NOT NULL, "
            "recipe_name TEXT NOT NULL, "
            "status TEXT NOT NULL DEFAULT 'QUEUED', "
            "input_artifact_ids TEXT NOT NULL DEFAULT '[]', "
            "output_artifact_id TEXT, "
            "queued_at TEXT NOT NULL, "
            "started_at TEXT, "
            "completed_at TEXT); "
            # ── Conflict log ───────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS conflict_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "flag_type TEXT NOT NULL, "
            "flag_message TEXT NOT NULL, "
            "operator_choice TEXT, "
            "outcome TEXT, "
            "occurred_at TEXT NOT NULL, "
            "resolved_at TEXT); "
        )
        self.conn.commit()


_db = None


def get_db(db_path: str = "data/nexusmon.db") -> "NexusmonDB":
    """Return (or lazily create) the module-level NexusmonDB singleton."""
    global _db
    if _db is None:
        _db = NexusmonDB(db_path)
    return _db
