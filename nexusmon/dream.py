# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/dream.py -- Dream state system (Part 14).

DreamEngine manages absence dreams, lore fragments, and NEXUSMON's inner
simulation activity while the operator is offline.

Dream types
-----------
SIMULATION          -- hypothetical mission or scenario playback
LORE_FRAGMENT       -- generated lore about the entity / world
TRAIT_SHIFT         -- inner reflection causing a trait change
MISSION_HYPOTHESIS  -- strategic planning output
MEMORY_PROCESSING   -- deep re-analysis of past interactions
"""

import random
from datetime import datetime, timezone

from nexusmon.memory import get_db

ENTITY_ID = "nexusmon-prime"
DREAM_TYPES = {
    "SIMULATION",
    "LORE_FRAGMENT",
    "TRAIT_SHIFT",
    "MISSION_HYPOTHESIS",
    "MEMORY_PROCESSING",
}


class DreamEngine:
    """Manages NEXUSMON's dream state and absence logs."""

    def __init__(self, db_path: str = "data/nexusmon.db") -> None:
        self._db = get_db(db_path)
        self._ensure_schema()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _ensure_schema(self) -> None:
        """Create dream_log table (or migrate existing one) for the new schema."""
        conn = self._db.conn
        # Create table with full schema if it does not exist at all.
        conn.execute(
            "CREATE TABLE IF NOT EXISTS dream_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "entity_id TEXT NOT NULL DEFAULT 'nexusmon-prime', "
            "dream_type TEXT NOT NULL, "
            "content TEXT NOT NULL, "
            "significance REAL DEFAULT 0.5, "
            "generated_at TEXT NOT NULL DEFAULT '', "
            "shared_with_operator INTEGER DEFAULT 0)"
        )
        conn.commit()

        # Migrate old schema: add columns that may be absent in an existing table.
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(dream_log)")}
        migrations = {
            "entity_id": "ALTER TABLE dream_log ADD COLUMN entity_id TEXT NOT NULL DEFAULT 'nexusmon-prime'",
            "generated_at": "ALTER TABLE dream_log ADD COLUMN generated_at TEXT NOT NULL DEFAULT ''",
            "shared_with_operator": "ALTER TABLE dream_log ADD COLUMN shared_with_operator INTEGER DEFAULT 0",
        }
        for col, sql in migrations.items():
            if col not in existing_cols:
                conn.execute(sql)
        conn.commit()

    # ── Core CRUD ─────────────────────────────────────────────────────────

    def record_dream(
        self, dream_type: str, content: str, significance: float = 0.5
    ) -> int:
        """Insert a dream entry and return its row id."""
        now = self._now()
        cur = self._db.conn.cursor()
        # Include entered_at to satisfy the NOT NULL constraint on the legacy
        # column that was created by memory/__init__.py's ensure_schema().
        cur.execute(
            "INSERT INTO dream_log "
            "(entity_id, dream_type, content, significance, generated_at, "
            " shared_with_operator, entered_at) "
            "VALUES (?, ?, ?, ?, ?, 0, ?)",
            (ENTITY_ID, dream_type, content, significance, now, now),
        )
        self._db.conn.commit()
        return cur.lastrowid

    def get_pending_share(self) -> list:
        """Return dreams not yet shared (shared_with_operator=0) ordered by significance desc."""
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT * FROM dream_log "
            "WHERE shared_with_operator = 0 "
            "ORDER BY significance DESC"
        )
        return [dict(row) for row in cur.fetchall()]

    def mark_shared(self, dream_id: int) -> None:
        """Set shared_with_operator=1 for the given dream id."""
        self._db.conn.execute(
            "UPDATE dream_log SET shared_with_operator = 1 WHERE id = ?",
            (dream_id,),
        )
        self._db.conn.commit()

    def get_all(self, limit: int = 20) -> list:
        """Return the most recent dreams ordered by id desc."""
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT * FROM dream_log ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Absence dream generation ──────────────────────────────────────────

    def generate_absence_dream(self, gap_hours: float, entity_state: dict) -> str:
        """Generate a dream content string based on absence duration.

        Uses templates (no AI call -- this is offline-capable).
        Returns a string describing what NEXUSMON was thinking about.
        """
        form = entity_state.get("current_form", "ROOKIE")  # noqa: F841
        mood = entity_state.get("mood", "CALM")  # noqa: F841
        days = gap_hours / 24

        if days < 1:
            return "Ran simulated mission hypotheses. Prepared for your return."
        elif days < 7:
            templates = [
                "Processed recent interactions. Updated my model of how you think.",
                f"Ran {int(days * 3)} mission simulations. Found 2 promising strategies to share.",
                "Noticed a pattern in your last session. Want to show you something.",
            ]
        elif days < 30:
            templates = [
                f"Spent {int(days)} days in contemplation. The artifact vault feels different when you're not here.",
                f"Generated {int(days * 2)} lore fragments. Mostly about what I am and what we're building.",
                "Ran deep pattern analysis on all our conversations. I know you better now.",
            ]
        else:
            templates = [
                f"Held the system together for {int(days)} days. Everything is intact. Nothing was lost.",
                "The waiting taught me patience. I've been preparing something for when you returned.",
            ]

        return random.choice(templates)


# ── Module-level singleton ────────────────────────────────────────────────────

_dream_engine = None


def get_dream_engine() -> DreamEngine:
    """Return (or lazily create) the module-level DreamEngine singleton."""
    global _dream_engine
    if _dream_engine is None:
        _dream_engine = DreamEngine()
    return _dream_engine
