# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/swarm.py -- SwarmEngine: swarm unit registry and lifecycle management.

Per NEXUSMON MASTER SPEC Part 6.

Unit types  : SCOUT, BUILDER, ANALYST, GUARDIAN, STRIKER, PHANTOM
Unit statuses: IDLE, ON_MISSION, RECOVERING, EVOLVING, RETIRED

XP threshold: level * 100.  When xp >= threshold, unit levels up and xp resets.

Starter seed (3 units created when table is empty):
  SCOUT "Scout-01"  |  BUILDER "Builder-01"  |  ANALYST "Analyst-01"
"""

import uuid
from datetime import datetime, timezone

from nexusmon.memory import get_db

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UNIT_TYPES = ["SCOUT", "BUILDER", "ANALYST", "GUARDIAN", "STRIKER", "PHANTOM"]
UNIT_STATUSES = ["IDLE", "ON_MISSION", "RECOVERING", "EVOLVING", "RETIRED"]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _table_cols(conn, table: str) -> set:
    """Return the set of column names for *table*."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _row_to_unit(row) -> dict:
    """Convert a sqlite3.Row (or dict-like) to a spec-conformant unit dict.

    The existing NexusmonDB schema uses column ``type`` while the spec names
    the field ``unit_type``.  We normalise here so callers always see
    ``unit_type``.
    """
    d = dict(row)
    # Normalise "type" -> "unit_type"
    if "unit_type" not in d:
        d["unit_type"] = d.pop("type", "")
    elif "type" in d:
        # Both columns present (after ALTER TABLE); prefer unit_type if set,
        # fall back to type for rows seeded before migration.
        if not d["unit_type"]:
            d["unit_type"] = d.pop("type", "")
        else:
            d.pop("type", None)
    # Ensure generated_from key exists
    if "generated_from" not in d:
        d["generated_from"] = ""
    return d


# ---------------------------------------------------------------------------
# SwarmEngine
# ---------------------------------------------------------------------------


