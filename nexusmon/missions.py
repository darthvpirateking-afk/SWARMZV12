# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/missions.py -- MissionEngine: mission lifecycle management.

Per NEXUSMON MASTER SPEC Part 7.

Mission types  : RESEARCH, BUILD, ANALYZE, PATROL, DRAFT, RAID, DISCOVERY, FORGE, EVOLUTION
Mission statuses: PENDING, DISPATCHED, COMPLETE, FAILED, CANCELLED

Schema compatibility note
-------------------------
NexusmonDB.ensure_schema() creates a ``missions`` table with legacy column
names (``name``, ``type``, ``assigned_units``, ``started_at``, ``outcome``).
This module adds the missing spec columns via ALTER TABLE and normalises all
reads into spec-conformant dicts (keys: ``title``, ``mission_type``,
``unit_id``, ``operator_id``, ``dispatched_at``, ``result``, ``notes``).
"""

import json
import random
import uuid
from datetime import datetime, timezone

from nexusmon.memory import get_db
from nexusmon.swarm import get_swarm_engine

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MISSION_TYPES = [
    "RESEARCH",
    "BUILD",
    "ANALYZE",
    "PATROL",
    "DRAFT",
    "RAID",
    "DISCOVERY",
    "FORGE",
    "EVOLUTION",
]
MISSION_STATUSES = ["PENDING", "DISPATCHED", "COMPLETE", "FAILED", "CANCELLED"]

# ---------------------------------------------------------------------------
# Loot generation
# ---------------------------------------------------------------------------


def generate_loot(mission_type: str, difficulty: int, unit_level: int) -> list:
    """Generate loot for a completed mission.

    Returns a list of ``{type, rarity, name}`` dicts.

    Probability table:
      difficulty 1-3  : COMMON result + 30 % UNCOMMON knowledge_block
      difficulty 4-6  : COMMON result + 50 % UNCOMMON / 20 % RARE
      difficulty 7-10 : UNCOMMON result + 40 % RARE / 10 % EPIC
    """
    loot = [
        {
            "type": "MISSION_RESULT",
            "rarity": "COMMON",
            "name": f"{mission_type} Report",
        }
    ]
    roll = random.random()
    if difficulty <= 3:
        if roll < 0.30:
            loot.append(
                {
                    "type": "KNOWLEDGE_BLOCK",
                    "rarity": "UNCOMMON",
                    "name": "Intelligence Fragment",
                }
            )
    elif difficulty <= 6:
        if roll < 0.50:
            loot.append(
                {
                    "type": "KNOWLEDGE_BLOCK",
                    "rarity": "UNCOMMON",
                    "name": "Intelligence Fragment",
                }
            )
        elif roll < 0.70:
            loot.append(
                {
                    "type": "KNOWLEDGE_BLOCK",
                    "rarity": "RARE",
                    "name": "Deep Intelligence",
                }
            )
    else:
        if roll < 0.40:
            loot.append(
                {
                    "type": "KNOWLEDGE_BLOCK",
                    "rarity": "RARE",
                    "name": "Deep Intelligence",
                }
            )
        elif roll < 0.50:
            loot.append(
                {
                    "type": "ABILITY",
                    "rarity": "EPIC",
                    "name": "Ability Fragment",
                }
            )
    return loot


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _table_cols(conn, table: str) -> set:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _row_to_mission(row) -> dict:
    """Normalise a DB row to a spec-conformant mission dict.

    Legacy column mappings:
      name          -> title
      type          -> mission_type
      assigned_units (JSON list) -> unit_id (first element or empty str)
      started_at    -> dispatched_at
      outcome       -> result
    """
    d = dict(row)

    # ---- title ----
    if "title" not in d:
        d["title"] = d.pop("name", "")
    elif "name" in d:
        d.pop("name", None)

    # ---- mission_type ----
    if "mission_type" not in d:
        d["mission_type"] = d.pop("type", "")
    elif "type" in d:
        d.pop("type", None)

    # ---- unit_id ----
    if "unit_id" not in d:
        raw = d.pop("assigned_units", "[]")
        try:
            lst = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except Exception:
            lst = []
        d["unit_id"] = lst[0] if lst else ""
    elif "assigned_units" in d:
        d.pop("assigned_units", None)

    # ---- dispatched_at ----
    if "dispatched_at" not in d:
        d["dispatched_at"] = d.pop("started_at", None)
    elif "started_at" in d:
        d.pop("started_at", None)

    # ---- result ----
    if "result" not in d:
        d["result"] = d.pop("outcome", "")
    elif "outcome" in d:
        d.pop("outcome", None)

    # ---- ensure optional keys exist ----
    d.setdefault("operator_id", "op-001")
    d.setdefault("notes", "")

    # ---- deserialise loot ----
    loot_raw = d.get("loot", "[]")
    if isinstance(loot_raw, str):
        try:
            d["loot"] = json.loads(loot_raw)
        except Exception:
            d["loot"] = []

    return d


# ---------------------------------------------------------------------------
# MissionEngine
# ---------------------------------------------------------------------------


class MissionEngine:
    """Manages missions in the NexusmonDB ``missions`` table."""

    def __init__(self) -> None:
        self.db = get_db()
        self._ensure_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        """Create the missions table (if absent) and add any missing columns."""
        conn = self.db.conn

        # Primary CREATE — only runs when the table does not yet exist.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                mission_type TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                status TEXT DEFAULT 'PENDING',
                unit_id TEXT,
                operator_id TEXT DEFAULT 'op-001',
                created_at TEXT NOT NULL,
                dispatched_at TEXT,
                completed_at TEXT,
                loot TEXT DEFAULT '[]',
                result TEXT DEFAULT '',
                xp_reward REAL DEFAULT 10.0,
                notes TEXT DEFAULT ''
            )
            """
        )

        # Retroactively add columns missing from the legacy schema.
        cols = _table_cols(conn, "missions")
        missing = {
            "title": "TEXT DEFAULT ''",
            "mission_type": "TEXT DEFAULT ''",
            "unit_id": "TEXT DEFAULT ''",
            "operator_id": "TEXT DEFAULT 'op-001'",
            "dispatched_at": "TEXT",
            "result": "TEXT DEFAULT ''",
            "notes": "TEXT DEFAULT ''",
        }
        for col, typedef in missing.items():
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE missions ADD COLUMN {col} {typedef}")
                except Exception:
                    pass

        conn.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _title_col(self) -> str:
        cols = _table_cols(self.db.conn, "missions")
        return "title" if "title" in cols else "name"

    def _type_col(self) -> str:
        cols = _table_cols(self.db.conn, "missions")
        return "mission_type" if "mission_type" in cols else "type"

    def _dispatched_col(self) -> str:
        cols = _table_cols(self.db.conn, "missions")
        return "dispatched_at" if "dispatched_at" in cols else "started_at"

    def _result_col(self) -> str:
        cols = _table_cols(self.db.conn, "missions")
        return "result" if "result" in cols else "outcome"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_mission(
        self,
        title: str,
        mission_type: str,
        difficulty: int = 1,
        operator_id: str = "op-001",
    ) -> dict:
        """Create and persist a new mission; return it as a dict."""
        mission_id = str(uuid.uuid4())
        now = _now()
        conn = self.db.conn
        cols = _table_cols(conn, "missions")

        # Build the column/value lists dynamically so we satisfy NOT NULL
        # constraints on BOTH legacy columns (name, type) and spec columns
        # (title, mission_type) when both variants are present.
        insert_cols: list = ["id", "difficulty", "created_at"]
        insert_vals: list = [mission_id, difficulty, now]

        # title / name
        if "name" in cols:
            insert_cols.append("name")
            insert_vals.append(title)
        if "title" in cols:
            insert_cols.append("title")
            insert_vals.append(title)

        # mission_type / type
        if "type" in cols:
            insert_cols.append("type")
            insert_vals.append(mission_type)
        if "mission_type" in cols:
            insert_cols.append("mission_type")
            insert_vals.append(mission_type)

        if "operator_id" in cols:
            insert_cols.append("operator_id")
            insert_vals.append(operator_id)

        # assigned_units may have NOT NULL — supply empty JSON list
        if "assigned_units" in cols:
            insert_cols.append("assigned_units")
            insert_vals.append("[]")

        placeholders = ", ".join(["?"] * len(insert_vals))
        col_list = ", ".join(insert_cols)

        conn.execute(
            f"INSERT INTO missions ({col_list}) VALUES ({placeholders})",
            insert_vals,
        )
        conn.commit()
        return self._fetch(mission_id)

    def dispatch(self, mission_id: str, unit_id: str) -> dict:
        """Assign *unit_id* to *mission_id*, set DISPATCHED, deploy unit."""
        conn = self.db.conn
        now = _now()
        cols = _table_cols(conn, "missions")

        # Build SET clause dynamically to satisfy all present columns.
        set_parts = ["status = 'DISPATCHED'"]
        set_vals: list = []

        if "unit_id" in cols:
            set_parts.append("unit_id = ?")
            set_vals.append(unit_id)
        if "assigned_units" in cols:
            set_parts.append("assigned_units = ?")
            set_vals.append(json.dumps([unit_id]))
        if "dispatched_at" in cols:
            set_parts.append("dispatched_at = ?")
            set_vals.append(now)
        if "started_at" in cols:
            set_parts.append("started_at = ?")
            set_vals.append(now)

        set_vals.append(mission_id)
        set_clause = ", ".join(set_parts)
        conn.execute(
            f"UPDATE missions SET {set_clause} WHERE id = ?",
            set_vals,
        )
        conn.commit()

        get_swarm_engine().deploy_unit(unit_id)
        return self._fetch(mission_id)

    def complete(self, mission_id: str, success: bool = True) -> dict:
        """Finalise a mission: generate loot, update unit, set terminal status."""
        mission = self._fetch(mission_id)
        if mission is None:
            return {}

        unit_id = mission.get("unit_id") or ""
        unit_level = 1
        if unit_id:
            unit = get_swarm_engine().get_unit(unit_id)
            if unit:
                unit_level = unit.get("level", 1) or 1

        loot = generate_loot(
            mission.get("mission_type", "RESEARCH"),
            mission.get("difficulty", 1),
            unit_level,
        )
        loot_json = json.dumps(loot)
        new_status = "COMPLETE" if success else "FAILED"
        now = _now()

        cols = _table_cols(self.db.conn, "missions")
        set_parts = ["status = ?", "loot = ?", "completed_at = ?"]
        set_vals: list = [new_status, loot_json, now]

        if "result" in cols:
            set_parts.append("result = ?")
            set_vals.append(new_status)
        if "outcome" in cols:
            set_parts.append("outcome = ?")
            set_vals.append(new_status)

        set_vals.append(mission_id)
        set_clause = ", ".join(set_parts)
        self.db.conn.execute(
            f"UPDATE missions SET {set_clause} WHERE id = ?",
            set_vals,
        )
        self.db.conn.commit()

        xp_reward = mission.get("xp_reward", 10.0) or 10.0
        if unit_id:
            get_swarm_engine().complete_mission(unit_id, success, xp_gained=xp_reward)

        # Wire loot → artifact vault
        mission_type = mission.get("mission_type", "RESEARCH")
        difficulty = mission.get("difficulty", 1)
        try:
            from nexusmon.artifacts import get_vault
            from nexusmon.entity import get_entity

            vault = get_vault()
            artifact_ids = []
            for loot_item in loot:
                artifact = vault.create(
                    name=loot_item.get("name", "Mission Drop"),
                    artifact_type=loot_item.get("type", "MISSION_RESULT"),
                    rarity=loot_item.get("rarity", "COMMON"),
                    created_by="mission",
                    tags=["mission-loot", mission_type.lower()],
                    metadata={"mission_id": mission_id, "difficulty": difficulty},
                )
                artifact_ids.append(artifact["id"])

            # Award evolution XP to entity
            entity = get_entity()
            entity.add_evolution_xp(xp_reward)
            entity.increment_interaction()
        except Exception:
            artifact_ids = []

        return self._fetch(mission_id)

    def get_active(self) -> list:
        """Return all DISPATCHED missions."""
        cur = self.db.conn.execute("SELECT * FROM missions WHERE status = 'DISPATCHED'")
        return [_row_to_mission(row) for row in cur.fetchall()]

    def get_pending(self) -> list:
        """Return all PENDING missions."""
        cur = self.db.conn.execute("SELECT * FROM missions WHERE status = 'PENDING'")
        return [_row_to_mission(row) for row in cur.fetchall()]

    def get_all(self, limit: int = 20) -> list:
        """Return recent missions (newest first), up to *limit* rows."""
        cur = self.db.conn.execute(
            "SELECT * FROM missions ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [_row_to_mission(row) for row in cur.fetchall()]

    def get_stats(self) -> dict:
        """Return aggregate statistics for all missions."""
        conn = self.db.conn
        total = conn.execute("SELECT COUNT(*) FROM missions").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM missions WHERE status = 'COMPLETE'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM missions WHERE status = 'FAILED'"
        ).fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM missions WHERE status = 'DISPATCHED'"
        ).fetchone()[0]
        finished = completed + failed
        success_rate = (completed / finished) if finished > 0 else 0.0
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "active": active,
            "success_rate": round(success_rate, 4),
        }

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _fetch(self, mission_id: str) -> dict | None:
        cur = self.db.conn.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
        row = cur.fetchone()
        return _row_to_mission(row) if row else None


# ---------------------------------------------------------------------------
# Module singleton
# ---------------------------------------------------------------------------

_missions = None


def get_mission_engine() -> MissionEngine:
    """Return (or lazily create) the module-level MissionEngine singleton."""
    global _missions
    if _missions is None:
        _missions = MissionEngine()
    return _missions
