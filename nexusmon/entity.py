# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
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
        self._ensure_entity_row()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

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

    def add_evolution_xp(self, amount):
        self._db.conn.execute(
            "UPDATE entity_state SET evolution_xp = evolution_xp + ? WHERE id = ?",
            (amount, ENTITY_ID),
        )
        self._db.conn.commit()

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


_entity = None


def get_entity(db_path="data/nexusmon.db"):
    global _entity
    if _entity is None:
        _entity = NexusmonEntity(db_path)
    return _entity
