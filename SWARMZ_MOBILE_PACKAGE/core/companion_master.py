# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/companion_master.py â€” MASTER SWARMZ companion orchestrator.

Higherâ€‘level layer over core/companion.py.  Owns:
  data/companion_master.json   â€” master identity + evolution counters
  data/companion_state.json    â€” current operational state (loaded by EvolutionMemory too)
  data/companion_memory.json   â€” session memory (managed by companion.py)

Responsibilities:
  1. Initialise master identity on first run (idempotent).
  2. Provide composite companion context for AI calls (merges master + state + memory).
  3. Record mission observations (delegate to companion.record_mission_outcome + self counters).
  4. Produce a selfâ€‘assessment (deterministic, for daily brief).

Policy: PREPAREâ€‘ONLY. Never autoâ€‘executes. Respects read_only flag.
"""

import json
from pathlib import Path
from typing import Any, Dict

from core.time_source import now
from core.atomic import atomic_write_json

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MASTER_FILE = DATA_DIR / "companion_master.json"


def _load_master() -> Dict[str, Any]:
    if MASTER_FILE.exists():
        try:
            return json.loads(MASTER_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    default = {
        "identity": "MASTER_SWARMZ",
        "personality_anchor": "calm_analytical",
        "created_at": now(),
        "epochs_completed": 0,
        "total_missions_witnessed": 0,
        "last_insight": None,
        "policy": "active",
    }
    atomic_write_json(MASTER_FILE, default)
    return default


def _save_master(data: Dict[str, Any]) -> None:
    data["updated_at"] = now()
    atomic_write_json(MASTER_FILE, data)


def ensure_master() -> Dict[str, Any]:
    """Ensure master identity exists. Returns current master data."""
    return _load_master()


def rename_master(new_name: str) -> Dict[str, Any]:
    """Set a custom display name for the master companion. Returns updated master data."""
    master = _load_master()
    master["display_name"] = new_name.strip()[:64]
    _save_master(master)
    return master


def get_display_name() -> str:
    """Return the companion's current display name (falls back to identity)."""
    master = _load_master()
    return master.get("display_name") or master.get("identity", "MASTER SWARMZ")


def record_mission_observed(
    mission_id: str, intent: str, status: str, summary: str = ""
) -> None:
    """Increment the master mission counter and delegate to companion memory."""
    master = _load_master()
    master["total_missions_witnessed"] = master.get("total_missions_witnessed", 0) + 1
    master["last_mission_id"] = mission_id
    master["last_mission_status"] = status
    _save_master(master)

    # Delegate to companion.py for detailed memory
    try:
        from core.companion import record_mission_outcome

        record_mission_outcome(mission_id, intent, status, summary)
    except Exception:
        pass


def record_epoch(epoch_number: int) -> None:
    """Called by EvolutionMemory when a new epoch is emitted."""
    master = _load_master()
    master["epochs_completed"] = epoch_number
    _save_master(master)


def record_insight(text: str) -> None:
    """Store a singleâ€‘line insight from the companion AI (e.g. pattern detected)."""
    master = _load_master()
    master["last_insight"] = text[:500]
    master["last_insight_at"] = now()
    _save_master(master)


def get_composite_context() -> Dict[str, Any]:
    """Build a merged context dict for AI prompts.

    Merges: master identity + companion_state + companion_memory (summary only).
    """
    master = _load_master()

    # companion state
    state_p = DATA_DIR / "companion_state.json"
    state: Dict[str, Any] = {}
    if state_p.exists():
        try:
            state = json.loads(state_p.read_text(encoding="utf-8"))
        except Exception:
            pass

    # companion memory (only summary + recent outcomes to keep context small)
    mem_p = DATA_DIR / "companion_memory.json"
    mem: Dict[str, Any] = {}
    if mem_p.exists():
        try:
            mem = json.loads(mem_p.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "master_identity": master.get("identity"),
        "personality_anchor": master.get("personality_anchor"),
        "policy": master.get("policy", "active"),
        "epochs_completed": master.get("epochs_completed", 0),
        "total_missions_witnessed": master.get("total_missions_witnessed", 0),
        "last_insight": master.get("last_insight"),
        "confidence_level": state.get("confidence_level", 0.5),
        "preferred_strategies": list(state.get("preferred_strategies", {}).keys()),
        "recent_failures_count": len(state.get("recent_failures", [])),
        "memory_summary": mem.get("summary", ""),
        "recent_outcomes": mem.get("mission_outcomes", [])[-5:],
        "learned_constraints": mem.get("learned_constraints", [])[-10:],
    }


def self_assessment() -> str:
    """Produce a deterministic selfâ€‘assessment paragraph (for daily brief)."""
    ctx = get_composite_context()
    lines = []
    lines.append(f"Identity: {ctx['master_identity']}")
    lines.append(f"Total missions witnessed: {ctx['total_missions_witnessed']}")
    lines.append(f"Epochs completed: {ctx['epochs_completed']}")
    lines.append(f"Confidence: {ctx['confidence_level']:.2f}")
    fail_count = ctx["recent_failures_count"]
    if fail_count > 3:
        lines.append(f"WARNING: {fail_count} recent failures â€” consider stabilising.")
    elif fail_count == 0:
        lines.append("No recent failures â€” clear for progression.")
    if ctx["last_insight"]:
        lines.append(f"Last insight: {ctx['last_insight']}")
    lines.append(f"Policy: {ctx['policy']}")
    return "\n".join(lines)
