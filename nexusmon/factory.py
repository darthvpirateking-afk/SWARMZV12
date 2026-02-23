# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/factory.py — Factory engine, recipes, and production queue."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from nexusmon.memory import get_db

# ---------------------------------------------------------------------------
# Starter recipes (seeded once on first run)
# ---------------------------------------------------------------------------

STARTER_RECIPES = [
    {
        "id": "recipe-001",
        "name": "Knowledge Synthesis",
        "input_types": ["KNOWLEDGE_BLOCK", "KNOWLEDGE_BLOCK"],
        "input_rarity_min": "COMMON",
        "output_type": "COMPOSITE_ARTIFACT",
        "output_rarity": "UNCOMMON",
        "operation": "Merge",
        "time_seconds": 30,
        "unlock_condition": "default",
    },
    {
        "id": "recipe-002",
        "name": "Blueprint Upgrade",
        "input_types": ["BLUEPRINT", "RESOURCE_BUNDLE"],
        "input_rarity_min": "COMMON",
        "output_type": "BLUEPRINT",
        "output_rarity": "RARE",
        "operation": "Upgrade",
        "time_seconds": 60,
        "unlock_condition": "default",
    },
    {
        "id": "recipe-003",
        "name": "Ability Fragment",
        "input_types": ["MISSION_RESULT", "MISSION_RESULT", "MISSION_RESULT"],
        "input_rarity_min": "UNCOMMON",
        "output_type": "ABILITY",
        "output_rarity": "RARE",
        "operation": "Synthesize",
        "time_seconds": 120,
        "unlock_condition": "default",
    },
]


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------


def _ensure_tables() -> None:
    """Create factory_recipes if it does not exist.

    factory_jobs is already created by nexusmon.memory; we do not recreate it
    but we do ensure factory_recipes exists so recipes can be stored.
    """
    conn = get_db().conn
    conn.execute("""CREATE TABLE IF NOT EXISTS factory_recipes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            input_types TEXT NOT NULL,
            input_rarity_min TEXT DEFAULT 'COMMON',
            output_type TEXT NOT NULL,
            output_rarity TEXT NOT NULL,
            operation TEXT NOT NULL,
            resource_cost TEXT DEFAULT '{}',
            time_seconds INTEGER DEFAULT 60,
            unlock_condition TEXT DEFAULT 'default',
            synergy_bonus TEXT
        )""")
    conn.commit()


