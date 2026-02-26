# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/oig/graph.py -- SQLite-native temporal knowledge graph for the OIG.

Implements Graphiti's bi-temporal model natively in SQLite:
- t_valid_from / t_valid_to: when the fact was true in reality (NULL = still valid)
- t_ingested: when NEXUSMON learned this fact

Conflict resolution: inserting a fact with the same (subject, predicate, fact_type)
as an existing active fact invalidates the old one (sets t_valid_to) and inserts a
new active edge. The full history is always queryable.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_iso(dt: datetime) -> str:
    return dt.isoformat()


class TemporalGraph:
    """SQLite-native temporal knowledge graph.

    All writes go through upsert_fact() which handles conflict resolution.
    Never use raw inserts into oig_edges from outside this class.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    # ── Schema ────────────────────────────────────────────────────────────────

    def ensure_tables(self) -> None:
        """Create OIG tables and indexes if they don't exist."""
        self.conn.executescript(
            "CREATE TABLE IF NOT EXISTS oig_nodes ("
            "id TEXT PRIMARY KEY, "
            "entity_type TEXT NOT NULL, "
            "entity_id TEXT NOT NULL, "
            "label TEXT NOT NULL, "
            "properties TEXT DEFAULT '{}', "
            "created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now'))); "
            #
            "CREATE TABLE IF NOT EXISTS oig_edges ("
            "id TEXT PRIMARY KEY, "
            "subject_id TEXT NOT NULL, "
            "predicate TEXT NOT NULL, "
            "object_id TEXT NOT NULL, "
            "t_valid_from TEXT NOT NULL, "
            "t_valid_to TEXT DEFAULT NULL, "
            "t_ingested TEXT NOT NULL DEFAULT (datetime('now')), "
            "confidence REAL NOT NULL DEFAULT 0.5, "
            "source TEXT NOT NULL DEFAULT 'behavioral_inference', "
            "fact_type TEXT NOT NULL DEFAULT 'general', "
            "metadata TEXT DEFAULT '{}'); "
            #
            "CREATE TABLE IF NOT EXISTS oig_patterns ("
            "id TEXT PRIMARY KEY, "
            "operator_id TEXT NOT NULL, "
            "pattern_type TEXT NOT NULL, "
            "description TEXT NOT NULL, "
            "evidence TEXT DEFAULT '[]', "
            "first_seen TEXT NOT NULL, "
            "last_seen TEXT NOT NULL, "
            "occurrence_count INTEGER DEFAULT 1, "
            "confidence REAL NOT NULL DEFAULT 0.5); "
            #
            "CREATE TABLE IF NOT EXISTS oig_epochs ("
            "id TEXT PRIMARY KEY, "
            "operator_id TEXT NOT NULL, "
            "name TEXT NOT NULL, "
            "start_time TEXT NOT NULL, "
            "end_time TEXT DEFAULT NULL, "
            "defining_characteristic TEXT DEFAULT '', "
            "missions_completed INTEGER DEFAULT 0, "
            "fact_changes INTEGER DEFAULT 0, "
            "mood_signature TEXT DEFAULT 'neutral', "
            "growth_areas TEXT DEFAULT '[]'); "
            #
            "CREATE INDEX IF NOT EXISTS idx_oig_edges_subject ON oig_edges(subject_id); "
            "CREATE INDEX IF NOT EXISTS idx_oig_edges_predicate ON oig_edges(predicate); "
            "CREATE INDEX IF NOT EXISTS idx_oig_edges_valid ON oig_edges(t_valid_from, t_valid_to); "
            "CREATE INDEX IF NOT EXISTS idx_oig_edges_fact_type ON oig_edges(fact_type); "
            "CREATE INDEX IF NOT EXISTS idx_oig_edges_confidence ON oig_edges(confidence); "
            "CREATE INDEX IF NOT EXISTS idx_oig_patterns_operator ON oig_patterns(operator_id); "
            "CREATE INDEX IF NOT EXISTS idx_oig_epochs_operator ON oig_epochs(operator_id); "
            "CREATE INDEX IF NOT EXISTS idx_oig_nodes_entity ON oig_nodes(entity_type, entity_id); "
        )
        self.conn.commit()

    # ── Nodes ─────────────────────────────────────────────────────────────────

    def upsert_node(
        self,
        entity_type: str,
        entity_id: str,
        label: str,
        properties: dict | None = None,
    ) -> str:
        """Create or update a node. Returns the node id."""
        now = _now_iso()
        props_json = json.dumps(properties or {})
        # Check if node exists
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM oig_nodes WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        row = cur.fetchone()
        if row:
            node_id = row["id"]
            self.conn.execute(
                "UPDATE oig_nodes SET label = ?, properties = ?, updated_at = ? WHERE id = ?",
                (label, props_json, now, node_id),
            )
        else:
            node_id = str(uuid4())
            self.conn.execute(
                "INSERT INTO oig_nodes (id, entity_type, entity_id, label, properties, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (node_id, entity_type, entity_id, label, props_json, now, now),
            )
        self.conn.commit()
        return node_id

    def get_node(self, entity_type: str, entity_id: str) -> dict | None:
        """Return node dict or None if not found."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM oig_nodes WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["properties"] = json.loads(d.get("properties") or "{}")
        except Exception:
            d["properties"] = {}
        return d

    def get_or_create_node(
        self,
        entity_type: str,
        entity_id: str,
        label: str,
        properties: dict | None = None,
    ) -> str:
        """Return existing node id or create a new one."""
        existing = self.get_node(entity_type, entity_id)
        if existing:
            return existing["id"]
        return self.upsert_node(entity_type, entity_id, label, properties)

    # ── Edges / Facts ─────────────────────────────────────────────────────────

    def upsert_fact(
        self,
        subject_id: str,
        predicate: str,
        object_id: str,
        confidence: float,
        source: str = "behavioral_inference",
        fact_type: str = "general",
        metadata: dict | None = None,
    ) -> str:
        """Insert a new temporal fact edge with conflict resolution.

        Conflict resolution logic:
        1. Check for an existing active edge with same (subject_id, predicate, fact_type)
        2. If found and object_id DIFFERS: set t_valid_to = now, then create new edge
        3. If found and object_id is SAME: update confidence if new is higher, refresh t_ingested
        4. If not found: create new edge

        Returns the edge id (new or existing).
        """
        now = _now_iso()
        meta_json = json.dumps(metadata or {})
        cur = self.conn.cursor()

        # Find existing active edge with same (subject, predicate, fact_type)
        cur.execute(
            "SELECT id, object_id, confidence FROM oig_edges "
            "WHERE subject_id = ? AND predicate = ? AND fact_type = ? AND t_valid_to IS NULL",
            (subject_id, predicate, fact_type),
        )
        existing = cur.fetchone()

        if existing:
            if existing["object_id"] == object_id:
                # Same fact — update confidence if new is higher, refresh ingestion time
                if confidence > existing["confidence"]:
                    self.conn.execute(
                        "UPDATE oig_edges SET confidence = ?, t_ingested = ?, metadata = ? WHERE id = ?",
                        (confidence, now, meta_json, existing["id"]),
                    )
                    self.conn.commit()
                return existing["id"]
            else:
                # Conflicting fact — invalidate old edge
                self.conn.execute(
                    "UPDATE oig_edges SET t_valid_to = ? WHERE id = ?",
                    (now, existing["id"]),
                )

        # Create new active edge
        edge_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO oig_edges "
            "(id, subject_id, predicate, object_id, t_valid_from, t_valid_to, t_ingested, "
            " confidence, source, fact_type, metadata) "
            "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)",
            (
                edge_id,
                subject_id,
                predicate,
                object_id,
                now,
                now,
                confidence,
                source,
                fact_type,
                meta_json,
            ),
        )
        self.conn.commit()
        return edge_id

    def get_facts(
        self,
        subject_id: str | None = None,
        predicate: str | None = None,
        fact_type: str | None = None,
        at_time: str | None = None,
        min_confidence: float = 0.0,
        active_only: bool = True,
        limit: int = 100,
    ) -> list[dict]:
        """Query facts with optional temporal and type filters.

        If at_time is set: return facts valid at that point in time.
        If active_only: return only currently valid facts (t_valid_to IS NULL).
        """
        conditions = []
        params: list = []

        if subject_id:
            conditions.append("e.subject_id = ?")
            params.append(subject_id)
        if predicate:
            conditions.append("e.predicate = ?")
            params.append(predicate)
        if fact_type:
            conditions.append("e.fact_type = ?")
            params.append(fact_type)
        if min_confidence > 0.0:
            conditions.append("e.confidence >= ?")
            params.append(min_confidence)

        if at_time:
            conditions.append("e.t_valid_from <= ?")
            params.append(at_time)
            conditions.append("(e.t_valid_to IS NULL OR e.t_valid_to > ?)")
            params.append(at_time)
        elif active_only:
            conditions.append("e.t_valid_to IS NULL")

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = (
            f"SELECT e.*, n_s.label AS subject_label, n_o.label AS object_label "
            f"FROM oig_edges e "
            f"LEFT JOIN oig_nodes n_s ON e.subject_id = n_s.id "
            f"LEFT JOIN oig_nodes n_o ON e.object_id = n_o.id "
            f"{where} "
            f"ORDER BY e.t_valid_from DESC "
            f"LIMIT ?"
        )
        params.append(limit)
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            result.append(d)
        return result

    def invalidate_fact(self, edge_id: str) -> None:
        """Manually invalidate a fact by setting t_valid_to = now."""
        self.conn.execute(
            "UPDATE oig_edges SET t_valid_to = ? WHERE id = ?",
            (_now_iso(), edge_id),
        )
        self.conn.commit()

    # ── Temporal Queries ──────────────────────────────────────────────────────

    def get_fact_timeline(self, subject_id: str, predicate: str) -> list[dict]:
        """Return the full temporal history of a specific fact/relationship.

        Returns all edges (active and invalidated) in chronological order.
        This answers "how has X changed over time?" — the killer feature of the OIG.
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT e.*, n_s.label AS subject_label, n_o.label AS object_label "
            "FROM oig_edges e "
            "LEFT JOIN oig_nodes n_s ON e.subject_id = n_s.id "
            "LEFT JOIN oig_nodes n_o ON e.object_id = n_o.id "
            "WHERE e.subject_id = ? AND e.predicate = ? "
            "ORDER BY e.t_valid_from ASC",
            (subject_id, predicate),
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["metadata"] = json.loads(d.get("metadata") or "{}")
            except Exception:
                d["metadata"] = {}
            result.append(d)
        return result

    def get_operator_snapshot(
        self, operator_id: str, at_time: str | None = None
    ) -> dict:
        """Reconstruct the full operator state at a given point in time.

        If at_time is None, returns current state.
        Returns dict with: identity, values, emotions, expertise, goals,
                           patterns, bond_metrics, current_epoch
        """
        # Get operator node id
        node = self.get_node("operator", operator_id)
        if not node:
            return {}
        subject_id = node["id"]

        kwargs: dict = dict(
            subject_id=subject_id, at_time=at_time, active_only=(at_time is None)
        )

        return {
            "identity": self.get_facts(predicate="is_named", **kwargs)
            + self.get_facts(predicate="communicates_as", **kwargs)
            + self.get_facts(predicate="thinks_as", **kwargs),
            "values": self.get_facts(fact_type="value", **kwargs),
            "emotions": self.get_facts(fact_type="emotion", **kwargs),
            "expertise": self.get_facts(fact_type="expertise", **kwargs),
            "goals": self.get_facts(fact_type="goal", **kwargs),
            "preferences": self.get_facts(fact_type="preference", **kwargs),
            "corrections": self.get_facts(fact_type="correction", **kwargs),
            "patterns": self.get_patterns(operator_id),
            "bond_metrics": self.compute_bond_metrics(operator_id),
            "current_epoch": self._get_current_epoch(operator_id),
        }

    def get_evolution_between(self, operator_id: str, t_start: str, t_end: str) -> dict:
        """Return all facts that changed between t_start and t_end.

        Returns: { added: [...], invalidated: [...] }
        """
        node = self.get_node("operator", operator_id)
        if not node:
            return {"added": [], "invalidated": []}
        subject_id = node["id"]
        cur = self.conn.cursor()

        # Facts added in window
        cur.execute(
            "SELECT e.*, n_o.label AS object_label "
            "FROM oig_edges e "
            "LEFT JOIN oig_nodes n_o ON e.object_id = n_o.id "
            "WHERE e.subject_id = ? AND e.t_valid_from >= ? AND e.t_valid_from <= ?",
            (subject_id, t_start, t_end),
        )
        added = [dict(r) for r in cur.fetchall()]

        # Facts invalidated in window
        cur.execute(
            "SELECT e.*, n_o.label AS object_label "
            "FROM oig_edges e "
            "LEFT JOIN oig_nodes n_o ON e.object_id = n_o.id "
            "WHERE e.subject_id = ? AND e.t_valid_to >= ? AND e.t_valid_to <= ?",
            (subject_id, t_start, t_end),
        )
        invalidated = [dict(r) for r in cur.fetchall()]

        return {"added": added, "invalidated": invalidated}

    def search(
        self, query: str, limit: int = 10, min_confidence: float = 0.0
    ) -> list[dict]:
        """Keyword search over node labels and edge predicates."""
        pattern = f"%{query.lower()}%"
        cur = self.conn.cursor()
        cur.execute(
            "SELECT e.*, n_s.label AS subject_label, n_o.label AS object_label "
            "FROM oig_edges e "
            "LEFT JOIN oig_nodes n_s ON e.subject_id = n_s.id "
            "LEFT JOIN oig_nodes n_o ON e.object_id = n_o.id "
            "WHERE e.t_valid_to IS NULL "
            "  AND e.confidence >= ? "
            "  AND (LOWER(n_s.label) LIKE ? OR LOWER(n_o.label) LIKE ? "
            "       OR LOWER(e.predicate) LIKE ? OR LOWER(e.metadata) LIKE ?) "
            "ORDER BY e.confidence DESC "
            "LIMIT ?",
            (min_confidence, pattern, pattern, pattern, pattern, limit),
        )
        return [dict(r) for r in cur.fetchall()]

    # ── Patterns ──────────────────────────────────────────────────────────────

    def record_pattern(
        self,
        operator_id: str,
        pattern_type: str,
        description: str,
        evidence: list[str],
        confidence: float = 0.5,
    ) -> str:
        """Upsert a behavioral pattern.

        If a pattern with the same (operator_id, pattern_type, description) exists:
        increment occurrence_count, update last_seen, append evidence, recalculate confidence.
        Otherwise create a new pattern entry.
        Returns the pattern id.
        """
        now = _now_iso()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, occurrence_count, evidence, confidence "
            "FROM oig_patterns WHERE operator_id = ? AND pattern_type = ? AND description = ?",
            (operator_id, pattern_type, description),
        )
        row = cur.fetchone()

        if row:
            pattern_id = row["id"]
            new_count = row["occurrence_count"] + 1
            # Append new evidence (keep last 20 unique items)
            existing_ev: list = []
            try:
                existing_ev = json.loads(row["evidence"] or "[]")
            except Exception:
                pass
            merged = list(dict.fromkeys(existing_ev + evidence))[-20:]
            # Average confidence toward new value (weighted by occurrence)
            old_conf = row["confidence"]
            new_conf = min(
                1.0, (old_conf * row["occurrence_count"] + confidence) / new_count
            )
            self.conn.execute(
                "UPDATE oig_patterns SET occurrence_count = ?, last_seen = ?, "
                "evidence = ?, confidence = ? WHERE id = ?",
                (new_count, now, json.dumps(merged), new_conf, pattern_id),
            )
            self.conn.commit()
            return pattern_id

        pattern_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO oig_patterns "
            "(id, operator_id, pattern_type, description, evidence, first_seen, last_seen, occurrence_count, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (
                pattern_id,
                operator_id,
                pattern_type,
                description,
                json.dumps(evidence[-20:]),
                now,
                now,
                confidence,
            ),
        )
        self.conn.commit()
        return pattern_id

    def get_patterns(
        self,
        operator_id: str,
        pattern_type: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[dict]:
        """Return patterns for an operator, sorted by occurrence_count * confidence."""
        cur = self.conn.cursor()
        if pattern_type:
            cur.execute(
                "SELECT * FROM oig_patterns WHERE operator_id = ? AND pattern_type = ? "
                "AND confidence >= ? ORDER BY (occurrence_count * confidence) DESC",
                (operator_id, pattern_type, min_confidence),
            )
        else:
            cur.execute(
                "SELECT * FROM oig_patterns WHERE operator_id = ? AND confidence >= ? "
                "ORDER BY (occurrence_count * confidence) DESC",
                (operator_id, min_confidence),
            )
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["evidence"] = json.loads(d.get("evidence") or "[]")
            except Exception:
                d["evidence"] = []
            result.append(d)
        return result

    # ── Epochs ────────────────────────────────────────────────────────────────

    def detect_epoch_boundary(
        self,
        operator_id: str,
        fact_change_threshold: int = 10,
        time_window_days: int = 14,
    ) -> bool:
        """Check if enough facts have changed recently to warrant a new epoch.

        Returns True if:
        - Count of facts created or invalidated in the last time_window_days >= fact_change_threshold
        - AND the current epoch is older than time_window_days
        """
        node = self.get_node("operator", operator_id)
        if not node:
            return False
        subject_id = node["id"]

        cutoff = _to_iso(datetime.now(timezone.utc) - timedelta(days=time_window_days))
        cur = self.conn.cursor()

        # Count recent fact changes (created OR invalidated)
        cur.execute(
            "SELECT COUNT(*) as cnt FROM oig_edges "
            "WHERE subject_id = ? AND (t_valid_from >= ? OR (t_valid_to IS NOT NULL AND t_valid_to >= ?))",
            (subject_id, cutoff, cutoff),
        )
        row = cur.fetchone()
        change_count = row["cnt"] if row else 0

        if change_count < fact_change_threshold:
            return False

        # Check current epoch age
        current = self._get_current_epoch(operator_id)
        if not current:
            return True  # No epoch yet — create the first one

        try:
            epoch_start = datetime.fromisoformat(current["start_time"])
            if epoch_start.tzinfo is None:
                epoch_start = epoch_start.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - epoch_start).days
            return age_days >= time_window_days
        except Exception:
            return False

    def create_epoch(
        self,
        operator_id: str,
        name: str,
        defining_characteristic: str,
        mood_signature: str = "neutral",
        growth_areas: list[str] | None = None,
    ) -> str:
        """Close the current epoch and create a new one.

        Calculates fact_changes and missions_completed for the closed epoch.
        Returns the new epoch id.
        """
        now = _now_iso()
        # Close current epoch
        self.conn.execute(
            "UPDATE oig_epochs SET end_time = ? WHERE operator_id = ? AND end_time IS NULL",
            (now, operator_id),
        )

        epoch_id = str(uuid4())
        self.conn.execute(
            "INSERT INTO oig_epochs "
            "(id, operator_id, name, start_time, end_time, defining_characteristic, "
            " missions_completed, fact_changes, mood_signature, growth_areas) "
            "VALUES (?, ?, ?, ?, NULL, ?, 0, 0, ?, ?)",
            (
                epoch_id,
                operator_id,
                name,
                now,
                defining_characteristic,
                mood_signature,
                json.dumps(growth_areas or []),
            ),
        )
        self.conn.commit()
        return epoch_id

    def get_epochs(self, operator_id: str) -> list[dict]:
        """Return all epochs for an operator, chronologically ordered."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM oig_epochs WHERE operator_id = ? ORDER BY start_time ASC",
            (operator_id,),
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["growth_areas"] = json.loads(d.get("growth_areas") or "[]")
            except Exception:
                d["growth_areas"] = []
            result.append(d)
        return result

    def _get_current_epoch(self, operator_id: str) -> dict | None:
        """Return the current (open) epoch for an operator, or None."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM oig_epochs WHERE operator_id = ? AND end_time IS NULL "
            "ORDER BY start_time DESC LIMIT 1",
            (operator_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["growth_areas"] = json.loads(d.get("growth_areas") or "[]")
        except Exception:
            d["growth_areas"] = []
        return d

    # ── Bond Metrics ──────────────────────────────────────────────────────────

    def compute_bond_metrics(self, operator_id: str) -> dict:
        """Calculate current bond metrics from graph data.

        trust_level formula:
            base = 0.1
            + (min(bond_age_days, 365) / 365) * 0.2          (max 0.20)
            + (min(missions_completed, 50) / 50) * 0.25       (max 0.25)
            + (corrections_learned / max(corrections_total, 1)) * 0.2  (max 0.20)
            + (disagreement_resolutions / max(disagreements, 1)) * 0.15 (max 0.15)
            max = 1.0

        Reads from existing nexusmon tables (missions, conflict_log, entity_state)
        and supplements with OIG graph data.
        """
        # Bond age from entity_state
        bond_age_days = 0
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT bond_established_at FROM entity_state LIMIT 1")
            row = cur.fetchone()
            if row and row["bond_established_at"]:
                bond_start = datetime.fromisoformat(row["bond_established_at"])
                if bond_start.tzinfo is None:
                    bond_start = bond_start.replace(tzinfo=timezone.utc)
                bond_age_days = (datetime.now(timezone.utc) - bond_start).days
        except Exception:
            pass

        # Missions completed + failed (from missions table)
        shared_victories = 0
        shared_failures = 0
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM missions WHERE status = 'COMPLETE'"
            )
            row = cur.fetchone()
            shared_victories = row["cnt"] if row else 0
            cur.execute("SELECT COUNT(*) as cnt FROM missions WHERE status = 'FAILED'")
            row = cur.fetchone()
            shared_failures = row["cnt"] if row else 0
        except Exception:
            pass

        # Corrections (from OIG graph)
        corrections_received = 0
        corrections_learned_from = 0
        node = self.get_node("operator", operator_id)
        if node:
            cur = self.conn.cursor()
            try:
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM oig_edges "
                    "WHERE subject_id = ? AND fact_type = 'correction'",
                    (node["id"],),
                )
                row = cur.fetchone()
                corrections_received = row["cnt"] if row else 0
                # "learned_from" = corrections where metadata has learned=true
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM oig_edges "
                    "WHERE subject_id = ? AND fact_type = 'correction' "
                    "AND LOWER(metadata) LIKE '%\"learned\": true%'",
                    (node["id"],),
                )
                row = cur.fetchone()
                corrections_learned_from = row["cnt"] if row else 0
            except Exception:
                pass

        # Disagreements + resolutions (from conflict_log if available)
        disagreements = 0
        resolutions = 0
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM conflict_log")
            row = cur.fetchone()
            disagreements = row["cnt"] if row else 0
            cur.execute(
                "SELECT COUNT(*) as cnt FROM conflict_log WHERE outcome IS NOT NULL"
            )
            row = cur.fetchone()
            resolutions = row["cnt"] if row else 0
        except Exception:
            pass

        # Inside references from OIG patterns
        inside_refs: list[str] = []
        try:
            patterns = self.get_patterns(operator_id, pattern_type="conversational")
            inside_refs = [
                p["description"] for p in patterns if p.get("occurrence_count", 0) >= 3
            ][:10]
        except Exception:
            pass

        # Compute trust level
        time_component = (min(bond_age_days, 365) / 365) * 0.2
        experience_component = (min(shared_victories, 50) / 50) * 0.25
        correction_component = (
            corrections_learned_from / max(corrections_received, 1)
        ) * 0.2
        conflict_component = (resolutions / max(disagreements, 1)) * 0.15
        trust_level = min(
            1.0,
            0.1
            + time_component
            + experience_component
            + correction_component
            + conflict_component,
        )

        return {
            "trust_level": round(trust_level, 4),
            "bond_age_days": bond_age_days,
            "shared_victories": shared_victories,
            "shared_failures": shared_failures,
            "corrections_received": corrections_received,
            "corrections_learned_from": corrections_learned_from,
            "disagreements": disagreements,
            "disagreements_resolved": resolutions,
            "inside_references": inside_refs,
        }


# ── Module-level singleton ────────────────────────────────────────────────────

_graph: TemporalGraph | None = None


def get_graph(db_path: str | None = None) -> TemporalGraph:
    """Return (or lazily create) the module-level TemporalGraph singleton."""
    global _graph
    if _graph is None:
        db_path = db_path or os.environ.get("DATABASE_URL") or "data/nexusmon.db"
        _graph = TemporalGraph(db_path)
        _graph.ensure_tables()
    return _graph
