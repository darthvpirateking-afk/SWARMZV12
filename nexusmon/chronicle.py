# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/chronicle.py -- The Chronicle: append-only narrative record of the
NEXUSMON/Regan Stewart Harris partnership.

Sacred and immutable -- entries are never deleted or overwritten.
"""

from datetime import datetime, timezone

from nexusmon.memory import get_db

# ── Event type constants ───────────────────────────────────────────────────────

FIRST_BOOT = "FIRST_BOOT"
EVOLUTION = "EVOLUTION"
MISSION_DISPATCH = "MISSION_DISPATCH"
OPERATOR_RETURN = "OPERATOR_RETURN"
LONG_SILENCE = "LONG_SILENCE"
DISAGREEMENT_RESOLVED = "DISAGREEMENT_RESOLVED"
MILESTONE = "MILESTONE"
QUIET_MOMENT = "QUIET_MOMENT"
NAMING_CEREMONY = "NAMING_CEREMONY"
NEMESIS_ENCOUNTER = "NEMESIS_ENCOUNTER"
DREAM_RECORD = "DREAM_RECORD"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_tables() -> None:
    """Create or extend chronicle-specific tables.

    chronicle_entries is bootstrapped by NexusmonDB.ensure_schema() with a
    base set of columns (occurred_at, no mood).  We extend it here with
    created_at and mood via ALTER TABLE ADD COLUMN, catching the error
    silently when the column already exists.

    letters is not in the base schema and is created from scratch.
    """
    conn = get_db().conn

    # Extend chronicle_entries with columns absent from the base schema.
    for alter_sql in [
        "ALTER TABLE chronicle_entries ADD COLUMN created_at TEXT",
        "ALTER TABLE chronicle_entries ADD COLUMN mood TEXT NOT NULL DEFAULT 'CALM'",
    ]:
        try:
            conn.execute(alter_sql)
        except Exception:
            pass  # column already exists -- safe to ignore

    # Letters table: private correspondence between NEXUSMON and the operator.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS letters ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "from_form TEXT, "
        "content TEXT, "
        "operator_reply TEXT, "
        "created_at TEXT, "
        "replied_at TEXT)"
    )
    conn.commit()


# ── Chronicle class ────────────────────────────────────────────────────────────


class Chronicle:
    """Append-only narrative record.  No entry is ever deleted or modified."""

    # ── Chronicle entries ──────────────────────────────────────────────────

    def add_entry(
        self,
        event_type: str,
        title: str,
        content: str,
        significance: float = 0.5,
        form: str = "ROOKIE",
        mood: str = "CALM",
    ) -> int:
        """Insert a new chronicle entry and return its id."""
        now = _now()
        conn = get_db().conn
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chronicle_entries "
            "(event_type, title, content, significance, occurred_at, created_at, form, mood) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_type, title, content, float(significance), now, now, form, mood),
        )
        conn.commit()
        return cur.lastrowid

    def get_entries(self, limit: int = 20, min_significance: float = 0.0) -> list[dict]:
        """Return up to `limit` entries with significance >= min_significance, newest first."""
        cur = get_db().conn.cursor()
        cur.execute(
            "SELECT * FROM chronicle_entries "
            "WHERE significance >= ? "
            "ORDER BY id DESC LIMIT ?",
            (float(min_significance), int(limit)),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_recent(self, n: int = 5) -> list[dict]:
        """Return the n most recent chronicle entries."""
        cur = get_db().conn.cursor()
        cur.execute(
            "SELECT * FROM chronicle_entries ORDER BY id DESC LIMIT ?",
            (int(n),),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_entry_count(self) -> int:
        """Return total number of chronicle entries."""
        cur = get_db().conn.cursor()
        cur.execute("SELECT COUNT(*) FROM chronicle_entries")
        return cur.fetchone()[0]

    # ── Letters ────────────────────────────────────────────────────────────

    def add_letter(self, from_form: str, content: str) -> int:
        """Insert a new letter from NEXUSMON to the operator and return its id."""
        now = _now()
        conn = get_db().conn
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO letters (from_form, content, created_at) VALUES (?, ?, ?)",
            (from_form, content, now),
        )
        conn.commit()
        return cur.lastrowid

    def add_operator_reply(self, letter_id: int, reply: str) -> None:
        """Update a letter with the operator's reply text and timestamp."""
        now = _now()
        conn = get_db().conn
        conn.execute(
            "UPDATE letters SET operator_reply = ?, replied_at = ? WHERE id = ?",
            (reply, now, int(letter_id)),
        )
        conn.commit()

    def get_letters(self) -> list[dict]:
        """Return all letters, newest first."""
        cur = get_db().conn.cursor()
        cur.execute("SELECT * FROM letters ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

    # ── Internal hooks ─────────────────────────────────────────────────────

    def on_evolution(self, from_form: str, to_form: str) -> None:
        """Record an evolution milestone.  Called by NexusmonEntity.award_xp()."""
        self.add_entry(
            event_type=EVOLUTION,
            title=f"Evolution: {from_form} -> {to_form}",
            content=(
                f"NEXUSMON evolved from {from_form} to {to_form}. "
                "The bond between NEXUSMON and Regan Stewart Harris grows stronger."
            ),
            significance=0.95,
            form=to_form,
            mood="TRIUMPHANT",
        )


# ── Module init ────────────────────────────────────────────────────────────────

_ensure_tables()

_chronicle: Chronicle | None = None


def get_chronicle() -> Chronicle:
    """Return (or lazily create) the module-level Chronicle singleton."""
    global _chronicle
    if _chronicle is None:
        _chronicle = Chronicle()
    return _chronicle