def _ensure_recipes() -> None:
    """Seed STARTER_RECIPES into factory_recipes if the table is empty."""
    conn = get_db().conn
    cur = conn.execute("SELECT COUNT(*) FROM factory_recipes")
    if cur.fetchone()[0] > 0:
        return  # Already seeded

    for recipe in STARTER_RECIPES:
        conn.execute(
            """INSERT INTO factory_recipes
               (id, name, input_types, input_rarity_min, output_type, output_rarity,
                operation, resource_cost, time_seconds, unlock_condition, synergy_bonus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                recipe["id"],
                recipe["name"],
                json.dumps(recipe.get("input_types", [])),
                recipe.get("input_rarity_min", "COMMON"),
                recipe["output_type"],
                recipe["output_rarity"],
                recipe["operation"],
                json.dumps(recipe.get("resource_cost", {})),
                recipe.get("time_seconds", 60),
                recipe.get("unlock_condition", "default"),
                recipe.get("synergy_bonus"),
            ),
        )
    conn.commit()


_ensure_tables()
_ensure_recipes()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_recipe_row(row) -> dict:
    """Convert a sqlite3.Row for a recipe to a plain dict."""
    d = dict(row)
    for field in ("input_types", "resource_cost"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = []
    return d


def _parse_job_row(row) -> dict:
    """Convert a sqlite3.Row for a factory job to a plain dict."""
    d = dict(row)
    if "input_artifact_ids" in d and isinstance(d["input_artifact_ids"], str):
        try:
            d["input_artifact_ids"] = json.loads(d["input_artifact_ids"])
        except (json.JSONDecodeError, TypeError):
            d["input_artifact_ids"] = []
    return d


# ---------------------------------------------------------------------------
# FactoryEngine
# ---------------------------------------------------------------------------


class FactoryEngine:
    """Manages factory recipes, job queue, and production tracking."""

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Return a snapshot of factory state.

        Returns a dict with keys:
            status          -- 'RUNNING' | 'QUEUED' | 'IDLE'
            current_job     -- the actively RUNNING job dict, or None
            queued_count    -- number of jobs in QUEUED state
            completed_today -- jobs completed since UTC midnight today
            total_produced  -- all-time COMPLETE job count
        """
        conn = get_db().conn

        cur = conn.execute(
            "SELECT * FROM factory_jobs WHERE status = 'RUNNING' LIMIT 1"
        )
        running_row = cur.fetchone()
        current_job = _parse_job_row(running_row) if running_row is not None else None

        cur = conn.execute("SELECT COUNT(*) FROM factory_jobs WHERE status = 'QUEUED'")
        queued_count: int = cur.fetchone()[0]

        today_prefix = datetime.now(timezone.utc).date().isoformat()
        cur = conn.execute(
            "SELECT COUNT(*) FROM factory_jobs WHERE status = 'COMPLETE' AND completed_at LIKE ?",
            (f"{today_prefix}%",),
        )
        completed_today: int = cur.fetchone()[0]

        cur = conn.execute(
            "SELECT COUNT(*) FROM factory_jobs WHERE status = 'COMPLETE'"
        )
        total_produced: int = cur.fetchone()[0]

        if current_job is not None:
            status = "RUNNING"
        elif queued_count > 0:
            status = "QUEUED"
        else:
            status = "IDLE"

        return {
            "status": status,
            "current_job": current_job,
            "queued_count": queued_count,
            "completed_today": completed_today,
            "total_produced": total_produced,
        }

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def queue_job(self, recipe_id: str) -> str:
        """Add a new job to the queue for *recipe_id*; return the job ID.

        The existing factory_jobs schema requires recipe_name NOT NULL, so we
        look up the recipe name before inserting.
        """
        recipe = self.get_recipe(recipe_id)
        if recipe is None:
            raise ValueError(f"Recipe not found: {recipe_id!r}")

        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn = get_db().conn
        conn.execute(
            """INSERT INTO factory_jobs
               (id, recipe_id, recipe_name, status, queued_at)
               VALUES (?, ?, ?, 'QUEUED', ?)""",
            (job_id, recipe_id, recipe["name"], now),
        )
        conn.commit()
        return job_id

    def get_queue(self) -> list:
        """Return all jobs currently in QUEUED state."""
        conn = get_db().conn
        cur = conn.execute(
            "SELECT * FROM factory_jobs WHERE status = 'QUEUED' ORDER BY queued_at ASC"
        )
        return [_parse_job_row(row) for row in cur.fetchall()]

    def complete_job(self, job_id: str, output_artifact_id: str) -> None:
        """Mark a job as COMPLETE and record its output artifact ID."""
        now = datetime.now(timezone.utc).isoformat()
        conn = get_db().conn
        conn.execute(
            """UPDATE factory_jobs
               SET status = 'COMPLETE', output_artifact_id = ?, completed_at = ?
               WHERE id = ?""",
            (output_artifact_id, now, job_id),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Recipe access
    # ------------------------------------------------------------------

    def get_recipes(self) -> list:
        """Return all factory recipes."""
        conn = get_db().conn
        cur = conn.execute("SELECT * FROM factory_recipes ORDER BY id")
        return [_parse_recipe_row(row) for row in cur.fetchall()]

    def get_recipe(self, recipe_id: str) -> Optional[dict]:
        """Return a single recipe by ID, or None if not found."""
        conn = get_db().conn
        cur = conn.execute("SELECT * FROM factory_recipes WHERE id = ?", (recipe_id,))
        row = cur.fetchone()
        return _parse_recipe_row(row) if row is not None else None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_factory: Optional[FactoryEngine] = None


def get_factory() -> FactoryEngine:
    """Return (or lazily create) the module-level FactoryEngine singleton."""
    global _factory
    if _factory is None:
        _factory = FactoryEngine()
    return _factory
