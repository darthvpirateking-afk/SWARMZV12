# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/routes/entity.py -- HTTP endpoints for NEXUSMON entity state.

Mounts at /v1/nexusmon/entity (registered in swarmz_server.py).

Endpoints:

  GET  /v1/nexusmon/entity/state        -- full entity state snapshot
  GET  /v1/nexusmon/entity/traits       -- just traits dict
  POST /v1/nexusmon/entity/mood         -- set mood
  GET  /v1/nexusmon/entity/xp           -- xp and form progress
  GET  /v1/nexusmon/entity/evolution    -- evolution log
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/nexusmon/entity", tags=["nexusmon-entity"])


def _entity():
    from nexusmon.entity import get_entity

    return get_entity()


# ── State ─────────────────────────────────────────────────────────────


@router.get("/state", operation_id="get_nexusmon_entity_state")
def get_entity_state():
    """Full entity state — form, mood, traits, XP, evolution log."""
    state = _entity().get_state()
    # Serialise any non-JSON-safe values
    if state.get("xp_to_next") == float("inf"):
        state["xp_to_next"] = None
    return {"ok": True, "entity": state}


@router.get("")
def get_entity():
    """Canonical capability-gating payload for cockpit/frontend hooks."""
    entity = _entity()
    state = entity.get_state()
    traits = entity.get_traits()

    form = str(state.get("current_form", "ROOKIE"))
    mood = str(state.get("mood", "CALM")).lower()
    xp = float(state.get("evolution_xp", 0.0))

    try:
        from nexusmon.evolution import FORM_XP_THRESHOLDS

        threshold = FORM_XP_THRESHOLDS.get(form)
        xp_pct = (
            100.0
            if threshold is None
            else round(min(100.0, (xp / threshold) * 100.0), 1)
        )
    except Exception:
        xp_pct = 0.0

    payload = {
        "name": "NEXUSMON",
        "form": form,
        "mood": mood,
        "xp": xp,
        "xp_pct": xp_pct,
        "boot_count": state.get("boot_count", 0),
        "interaction_count": state.get("interaction_count", 0),
        "operator_name": state.get("operator_name", ""),
        "traits": traits,
    }
    return {"ok": True, "entity": payload}


@router.get("/traits")
def get_traits():
    return {"ok": True, "traits": _entity().get_traits()}


@router.get("/xp")
def get_xp():
    state = _entity().get_state()
    xp = float(state.get("evolution_xp") or 0.0)
    form = str(state.get("current_form", "ROOKIE")).upper()
    # Compute xp_to_next from known evolution thresholds
    try:
        from nexusmon.evolution import FORM_XP_THRESHOLDS

        xp_to_next = FORM_XP_THRESHOLDS.get(form)
    except Exception:
        _thresholds = {
            "ROOKIE": 100.0,
            "CHAMPION": 500.0,
            "ULTIMATE": 2000.0,
            "MEGA": 10000.0,
        }
        xp_to_next = _thresholds.get(form)
    if xp_to_next is None or xp_to_next == float("inf"):
        xp_to_next = None
        pct = 100.0
    else:
        pct = round(min(100.0, (xp / xp_to_next) * 100.0), 1) if xp_to_next else 100.0
    return {
        "ok": True,
        "xp": xp,
        "xp_to_next": xp_to_next,
        "pct": pct,
        "form": form.capitalize(),
    }


@router.get("/evolution")
def get_evolution():
    state = _entity().get_state()
    current_form = str(state.get("current_form", "ROOKIE")).capitalize()
    # Query evolution_events table for the log
    evolution_log = []
    try:
        from nexusmon.memory import get_db

        db = get_db()
        rows = db.conn.execute(
            "SELECT from_form, to_form, occurred_at, trigger FROM evolution_events ORDER BY id DESC LIMIT 50"
        ).fetchall()
        evolution_log = [
            {
                "from_form": r["from_form"],
                "to_form": r["to_form"],
                "occurred_at": r["occurred_at"],
                "trigger": r["trigger"],
            }
            for r in rows
        ]
    except Exception:
        pass
    return {
        "ok": True,
        "form": current_form,
        "evolution_log": evolution_log,
    }


# ── Mood ──────────────────────────────────────────────────────────────


class MoodPayload(BaseModel):
    mood: str


@router.post("/mood")
def set_mood(payload: MoodPayload):
    from nexusmon.entity import VALID_MOODS

    normalized = str(payload.mood).upper()
    if normalized not in VALID_MOODS:
        return {"ok": False, "error": f"Invalid mood. Valid: {sorted(VALID_MOODS)}"}
    _entity().set_mood(normalized)
    return {"ok": True, "mood": normalized}


# ── Operator profile ──────────────────────────────────────────────────


@router.get("/operator/{operator_id}")
def get_operator_profile(operator_id: str):
    profile = _entity().get_operator_profile(operator_id)
    return {"ok": True, "profile": profile}
