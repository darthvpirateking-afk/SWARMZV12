# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/operator.py -- OperatorProfile: silent session tracking.

Tracks four dimensions per operator, updated after every exchange:

  coherence  -- alignment between stated goals and actual commands (0-1)
  fatigue    -- grows with message count and session length (0-1)
  drift      -- deviation from session's original intent (0-1)
  focus      -- single-task vs scatter ratio (0-1, 1 = fully focused)

All values are clamped to [0.0, 1.0].
State is stored in nexus_entity.db via NexusmonEntity.
"""

from datetime import datetime, timezone
from typing import Optional


class OperatorProfile:
    """Live operator state for one session.

    Instantiated per WebSocket connection; persisted to SQLite via entity.
    """

    # How much fatigue increases per message (decays over time)
    _FATIGUE_PER_MSG = 0.015
    _FATIGUE_DECAY_PER_HOUR = 0.10

    # Coherence/drift nudge per exchange
    _COHERENCE_NUDGE = 0.02
    _DRIFT_NUDGE = 0.01

    def __init__(self, operator_id: str) -> None:
        self.operator_id = operator_id
        self._session_start = datetime.now(timezone.utc)
        self._message_count = 0
        self._first_intent: Optional[str] = None

        # Load persisted values from entity
        self._coherence: float = 0.80
        self._fatigue: float = 0.00
        self._drift: float = 0.00
        self._focus: float = 1.00
        self._load()

    # ------------------------------------------------------------------
    # Init: load from SQLite
    # ------------------------------------------------------------------

    def _load(self) -> None:
        try:
            from nexusmon.entity import get_entity

            entity = get_entity()
            p = entity.get_operator_profile(self.operator_id)
            self._coherence = float(p.get("coherence", 0.80))
            self._fatigue = float(p.get("fatigue", 0.00))
            self._drift = float(p.get("drift", 0.00))
            self._focus = float(p.get("focus", 1.00))
            self._message_count = int(p.get("message_count", 0))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Per-exchange update
    # ------------------------------------------------------------------

    def record_exchange(
        self,
        message: str,
        intent: str = "general",
        response_quality: float = 1.0,
    ) -> None:
        """Call once per operator message to update all dimensions.

        Args:
            message:          The operator's raw message text.
            intent:           Classified intent label (from intelligence layer).
            response_quality: 0-1 hint from the AI layer (1 = good response).
        """
        self._message_count += 1

        # ── Track first intent for drift detection ─────────────────────
        if self._first_intent is None:
            self._first_intent = intent

        # ── Fatigue: grows per message, but longer gaps = less fatigue ──
        session_hours = (
            datetime.now(timezone.utc) - self._session_start
        ).total_seconds() / 3600
        # Decay fatigue slightly for rest between sessions
        decayed = self._fatigue - (session_hours * self._FATIGUE_DECAY_PER_HOUR * 0.01)
        self._fatigue = max(0.0, decayed) + self._FATIGUE_PER_MSG

        # ── Coherence: nudge up if response_quality is high ─────────────
        coherence_delta = self._COHERENCE_NUDGE * (response_quality - 0.5) * 2
        self._coherence = self._clamp(self._coherence + coherence_delta)

        # ── Drift: increases when intent shifts from first intent ────────
        if self._first_intent and intent != self._first_intent and intent != "general":
            self._drift = self._clamp(self._drift + self._DRIFT_NUDGE)
        elif intent == self._first_intent:
            self._drift = self._clamp(self._drift - self._DRIFT_NUDGE * 0.5)

        # ── Focus: single intent sessions score high ─────────────────────
        if self._first_intent:
            same_ratio = 1.0 if intent == self._first_intent else 0.0
            # Exponential moving average
            self._focus = self._clamp(self._focus * 0.9 + same_ratio * 0.1)

        self._persist()

    # ------------------------------------------------------------------
    # Persist to SQLite
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        try:
            from nexusmon.entity import get_entity

            entity = get_entity()
            entity.update_operator_profile(
                self.operator_id,
                coherence=round(self._coherence, 4),
                fatigue=round(self._clamp(self._fatigue), 4),
                drift=round(self._drift, 4),
                focus=round(self._focus, 4),
                message_count=self._message_count,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def coherence(self) -> float:
        return self._coherence

    @property
    def fatigue(self) -> float:
        return self._clamp(self._fatigue)

    @property
    def drift(self) -> float:
        return self._drift

    @property
    def focus(self) -> float:
        return self._focus

    @property
    def message_count(self) -> int:
        return self._message_count

    # ------------------------------------------------------------------
    # Context snapshot for prompt injection
    # ------------------------------------------------------------------

    def to_context_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "coherence": round(self._coherence, 3),
            "fatigue": round(self._clamp(self._fatigue), 3),
            "drift": round(self._drift, 3),
            "focus": round(self._focus, 3),
            "message_count": self._message_count,
        }

    def to_prompt_snippet(self) -> str:
        """One-line context string for injection into system prompt."""
        state = "sharp" if self._coherence > 0.7 else "drifting"
        energy = "alert" if self._clamp(self._fatigue) < 0.4 else "tired"
        return (
            f"Operator is {state} (coherence={self._coherence:.2f}) and "
            f"{energy} (fatigue={self._clamp(self._fatigue):.2f}). "
            f"Drift={self._drift:.2f}, Focus={self._focus:.2f}. "
            f"Messages this session: {self._message_count}."
        )


# ── OperatorEngine (NEXUSMON MASTER SPEC Parts 9 & 22) ────────────────
# Implements full operator profile persistence, rank computation,
# synergy scoring, and the operator profile page (Regan Stewart Harris).

import json  # noqa: E402  (extended import — sqlite3, json, os not in original header)
import os  # noqa: E402
import sqlite3  # noqa: E402

# nexusmon.memory.get_db is not yet implemented; fall back to direct sqlite3.
try:
    from nexusmon.memory import get_db as _get_db  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    _get_db = None

_ENGINE_DB_PATH = "data/nexusmon.db"

_RANK_THRESHOLDS = [
    ("SOVEREIGN_OPERATOR", 200),
    ("COMMANDER", 50),
    ("OPERATOR", 10),
    ("RECRUIT", 0),
]

_OP_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS operator_profile (
    operator_id          TEXT PRIMARY KEY,
    name                 TEXT NOT NULL DEFAULT 'Regan Stewart Harris',
    rank                 TEXT NOT NULL DEFAULT 'RECRUIT',
    coherence            REAL NOT NULL DEFAULT 0.5,
    fatigue              REAL NOT NULL DEFAULT 0.5,
    drift                REAL NOT NULL DEFAULT 0.5,
    focus                REAL NOT NULL DEFAULT 0.5,
    total_sessions       INTEGER NOT NULL DEFAULT 0,
    total_commands       INTEGER NOT NULL DEFAULT 0,
    mission_success_rate REAL NOT NULL DEFAULT 0.0,
    last_updated         TEXT
);
"""

