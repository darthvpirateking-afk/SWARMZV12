# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/artifacts.py — Artifact vault, rarity system, and synergy."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from nexusmon.memory import get_db

# Artifact types
ARTIFACT_TYPES = [
    "BLUEPRINT",
    "KNOWLEDGE_BLOCK",
    "ABILITY",
    "EVOLUTION_TRIGGER",
    "SWARM_TEMPLATE",
    "MISSION_RESULT",
    "UI_MODULE",
    "SYSTEM_UPGRADE",
    "RESOURCE_BUNDLE",
    "COMPOSITE_ARTIFACT",
    "LORE_ENTRY",
    "WITNESSED_ARTIFACT",
]

# Rarity tiers (ordered)
RARITY_ORDER = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]

# Artifact slot counts per form
SLOT_COUNTS = {
    "ROOKIE": 2,
    "CHAMPION": 4,
    "ULTIMATE": 6,
    "MEGA": 8,
    "SOVEREIGN": 99,
}


def _ensure_tables() -> None:
    """Create the artifacts table if it does not exist; add entropy_score if missing."""
    conn = get_db().conn
    # The memory layer already creates 'artifacts' with column 'type'.
    # This CREATE TABLE IF NOT EXISTS is a no-op when that table already exists,
    # but will create a correct table in a fresh DB using the same 'type' column name.
    conn.execute("""CREATE TABLE IF NOT EXISTS artifacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            rarity TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            created_by TEXT DEFAULT 'NEXUSMON',
            created_at TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            metadata TEXT DEFAULT '{}',
            payload TEXT DEFAULT '{}',
            equipped_to TEXT,
            synergy_ids TEXT DEFAULT '[]',
            entropy_score REAL DEFAULT 0.0
        )""")
    # Safely add entropy_score for databases created before this module existed.
    try:
        conn.execute("ALTER TABLE artifacts ADD COLUMN entropy_score REAL DEFAULT 0.0")
    except Exception:
        pass  # Column already present
    conn.commit()


_ensure_tables()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_json_fields(d: dict) -> dict:
    """Deserialize JSON-encoded list/dict fields in an artifact row dict."""
    for field in ("tags", "metadata", "payload", "synergy_ids"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = [] if field in ("tags", "synergy_ids") else {}
    return d


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict with normalised field names.

    The underlying column is named 'type'; we expose it as 'artifact_type' to
    match the spec API while remaining compatible with the existing schema.
    """
    d = dict(row)
    # Rename 'type' -> 'artifact_type' at the API boundary
    if "type" in d:
        d["artifact_type"] = d.pop("type")
    return _parse_json_fields(d)


# ---------------------------------------------------------------------------
# ArtifactVault
# ---------------------------------------------------------------------------


class ArtifactVault:
    """Artifact vault: create, store, retrieve, and slot management."""

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        artifact_type: str,
        rarity: str = "COMMON",
        created_by: str = "NEXUSMON",
        tags: Optional[list] = None,
        metadata: Optional[dict] = None,
        payload: Optional[dict] = None,
    ) -> dict:
        """Insert a new artifact and return it as a dict."""
        artifact_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(tags or [])
        metadata_json = json.dumps(metadata or {})
        payload_json = json.dumps(payload or {})

        conn = get_db().conn
        conn.execute(
            """INSERT INTO artifacts
               (id, name, type, rarity, version, created_by, created_at,
                tags, metadata, payload, synergy_ids, entropy_score)
               VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, '[]', 0.0)""",
            (
                artifact_id,
                name,
                artifact_type,
                rarity,
                created_by,
                now,
                tags_json,
                metadata_json,
                payload_json,
            ),
        )
        conn.commit()
        return self.get(artifact_id)

    def equip(self, artifact_id: str, entity_id: str) -> None:
        """Set the equipped_to field for the artifact."""
        conn = get_db().conn
        conn.execute(
            "UPDATE artifacts SET equipped_to = ? WHERE id = ?",
            (entity_id, artifact_id),
        )
        conn.commit()

    def unequip(self, artifact_id: str) -> None:
        """Clear the equipped_to field for the artifact."""
        conn = get_db().conn
        conn.execute(
            "UPDATE artifacts SET equipped_to = NULL WHERE id = ?",
            (artifact_id,),
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get(self, artifact_id: str) -> Optional[dict]:
        """Return a single artifact by ID, or None if not found."""
        conn = get_db().conn
        cur = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row is not None else None

    def list_all(
        self,
        artifact_type: Optional[str] = None,
        rarity: Optional[str] = None,
        limit: int = 50,
    ) -> list:
        """Return up to *limit* artifacts, optionally filtered by type and/or rarity."""
        conn = get_db().conn
        query = "SELECT * FROM artifacts WHERE 1=1"
        params: list = []
        if artifact_type is not None:
            query += " AND type = ?"
            params.append(artifact_type)
        if rarity is not None:
            query += " AND rarity = ?"
            params.append(rarity)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur = conn.execute(query, params)
        return [_row_to_dict(row) for row in cur.fetchall()]

    def get_equipped(self, entity_id: str) -> list:
        """Return all artifacts currently equipped to *entity_id*."""
        conn = get_db().conn
        cur = conn.execute(
            "SELECT * FROM artifacts WHERE equipped_to = ?", (entity_id,)
        )
        return [_row_to_dict(row) for row in cur.fetchall()]

    def get_vault_size(self) -> int:
        """Return the total number of artifacts in the vault."""
        conn = get_db().conn
        cur = conn.execute("SELECT COUNT(*) FROM artifacts")
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Convenience factory methods
    # ------------------------------------------------------------------

    def create_witnessed(self, event_name: str, description: str, form: str) -> dict:
        """Create a MYTHIC WITNESSED_ARTIFACT commemorating a notable event.

        The artifact name is formatted as "The <event_name>" to give it a
        legendary character (e.g. "The First Awakening").
        """
        name = f"The {event_name}"
        slot_count = SLOT_COUNTS.get(form, 2)
        return self.create(
            name=name,
            artifact_type="WITNESSED_ARTIFACT",
            rarity="MYTHIC",
            created_by="NEXUSMON",
            tags=["witnessed", form.lower(), "auto-generated"],
            metadata={
                "form": form,
                "description": description,
                "slot_count": slot_count,
            },
            payload={
                "event_name": event_name,
                "description": description,
                "form_at_creation": form,
            },
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_vault: Optional[ArtifactVault] = None


def get_vault() -> ArtifactVault:
    """Return (or lazily create) the module-level ArtifactVault singleton."""
    global _vault
    if _vault is None:
        _vault = ArtifactVault()
    return _vault
