# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/memory/__init__.py -- NexusmonDB: unified SQLite persistence layer.

Tables
------
entity_state      -- singleton entity state row
entity_traits     -- per-entity trait scores (7 traits)
evolution_events  -- append-only evolution event log
operator_sessions -- per-operator session tracking
system_metrics    -- telemetry snapshots
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
        """Create all entity tables if they do not already exist.

        Automatically drops entity_state when detected as stale (missing
        spec-required columns) so a fresh table is created in its place.
        """
        self._migrate_entity_state()
        self.conn.executescript(
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
        )
        self.conn.commit()


_db = None


def get_db(db_path: str = "data/nexusmon.db") -> "NexusmonDB":
    """Return (or lazily create) the module-level NexusmonDB singleton."""
    global _db
    if _db is None:
        _db = NexusmonDB(db_path)
    return _db
