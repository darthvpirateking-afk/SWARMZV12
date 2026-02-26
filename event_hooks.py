#!/usr/bin/env python3
"""
Event Hooks — Lifecycle hooks that fire when plugin events occur.
Auto-appends to timeline and emits to notification system.

Hooks:
  on_plugin_installed(plugin_id, url, dest)
  on_plugin_unlocked(plugin_id, operator_rank, operator_xp)
  on_xp_gain(amount, reason, plugin_id=None)
  on_rank_up(new_rank, operator_id)
  on_mission_complete(mission_id, reward_xp, completed_by=None)
  on_evolution(organism_id, old_stage, new_stage, trigger=None)
  on_system_event(event_type, message, severity='info')
"""

from timeline_store import append_event
from datetime import datetime
from typing import Optional, Dict, Any

# In-memory event buffer for real-time subscriptions (Phase 5 notifications)
_event_buffer = []
_max_buffer_size = 100


def _buffer_event(event_dict: Dict[str, Any]) -> None:
    """Add event to notification buffer for subscribers."""
    global _event_buffer
    _event_buffer.append(event_dict)
    if len(_event_buffer) > _max_buffer_size:
        _event_buffer.pop(0)


def on_plugin_installed(plugin_id: str, url: str, dest: str) -> Dict[str, Any]:
    """Fire when plugin is successfully installed."""
    event = {
        "id": plugin_id,
        "url": url,
        "destination": dest,
        "installed_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("plugin_installed", event)
    _buffer_event({**timeline_evt, "event_type": "plugin_installed"})
    print(f"[HOOK] Plugin installed: {plugin_id}")
    return timeline_evt


def on_plugin_unlocked(
    plugin_id: str, operator_rank: str, operator_xp: int
) -> Dict[str, Any]:
    """Fire when plugin is unlocked by operator."""
    event = {
        "id": plugin_id,
        "unlocked_by_rank": operator_rank,
        "operator_xp_at_unlock": operator_xp,
        "unlocked_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("plugin_unlocked", event)
    _buffer_event({**timeline_evt, "event_type": "plugin_unlocked"})
    print(f"[HOOK] Plugin unlocked: {plugin_id} (rank={operator_rank})")
    return timeline_evt


def on_xp_gain(
    amount: int, reason: str, plugin_id: Optional[str] = None
) -> Dict[str, Any]:
    """Fire when operator gains XP (from missions, tasks, etc.)."""
    event = {
        "amount": amount,
        "reason": reason,
        "from_plugin": plugin_id,
        "gained_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("xp_gain", event)
    _buffer_event({**timeline_evt, "event_type": "xp_gain"})
    print(f"[HOOK] XP gain: +{amount} ({reason})")
    return timeline_evt


def on_rank_up(new_rank: str, operator_id: Optional[str] = None) -> Dict[str, Any]:
    """Fire when operator ranks up (promotion)."""
    event = {
        "new_rank": new_rank,
        "operator_id": operator_id,
        "promoted_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("rank_up", event)
    _buffer_event({**timeline_evt, "event_type": "rank_up"})
    print(f"[HOOK] Rank up: {new_rank}")
    return timeline_evt


def on_mission_complete(
    mission_id: str, reward_xp: int, completed_by: Optional[str] = None
) -> Dict[str, Any]:
    """Fire when a mission is completed."""
    event = {
        "mission_id": mission_id,
        "reward_xp": reward_xp,
        "completed_by": completed_by,
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("mission_complete", event)
    _buffer_event({**timeline_evt, "event_type": "mission_complete"})
    print(f"[HOOK] Mission complete: {mission_id} (+{reward_xp} XP)")
    return timeline_evt


def on_evolution(
    organism_id: str, old_stage: str, new_stage: str, trigger: Optional[str] = None
) -> Dict[str, Any]:
    """Fire when organism evolves to a new stage."""
    event = {
        "organism_id": organism_id,
        "old_stage": old_stage,
        "new_stage": new_stage,
        "evolution_trigger": trigger,
        "evolved_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("evolution", event)
    _buffer_event({**timeline_evt, "event_type": "evolution"})
    print(f"[HOOK] Evolution: {old_stage} → {new_stage}")
    return timeline_evt


def on_system_event(
    event_type: str, message: str, severity: str = "info"
) -> Dict[str, Any]:
    """Fire for general system events (warnings, errors, milestones)."""
    event = {
        "type": event_type,
        "message": message,
        "severity": severity,
        "occurred_at": datetime.utcnow().isoformat() + "Z",
    }
    timeline_evt = append_event("system", event)
    _buffer_event({**timeline_evt, "event_type": "system"})
    print(f"[HOOK] System: {severity.upper()} - {event_type}: {message}")
    return timeline_evt


# ─────────────────────────────────────────────────────────────
# Notification Buffer API (Phase 5 ready)
# ─────────────────────────────────────────────────────────────


def get_event_buffer() -> list:
    """Return recent events for notifications."""
    return _event_buffer.copy()


def clear_event_buffer(keep_last_n: int = 10) -> None:
    """Clear buffer, optionally keeping last N events."""
    global _event_buffer
    if keep_last_n > 0:
        _event_buffer = _event_buffer[-keep_last_n:]
    else:
        _event_buffer = []


# ─────────────────────────────────────────────────────────────
# Wire hooks into plugin lifecycle
# ─────────────────────────────────────────────────────────────


def wire_hooks(nexusmon_plugins_router) -> None:
    """
    Optional: Wire hooks into nexusmon_plugins endpoints.
    Call this from swarmz_server.py after plugins router is registered.
    """
    # In the actual implementation, hooks are called directly from
    # nexusmon_plugins.py install_plugin() and unlock_plugin() routes.
    pass


if __name__ == "__main__":
    # Example hook usage
    on_plugin_installed(
        "scout-worker", "https://github.com/example/scout", "plugins/scout-worker"
    )
    on_xp_gain(100, "installed_plugin", "scout-worker")
    on_plugin_unlocked("parallel-node-v2", "C", 500)
    on_mission_complete("first-swarm", 250, "operator-001")
    on_evolution("nexusmon-v1", "larva", "pupa", "xp_threshold_reached")
    on_system_event("startup", "SWARMZ online and ready", "info")
    print(f"\nBuffer ({len(_event_buffer)} events):")
    for evt in _event_buffer:
        print(f"  {evt['type']}: {evt.get('payload', {})}")