_OP_PROFILE_PAGE_DDL = """
CREATE TABLE IF NOT EXISTS operator_profile_page (
    operator_id         TEXT PRIMARY KEY,
    origin              TEXT NOT NULL DEFAULT 'Human. From Earth.',
    observed_strengths  TEXT NOT NULL DEFAULT '[]',
    working_style       TEXT NOT NULL DEFAULT 'Unknown — learning in progress',
    what_drives_him     TEXT NOT NULL DEFAULT 'Unknown — learning in progress',
    what_he_cares_about TEXT NOT NULL DEFAULT '[]',
    nexusmon_note       TEXT NOT NULL DEFAULT 'Still getting to know you, Regan Stewart Harris. Ask me anything.',
    last_updated        TEXT
);
"""


class OperatorEngine:
    """NEXUSMON OperatorEngine — durable operator rank, metrics, and profile page.

    Implements NEXUSMON MASTER SPEC Parts 9 and 22.

    Tables (in data/nexusmon.db):
        operator_profile     — rank, coherence/fatigue/drift/focus, session counts
        operator_profile_page — Regan's lore page, strengths, NEXUSMON note

    The operator is always 'Regan Stewart Harris' (op-001 by default).
    """

    def __init__(self, operator_id: str = "op-001") -> None:
        self.operator_id = operator_id
        self._db_path = _ENGINE_DB_PATH
        self._conn = self._connect()
        self._ensure_tables()

    # ------------------------------------------------------------------
    # DB bootstrap
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        self._conn.executescript(_OP_PROFILE_DDL + _OP_PROFILE_PAGE_DDL)
        self._conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Profile CRUD
    # ------------------------------------------------------------------

    def ensure_profile(self) -> dict:
        """Get or create the operator profile row, returning it as a dict.

        Defaults: name='Regan Stewart Harris', rank='RECRUIT', all floats=0.5.
        """
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM operator_profile WHERE operator_id = ?",
            (self.operator_id,),
        )
        row = cur.fetchone()
        if row:
            return dict(row)

        now = self._now()
        cur.execute(
            """
            INSERT INTO operator_profile
                (operator_id, name, rank, coherence, fatigue, drift, focus,
                 total_sessions, total_commands, mission_success_rate, last_updated)
            VALUES (?, 'Regan Stewart Harris', 'RECRUIT',
                    0.5, 0.5, 0.5, 0.5, 0, 0, 0.0, ?)
            """,
            (self.operator_id, now),
        )
        self._conn.commit()
        cur.execute(
            "SELECT * FROM operator_profile WHERE operator_id = ?",
            (self.operator_id,),
        )
        return dict(cur.fetchone())

    def get_rank(self) -> str:
        """Compute operator rank from total_sessions.

        RECRUIT          < 10 sessions
        OPERATOR         >= 10 sessions
        COMMANDER        >= 50 sessions
        SOVEREIGN_OPERATOR >= 200 sessions
        """
        profile = self.ensure_profile()
        total_sessions = int(profile.get("total_sessions", 0))
        for rank_name, threshold in _RANK_THRESHOLDS:
            if total_sessions >= threshold:
                return rank_name
        return "RECRUIT"

    def update_session(
        self,
        coherence: float,
        fatigue: float,
        drift: float,
        focus: float,
    ) -> None:
        """Upsert session metrics and increment total_sessions by 1."""
        self.ensure_profile()  # guarantee row exists
        now = self._now()
        self._conn.execute(
            """
            UPDATE operator_profile SET
                coherence      = ?,
                fatigue        = ?,
                drift          = ?,
                focus          = ?,
                total_sessions = total_sessions + 1,
                last_updated   = ?
            WHERE operator_id = ?
            """,
            (coherence, fatigue, drift, focus, now, self.operator_id),
        )
        self._conn.commit()
        # Recompute and persist rank after session increment
        new_rank = self.get_rank()
        self._conn.execute(
            "UPDATE operator_profile SET rank = ? WHERE operator_id = ?",
            (new_rank, self.operator_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Synergy Score (Part 9.3)
    # ------------------------------------------------------------------

    def get_synergy_score(self, bond_established_at: str) -> float:
        """Compute operator-NEXUSMON synergy score in [0.0, 1.0].

        Factors:
            consistency    (40%) — session regularity proxy (sessions / 100, capped 1.0)
            goal_alignment (40%) — uses stored coherence as proxy
            time_alive     (20%) — days since bond_established_at, caps at 180 days
        """
        profile = self.ensure_profile()
        total_sessions = int(profile.get("total_sessions", 0))

        # Consistency: sigmoid-like growth, saturates at ~100 sessions
        consistency = min(1.0, total_sessions / 100.0)

        # Goal alignment: coherence is the best available proxy (0.0-1.0)
        goal_alignment = float(profile.get("coherence", 0.5))

        # Time alive factor
        time_alive_days = 0.0
        try:
            bond_dt = datetime.fromisoformat(bond_established_at)
            now_dt = datetime.now(timezone.utc)
            if bond_dt.tzinfo is None:
                bond_dt = bond_dt.replace(tzinfo=timezone.utc)
            time_alive_days = (now_dt - bond_dt).total_seconds() / 86400.0
        except Exception:
            time_alive_days = 0.0

        # Time factor: mild bonus for longevity, caps at 1.0 around 180 days
        time_factor = min(1.0, time_alive_days / 180.0)

        score = (consistency * 0.4) + (goal_alignment * 0.4) + (time_factor * 0.2)
        return round(max(0.0, min(1.0, score)), 4)

    # ------------------------------------------------------------------
    # Profile Page (Part 22)
    # ------------------------------------------------------------------

    def get_profile_page(self) -> dict:
        """Return the operator profile page dict, creating defaults if not found."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM operator_profile_page WHERE operator_id = ?",
            (self.operator_id,),
        )
        row = cur.fetchone()
        if row:
            d = dict(row)
            d["observed_strengths"] = json.loads(d.get("observed_strengths") or "[]")
            d["what_he_cares_about"] = json.loads(d.get("what_he_cares_about") or "[]")
            return d

        now = self._now()
        cur.execute(
            """
            INSERT INTO operator_profile_page
                (operator_id, origin, observed_strengths, working_style,
                 what_drives_him, what_he_cares_about, nexusmon_note, last_updated)
            VALUES (?,
                    'Human. From Earth.',
                    '[]',
                    'Unknown \u2014 learning in progress',
                    'Unknown \u2014 learning in progress',
                    '[]',
                    'Still getting to know you, Regan Stewart Harris. Ask me anything.',
                    ?)
            """,
            (self.operator_id, now),
        )
        self._conn.commit()
        return self.get_profile_page()

    def update_nexusmon_note(self, note: str) -> None:
        """Overwrite the free-form NEXUSMON reflection note."""
        self.get_profile_page()  # ensure row exists
        now = self._now()
        self._conn.execute(
            """
            UPDATE operator_profile_page
            SET nexusmon_note = ?, last_updated = ?
            WHERE operator_id = ?
            """,
            (note, now, self.operator_id),
        )
        self._conn.commit()


# ── Module-level singleton ────────────────────────────────────────────

_operator_engine: Optional[OperatorEngine] = None


def get_operator_engine(operator_id: str = "op-001") -> OperatorEngine:
    """Return (or lazily create) the module-level OperatorEngine singleton."""
    global _operator_engine
    if _operator_engine is None:
        _operator_engine = OperatorEngine(operator_id)
    return _operator_engine
