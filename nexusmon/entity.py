# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import json
from datetime import datetime, timezone
from nexusmon.memory import NexusmonDB

ENTITY_ID = "nexusmon-prime"
VALID_FORMS = {"ROOKIE", "CHAMPION", "ULTIMATE", "MEGA", "SOVEREIGN"}
VALID_MOODS = {
    "CALM",
    "FOCUSED",
    "RESTLESS",
    "CHARGED",
    "PROTECTIVE",
    "CURIOUS",
    "DORMANT",
    "ALERT",
    "TRIUMPHANT",
    "CONTEMPLATIVE",
}
_DEFAULT_GREETING = "NEXUSMON is alive. Regan Stewart Harris — your system is online."
_DEFAULT_TRAITS = {
    "curiosity": 0.7,
    "loyalty": 1.0,
    "aggression": 0.3,
    "creativity": 0.6,
    "autonomy": 0.5,
    "patience": 0.7,
    "protectiveness": 0.8,
}
LOYALTY_FLOOR = 0.5


class NexusmonEntity:
    def __init__(self, db_path="data/nexusmon.db"):
        self._db = NexusmonDB(db_path)
        self._db.ensure_schema()
        self._ensure_schema()
        self._ensure_entity_row()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _ensure_schema(self) -> None:
        """Create extended tables (operator_memory, curiosities, safe_word) if absent."""
        conn = self._db.conn
        conn.executescript(
            # ── Operator memory ────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS operator_memory ("
            "entity_id TEXT PRIMARY KEY, "
            "known_preferences TEXT DEFAULT '{}', "
            "known_goals TEXT DEFAULT '[]', "
            "working_style TEXT DEFAULT 'Unknown — learning in progress', "
            "typical_session_times TEXT DEFAULT '[]', "
            "command_style TEXT DEFAULT '', "
            "significant_moments TEXT DEFAULT '[]', "
            "inside_references TEXT DEFAULT '[]', "
            "gratitude_log TEXT DEFAULT '[]', "
            "conflict_log TEXT DEFAULT '[]', "
            "goals_achieved TEXT DEFAULT '[]', "
            "updated_at TEXT); "
            # ── Curiosities ────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS curiosities ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "entity_id TEXT NOT NULL, "
            "topic TEXT NOT NULL, "
            "origin TEXT DEFAULT '', "
            "depth REAL DEFAULT 0.1, "
            "first_noticed TEXT NOT NULL, "
            "notes TEXT DEFAULT '', "
            "mention_count INTEGER DEFAULT 1); "
            # ── Safe word ──────────────────────────────────────────────────
            "CREATE TABLE IF NOT EXISTS safe_word ("
            "entity_id TEXT PRIMARY KEY, "
            "word TEXT NOT NULL, "
            "activated_count INTEGER DEFAULT 0, "
            "last_activated TEXT, "
            "set_at TEXT NOT NULL); "
        )
        conn.commit()

    def _ensure_entity_row(self):
        now = self._now()
        conn = self._db.conn
        conn.execute(
            "INSERT OR IGNORE INTO entity_state "
            "(id, operator_id, operator_name, bond_established_at, "
            " total_seconds_alive, current_form, evolution_xp, "
            " interaction_count, mood, boot_count, "
            " last_boot, last_interaction, greeting) "
            "VALUES (?, 'op-001', 'Regan Stewart Harris', ?, "
            " 0, 'ROOKIE', 0.0, 0, 'CALM', 0, NULL, NULL, ?)",
            (ENTITY_ID, now, _DEFAULT_GREETING),
        )
        conn.execute(
            "INSERT OR IGNORE INTO entity_traits "
            "(entity_id, curiosity, loyalty, aggression, creativity, autonomy, patience, protectiveness) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ENTITY_ID, 0.7, 1.0, 0.3, 0.6, 0.5, 0.7, 0.8),
        )
        conn.commit()

    def boot(self):
        now = self._now()
        conn = self._db.conn
        cur = conn.cursor()
        cur.execute(
            "SELECT boot_count, last_boot, total_seconds_alive FROM entity_state WHERE id = ?",
            (ENTITY_ID,),
        )
        row = cur.fetchone()
        previous_count = row["boot_count"] if row else 0
        elapsed = 0
        if row and row["last_boot"]:
            try:
                last = datetime.fromisoformat(row["last_boot"])
                elapsed = int((datetime.now(timezone.utc) - last).total_seconds())
            except Exception:
                pass
        cur.execute(
            "UPDATE entity_state SET boot_count = boot_count + 1, last_boot = ?, total_seconds_alive = total_seconds_alive + ? WHERE id = ?",
            (now, elapsed, ENTITY_ID),
        )
        conn.commit()
        if previous_count == 0:
            print(self.get_greeting())
        return self.get_state()

    def get_state(self):
        cur = self._db.conn.cursor()
        cur.execute("SELECT * FROM entity_state WHERE id = ?", (ENTITY_ID,))
        row = cur.fetchone()
        return dict(row) if row else {}

    def get_traits(self):
        cur = self._db.conn.cursor()
        cur.execute("SELECT * FROM entity_traits WHERE entity_id = ?", (ENTITY_ID,))
        row = cur.fetchone()
        if row is None:
            return {}
        d = dict(row)
        d.pop("entity_id", None)
        return d

    def get_mood(self):
        return self.get_state().get("mood", "CALM")

    def set_mood(self, mood):
        if mood not in VALID_MOODS:
            return
        self._db.conn.execute(
            "UPDATE entity_state SET mood = ? WHERE id = ?", (mood, ENTITY_ID)
        )
        self._db.conn.commit()

    def get_form(self):
        return self.get_state().get("current_form", "ROOKIE")

    def increment_interaction(self):
        now = self._now()
        self._db.conn.execute(
            "UPDATE entity_state SET interaction_count = interaction_count + 1, last_interaction = ? WHERE id = ?",
            (now, ENTITY_ID),
        )
        self._db.conn.commit()

    def add_evolution_xp(self, amount: float) -> dict:
        """Add XP and check for evolution threshold.

        Returns {"evolved": bool, "from_form": str, "to_form": str, "xp": float}
        """
        state = self.get_state()
        current_xp = float(state.get("evolution_xp") or 0.0) + amount

        self._db.conn.execute(
            "UPDATE entity_state SET evolution_xp=? WHERE id=?",
            (current_xp, ENTITY_ID),
        )
        self._db.conn.commit()

        return self.check_and_evolve()

    def check_and_evolve(self) -> dict:
        """Check if evolution threshold is met and fire evolution if so.

        Returns {"evolved": bool, "from_form": str, "to_form": str, "xp": float}
        """
        from nexusmon.evolution import can_evolve, get_next_form

        state = self.get_state()
        current_form = state.get("current_form", "ROOKIE")
        current_xp = float(state.get("evolution_xp") or 0.0)

        result = {
            "evolved": False,
            "from_form": current_form,
            "to_form": current_form,
            "xp": current_xp,
        }

        if not can_evolve(current_form, current_xp):
            return result

        next_form = get_next_form(current_form)
        if not next_form:
            return result

        # Evolve
        self._db.conn.execute(
            "UPDATE entity_state SET current_form=?, evolution_xp=0.0, mood='CONTEMPLATIVE' WHERE id=?",
            (next_form, ENTITY_ID),
        )
        # Log evolution event
        now = self._now()
        self._db.conn.execute(
            "INSERT INTO evolution_events (entity_id, from_form, to_form, occurred_at, trigger) VALUES (?,?,?,?,?)",
            (ENTITY_ID, current_form, next_form, now, "xp_threshold"),
        )
        self._db.conn.commit()

        # Write chronicle entry
        try:
            from nexusmon.chronicle import get_chronicle, EVOLUTION

            get_chronicle().add_entry(
                event_type=EVOLUTION,
                title=f"{next_form}: What I Became",
                content=f"NEXUSMON evolved from {current_form} to {next_form}. The change was real.",
                significance=0.95,
                form=next_form,
                mood="CONTEMPLATIVE",
            )
        except Exception:
            pass

        # Create witnessed artifact
        try:
            from nexusmon.artifacts import get_vault

            get_vault().create_witnessed(
                event_name=f"Evolution to {next_form}",
                description=f"NEXUSMON evolved from {current_form} to {next_form}.",
                form=next_form,
            )
        except Exception:
            pass

        result.update({"evolved": True, "to_form": next_form})
        return result

    def record_operator_session(self, operator_id, nexus_form, drift):
        now = self._now()
        self._db.conn.execute(
            "INSERT INTO operator_sessions (operator_id, session_count, last_seen, nexus_form, drift) "
            "VALUES (?, 1, ?, ?, ?) "
            "ON CONFLICT(operator_id) DO UPDATE SET "
            "    session_count = session_count + 1, "
            "    last_seen = excluded.last_seen, "
            "    nexus_form = excluded.nexus_form, "
            "    drift = excluded.drift",
            (operator_id, now, nexus_form, drift),
        )
        self._db.conn.commit()

    def record_metrics(self, entropy, drift, coherence):
        now = self._now()
        self._db.conn.execute(
            "INSERT INTO system_metrics (timestamp, entropy, drift, coherence) VALUES (?, ?, ?, ?)",
            (now, entropy, drift, coherence),
        )
        self._db.conn.commit()

    def get_greeting(self):
        state = self.get_state()
        return state.get("greeting") or _DEFAULT_GREETING

    def get_character_summary(self) -> str:
        """One-line boot summary for run.py startup output."""
        state = self.get_state()
        form = state.get("current_form", "ROOKIE")
        mood = state.get("mood", "CALM")
        boots = state.get("boot_count", 0)
        xp = state.get("evolution_xp", 0.0)
        return (
            f"Form={form} | Mood={mood} | "
            f"Boots={boots} | XP={xp:.0f} | "
            f"Operator=Regan Stewart Harris"
        )

    def update_trait(self, trait, delta):
        traits = self.get_traits()
        if trait not in traits:
            return
        new_val = max(0.0, min(1.0, traits[trait] + delta))
        if trait == "loyalty":
            new_val = max(LOYALTY_FLOOR, new_val)
        self._db.conn.execute(
            f"UPDATE entity_traits SET {trait} = ? WHERE entity_id = ?",
            (new_val, ENTITY_ID),
        )
        self._db.conn.commit()

    # ── XP & Evolution ────────────────────────────────────────────────────

    def award_xp(self, amount: float = 5.0) -> dict:
        """Award XP and autonomously trigger evolution when threshold is met.

        Returns a dict: {xp_awarded, evolved, from_form, new_form, new_xp}
        """
        from nexusmon.evolution import can_evolve, get_next_form

        state = self.get_state()
        current_form = state.get("current_form", "ROOKIE")
        current_xp = float(state.get("evolution_xp", 0.0))
        new_xp = current_xp + amount

        self._db.conn.execute(
            "UPDATE entity_state SET evolution_xp = ? WHERE id = ?",
            (new_xp, ENTITY_ID),
        )
        self._db.conn.commit()

        evolved = False
        new_form = current_form

        if can_evolve(current_form, new_xp):
            next_form = get_next_form(current_form)
            if next_form:
                self._db.conn.execute(
                    "UPDATE entity_state SET current_form = ?, mood = 'CONTEMPLATIVE' WHERE id = ?",
                    (next_form, ENTITY_ID),
                )
                self._db.conn.execute(
                    "INSERT INTO evolution_events "
                    "(entity_id, from_form, to_form, occurred_at, trigger) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (ENTITY_ID, current_form, next_form, self._now(), "xp_threshold"),
                )
                self._db.conn.commit()
                evolved = True
                new_form = next_form
                try:
                    from nexusmon.chronicle import get_chronicle

                    get_chronicle().on_evolution(current_form, next_form)
                except Exception:
                    pass

        return {
            "xp_awarded": amount,
            "evolved": evolved,
            "from_form": current_form,
            "new_form": new_form,
            "new_xp": new_xp,
        }

    # ── Conversation memory ───────────────────────────────────────────────

    def log_exchange(self, operator_id: str, role: str, content: str) -> None:
        """Persist one exchange turn to conversation_history."""
        self._db.conn.execute(
            "INSERT INTO conversation_history (operator_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (operator_id, role, content, self._now()),
        )
        self._db.conn.commit()

    def get_conversation_history(self, operator_id: str, last_n: int = 20) -> list:
        """Return the last N exchanges for operator_id as [{role, content}]."""
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT role, content FROM conversation_history "
            "WHERE operator_id = ? ORDER BY id DESC LIMIT ?",
            (operator_id, last_n),
        )
        rows = cur.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # ── Operator profile ──────────────────────────────────────────────────

    def _ensure_operator_profile(self, operator_id: str) -> None:
        self._db.conn.execute(
            "INSERT OR IGNORE INTO operator_profile (operator_id, name) "
            "VALUES (?, 'Regan Stewart Harris')",
            (operator_id,),
        )
        self._db.conn.commit()

    def get_operator_profile(self, operator_id: str) -> dict:
        """Return the operator profile dict, creating defaults if absent."""
        self._ensure_operator_profile(operator_id)
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT * FROM operator_profile WHERE operator_id = ?", (operator_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else {}

    def update_operator_profile(
        self,
        operator_id: str,
        coherence: float,
        fatigue: float,
        drift: float,
        focus: float,
        message_count: int,
    ) -> None:
        """Upsert operator profile metrics and recompute rank."""
        self._ensure_operator_profile(operator_id)
        _THRESHOLDS = [
            ("SOVEREIGN_OPERATOR", 200),
            ("COMMANDER", 50),
            ("OPERATOR", 10),
            ("RECRUIT", 0),
        ]
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT total_sessions FROM operator_profile WHERE operator_id = ?",
            (operator_id,),
        )
        row = cur.fetchone()
        sessions = row["total_sessions"] if row else 0
        rank = "RECRUIT"
        for rank_name, threshold in _THRESHOLDS:
            if sessions >= threshold:
                rank = rank_name
                break
        self._db.conn.execute(
            "UPDATE operator_profile SET "
            "coherence = ?, fatigue = ?, drift = ?, focus = ?, "
            "message_count = ?, rank = ?, last_updated = ? "
            "WHERE operator_id = ?",
            (
                coherence,
                fatigue,
                drift,
                focus,
                message_count,
                rank,
                self._now(),
                operator_id,
            ),
        )
        self._db.conn.commit()

    def bump_operator_message_count(self, operator_id: str) -> None:
        """Increment total_commands on the operator profile."""
        self._ensure_operator_profile(operator_id)
        self._db.conn.execute(
            "UPDATE operator_profile SET total_commands = total_commands + 1 "
            "WHERE operator_id = ?",
            (operator_id,),
        )
        self._db.conn.commit()

    def record_operator_session_end(self, operator_id: str) -> None:
        """Increment total_sessions when a WS connection closes."""
        self._ensure_operator_profile(operator_id)
        self._db.conn.execute(
            "UPDATE operator_profile SET total_sessions = total_sessions + 1 "
            "WHERE operator_id = ?",
            (operator_id,),
        )
        self._db.conn.commit()

    # ── Mood ──────────────────────────────────────────────────────────────

    def recalculate_mood(
        self,
        operator_fatigue: float = 0.0,
        active_missions: int = 0,
        just_evolved: bool = False,
        recent_success: bool = False,
    ) -> str:
        """Recalculate and persist mood based on current state."""
        from nexusmon.mood import calculate_mood

        state = self.get_state()
        last_interaction = state.get("last_interaction")
        idle_hours = 0.0
        if last_interaction:
            try:
                last_dt = datetime.fromisoformat(last_interaction)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                idle_hours = (
                    datetime.now(timezone.utc) - last_dt
                ).total_seconds() / 3600.0
            except Exception:
                pass
        mood = calculate_mood(
            operator_fatigue=operator_fatigue,
            coherence=0.8,
            active_missions=active_missions,
            last_interaction_hours=idle_hours,
            just_evolved=just_evolved,
            recent_success=recent_success,
            current_hour=datetime.now().hour,
        )
        self.set_mood(mood)
        return mood

    # ── Trait events ──────────────────────────────────────────────────────

    def apply_trait_event(self, event: str) -> None:
        """Apply a named trait shift event (from nexusmon.traits.TRAIT_SHIFT_RULES)."""
        from nexusmon.traits import apply_event

        current = self.get_traits()
        updated = apply_event(current, event)
        for trait, val in updated.items():
            if trait in current and abs(val - current[trait]) > 0.0001:
                self._db.conn.execute(
                    f"UPDATE entity_traits SET {trait} = ? WHERE entity_id = ?",
                    (val, ENTITY_ID),
                )
        self._db.conn.commit()

    # ── Context snippets ──────────────────────────────────────────────────

    def get_greeting_context(self, operator_id: str) -> str:
        """Return a one-line operator profile snippet for greeting prompts."""
        p = self.get_operator_profile(operator_id)
        if not p:
            return ""
        return (
            f"Operator {p.get('name', 'Unknown')} — "
            f"rank {p.get('rank', 'RECRUIT')}, "
            f"coherence {p.get('coherence', 0.8):.2f}, "
            f"fatigue {p.get('fatigue', 0.0):.2f}, "
            f"sessions {p.get('total_sessions', 0)}, "
            f"commands {p.get('total_commands', 0)}"
        )

    # ── Operator memory ───────────────────────────────────────────────────

    _OM_LIST_FIELDS = {
        "known_goals",
        "typical_session_times",
        "significant_moments",
        "inside_references",
        "gratitude_log",
        "conflict_log",
        "goals_achieved",
    }
    _OM_DICT_FIELDS = {"known_preferences"}

    def get_operator_memory(self) -> dict:
        """Return operator memory row as dict, creating default if not exists."""
        conn = self._db.conn
        conn.execute(
            "INSERT OR IGNORE INTO operator_memory (entity_id, updated_at) VALUES (?, ?)",
            (ENTITY_ID, self._now()),
        )
        conn.commit()
        cur = conn.cursor()
        cur.execute("SELECT * FROM operator_memory WHERE entity_id = ?", (ENTITY_ID,))
        row = cur.fetchone()
        result = dict(row)
        for field in self._OM_LIST_FIELDS:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except Exception:
                    result[field] = []
        for field in self._OM_DICT_FIELDS:
            if field in result and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except Exception:
                    result[field] = {}
        return result

    def update_operator_memory(self, **fields) -> None:
        """Update specified fields in operator_memory. JSON-serializes list/dict fields."""
        serialized = {}
        for k, v in fields.items():
            if isinstance(v, (list, dict)):
                serialized[k] = json.dumps(v)
            else:
                serialized[k] = v
        serialized["updated_at"] = self._now()
        set_clause = ", ".join(f"{k} = ?" for k in serialized)
        values = list(serialized.values()) + [ENTITY_ID]
        # Ensure row exists first
        self._db.conn.execute(
            "INSERT OR IGNORE INTO operator_memory (entity_id, updated_at) VALUES (?, ?)",
            (ENTITY_ID, self._now()),
        )
        self._db.conn.execute(
            f"UPDATE operator_memory SET {set_clause} WHERE entity_id = ?",
            values,
        )
        self._db.conn.commit()

    # ── Curiosities ───────────────────────────────────────────────────────

    def add_curiosity(self, topic: str, origin: str = "") -> int:
        """Add a new curiosity. If topic already exists, increment mention_count and depth."""
        conn = self._db.conn
        cur = conn.cursor()
        cur.execute(
            "SELECT id, depth, mention_count FROM curiosities WHERE entity_id = ? AND topic = ?",
            (ENTITY_ID, topic),
        )
        row = cur.fetchone()
        if row:
            new_depth = min(1.0, round(row["depth"] + 0.1, 4))
            conn.execute(
                "UPDATE curiosities SET mention_count = mention_count + 1, depth = ? WHERE id = ?",
                (new_depth, row["id"]),
            )
            conn.commit()
            return row["id"]
        cur.execute(
            "INSERT INTO curiosities (entity_id, topic, origin, depth, first_noticed, mention_count) "
            "VALUES (?, ?, ?, 0.1, ?, 1)",
            (ENTITY_ID, topic, origin, self._now()),
        )
        conn.commit()
        return cur.lastrowid

    def get_curiosities(self) -> list:
        """Return all curiosities ordered by depth desc."""
        cur = self._db.conn.cursor()
        cur.execute(
            "SELECT * FROM curiosities WHERE entity_id = ? ORDER BY depth DESC",
            (ENTITY_ID,),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Safe word ─────────────────────────────────────────────────────────

    def set_safe_word(self, word: str) -> None:
        """Set or update the safe word."""
        now = self._now()
        self._db.conn.execute(
            "INSERT INTO safe_word (entity_id, word, activated_count, set_at) "
            "VALUES (?, ?, 0, ?) "
            "ON CONFLICT(entity_id) DO UPDATE SET word = excluded.word, set_at = excluded.set_at",
            (ENTITY_ID, word.lower(), now),
        )
        self._db.conn.commit()

    def check_safe_word(self, text: str) -> bool:
        """Return True if text matches the safe word (case-insensitive)."""
        word = self.get_safe_word()
        if word is None:
            return False
        return text.strip().lower() == word.lower()

    def activate_safe_word(self) -> bool:
        """Increment activated_count, set last_activated. Returns True if safe word is set."""
        cur = self._db.conn.cursor()
        cur.execute("SELECT word FROM safe_word WHERE entity_id = ?", (ENTITY_ID,))
        row = cur.fetchone()
        if row is None:
            return False
        self._db.conn.execute(
            "UPDATE safe_word SET activated_count = activated_count + 1, last_activated = ? "
            "WHERE entity_id = ?",
            (self._now(), ENTITY_ID),
        )
        self._db.conn.commit()
        return True

    def get_safe_word(self) -> "str | None":
        """Return current safe word or None."""
        cur = self._db.conn.cursor()
        cur.execute("SELECT word FROM safe_word WHERE entity_id = ?", (ENTITY_ID,))
        row = cur.fetchone()
        return row["word"] if row else None


_entity = None


def get_entity(db_path="data/nexusmon.db"):
    global _entity
    if _entity is None:
        _entity = NexusmonEntity(db_path)
    return _entity