class SwarmEngine:
    """Manages swarm units in the NexusmonDB ``swarm_units`` table."""

    def __init__(self) -> None:
        self.db = get_db()
        self._ensure_tables()
        self._seed()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create the swarm_units table (if absent) and add any missing columns."""
        conn = self.db.conn

        # Primary CREATE — only runs when the table does not yet exist.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS swarm_units (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                unit_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp REAL DEFAULT 0.0,
                evolution_tier INTEGER DEFAULT 1,
                status TEXT DEFAULT 'IDLE',
                specialization TEXT DEFAULT '',
                abilities TEXT DEFAULT '[]',
                generated_from TEXT DEFAULT '',
                missions_completed INTEGER DEFAULT 0,
                missions_failed INTEGER DEFAULT 0,
                personal_lore TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )

        # Retroactively add columns that exist in the spec but may be missing
        # from an older schema created by NexusmonDB.ensure_schema().
        cols = _table_cols(conn, "swarm_units")
        missing = {
            "generated_from": "TEXT DEFAULT ''",
            "unit_type": "TEXT DEFAULT ''",
        }
        for col, typedef in missing.items():
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE swarm_units ADD COLUMN {col} {typedef}")
                except Exception:
                    pass  # column already exists in some form

        conn.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _type_col(self) -> str:
        """Return the actual type column name used by the live table."""
        cols = _table_cols(self.db.conn, "swarm_units")
        # Prefer the spec name; fall back to legacy name.
        return "unit_type" if "unit_type" in cols else "type"

    def _auto_name(self, unit_type: str) -> str:
        """Return the next sequential name for *unit_type*, e.g. "Scout-03"."""
        type_col = self._type_col()
        cur = self.db.conn.execute(
            f"SELECT COUNT(*) FROM swarm_units WHERE {type_col} = ?",
            (unit_type,),
        )
        count = cur.fetchone()[0]
        label = unit_type.capitalize()
        return f"{label}-{(count + 1):02d}"

    def _insert_unit(
        self, unit_id: str, name: str, unit_type: str, generated_from: str = ""
    ) -> None:
        conn = self.db.conn
        now = _now()
        cols = _table_cols(conn, "swarm_units")

        # Build the column/value lists dynamically so we satisfy NOT NULL
        # constraints on BOTH the legacy ``type`` column and the spec's
        # ``unit_type`` column when both are present in the table.
        insert_cols = ["id", "name"]
        insert_vals: list = [unit_id, name]

        if "type" in cols:
            insert_cols.append("type")
            insert_vals.append(unit_type)
        if "unit_type" in cols:
            insert_cols.append("unit_type")
            insert_vals.append(unit_type)
        if "generated_from" in cols:
            insert_cols.append("generated_from")
            insert_vals.append(generated_from)
        insert_cols.append("created_at")
        insert_vals.append(now)

        placeholders = ", ".join(["?"] * len(insert_vals))
        col_str = ", ".join(insert_cols)
        conn.execute(
            f"INSERT INTO swarm_units ({col_str}) VALUES ({placeholders})",
            insert_vals,
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_unit(self, unit_type: str, generated_from: str = "") -> dict:
        """Create and persist a new swarm unit; return it as a dict."""
        unit_id = str(uuid.uuid4())
        name = self._auto_name(unit_type)
        self._insert_unit(unit_id, name, unit_type, generated_from)
        return self.get_unit(unit_id)

    def get_unit(self, unit_id: str) -> dict | None:
        """Fetch a single unit by *unit_id*; returns None if not found."""
        cur = self.db.conn.execute("SELECT * FROM swarm_units WHERE id = ?", (unit_id,))
        row = cur.fetchone()
        return _row_to_unit(row) if row else None

    def list_units(self, status: str = None) -> list[dict]:
        """Return all units, optionally filtered by *status*."""
        if status:
            cur = self.db.conn.execute(
                "SELECT * FROM swarm_units WHERE status = ?", (status,)
            )
        else:
            cur = self.db.conn.execute("SELECT * FROM swarm_units")
        return [_row_to_unit(row) for row in cur.fetchall()]

    def deploy_unit(self, unit_id: str) -> None:
        """Set a unit's status to ON_MISSION."""
        self.db.conn.execute(
            "UPDATE swarm_units SET status = 'ON_MISSION' WHERE id = ?", (unit_id,)
        )
        self.db.conn.commit()

    def recall_unit(self, unit_id: str) -> None:
        """Set a unit's status back to IDLE."""
        self.db.conn.execute(
            "UPDATE swarm_units SET status = 'IDLE' WHERE id = ?", (unit_id,)
        )
        self.db.conn.commit()

    def complete_mission(
        self, unit_id: str, success: bool, xp_gained: float = 10.0
    ) -> None:
        """Credit XP, handle level-up, increment counters, set status IDLE."""
        unit = self.get_unit(unit_id)
        if unit is None:
            return

        level = unit.get("level", 1) or 1
        xp = (unit.get("xp") or 0.0) + xp_gained

        # Level-up loop: threshold = current level * 100
        threshold = level * 100.0
        while xp >= threshold:
            xp -= threshold
            level += 1
            threshold = level * 100.0

        if success:
            self.db.conn.execute(
                "UPDATE swarm_units "
                "SET status = 'IDLE', xp = ?, level = ?, "
                "    missions_completed = missions_completed + 1 "
                "WHERE id = ?",
                (xp, level, unit_id),
            )
        else:
            self.db.conn.execute(
                "UPDATE swarm_units "
                "SET status = 'IDLE', xp = ?, level = ?, "
                "    missions_failed = missions_failed + 1 "
                "WHERE id = ?",
                (xp, level, unit_id),
            )
        self.db.conn.commit()

    def get_unit_count(self) -> int:
        """Return total number of units in the registry."""
        cur = self.db.conn.execute("SELECT COUNT(*) FROM swarm_units")
        return cur.fetchone()[0]

    def get_idle_count(self) -> int:
        """Return number of units currently IDLE."""
        cur = self.db.conn.execute(
            "SELECT COUNT(*) FROM swarm_units WHERE status = 'IDLE'"
        )
        return cur.fetchone()[0]

    def assign_lore(self, unit_id: str, lore: str) -> None:
        """Write *lore* into the unit's personal_lore field."""
        self.db.conn.execute(
            "UPDATE swarm_units SET personal_lore = ? WHERE id = ?", (lore, unit_id)
        )
        self.db.conn.commit()

    # ------------------------------------------------------------------
    # Seeding
    # ------------------------------------------------------------------

    def _seed(self) -> None:
        """Insert 3 starter units when the table is empty."""
        if self.get_unit_count() == 0:
            starters = [
                ("SCOUT", "Scout-01"),
                ("BUILDER", "Builder-01"),
                ("ANALYST", "Analyst-01"),
            ]
            for unit_type, name in starters:
                self._insert_unit(str(uuid.uuid4()), name, unit_type)


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_swarm = None


def get_swarm_engine() -> SwarmEngine:
    """Return (or lazily create) the module-level SwarmEngine singleton."""
    global _swarm
    if _swarm is None:
        _swarm = SwarmEngine()
    return _swarm
