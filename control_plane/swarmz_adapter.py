# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
swarmz_adapter.py â€“ Adapter abstraction for interfacing with the swarmz system.

This is the *in-process* version: it simply applies actions by emitting state
updates back into the control plane.  A future version can replace this with
an HTTP or gRPC adapter without changing the rest of the system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state_store import StateStore
    from .event_debouncer import EventDebouncer


class SwarmzAdapter:
    """In-process adapter that translates ACTION decisions into state updates."""

    def __init__(self, state_store: "StateStore", bus: "EventDebouncer"):
        self._state = state_store
        self._bus = bus

    def execute(self, action: dict) -> bool:
        """Apply *action*'s expected effects by writing state records.

        Returns ``True`` on success.
        """
        now = datetime.now(timezone.utc).isoformat()
        for eff in action.get("expected_effects", []):
            var = eff["variable"]
            delta = eff.get("delta", 0)
            current = self._state.get_value(var, 0)
            new_val = current + delta
            parts = var.split(".", 1)
            layer = parts[0] if len(parts) > 1 else "unknown"
            self._state.put({
                "layer": layer,
                "variable": var,
                "value": new_val,
                "units": "abstract",
                "time": now,
                "confidence": 0.9,
                "directionality": "up" if delta >= 0 else "down",
                "source": f"adapter:{action.get('action_id', 'unknown')}",
            })
        self._bus.publish("ACTION_EXECUTED", action)
        return True

