"""
swarmz_adapter.py – Adapter abstraction for interfacing with the swarmz system.

Defines the SwarmzAdapter interface:
  - publish(task)          → task_id
  - poll_result(task_id)   → result dict
  - emit_event(event_type, payload)

Includes InProcessSwarmzBus for local/dev execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .event_debouncer import EventDebouncer


class SwarmzAdapter:
    """Abstract adapter for swarmz task execution and event emission."""

    def publish(self, task: dict) -> str:
        raise NotImplementedError

    def poll_result(self, task_id: str, timeout_seconds: float = 5.0) -> Optional[dict]:
        raise NotImplementedError

    def emit_event(self, event_type: str, payload: dict):
        raise NotImplementedError


class InProcessSwarmzBus(SwarmzAdapter):
    """In-process adapter that simulates task execution locally.

    Actions are applied by modifying state values through the state_store.
    Events are emitted to the EventDebouncer bus.
    """

    def __init__(self, state_store, bus: EventDebouncer):
        self._state = state_store
        self._bus = bus
        self._tasks: Dict[str, dict] = {}

    def publish(self, task: dict) -> str:
        """Simulate task execution: apply expected effects to state."""
        task_id = task.get("task_id") or str(uuid.uuid4())[:12]
        action = task.get("action", task)
        now = datetime.now(timezone.utc).isoformat()

        for eff in action.get("expected_effects", []):
            var = eff["variable"]
            delta = eff.get("delta", 0)
            current = self._state.get_latest_value(var, 0)
            new_val = current + delta
            parts = var.split(".", 1)
            layer = action.get(
                "target_layer", parts[0] if len(parts) > 1 else "unknown"
            )
            self._state.append(
                {
                    "layer": layer,
                    "variable": var,
                    "value": new_val,
                    "units": eff.get("units", "abstract"),
                    "time": now,
                    "confidence": eff.get("confidence", 0.8),
                    "directionality": "neutral",
                    "source": f"adapter:{action.get('id', 'unknown')}",
                }
            )

        result = {
            "task_id": task_id,
            "status": "completed",
            "action_id": action.get("id"),
        }
        self._tasks[task_id] = result
        self._bus.publish_immediate("ACTION_EXECUTED", result)
        return task_id

    def poll_result(self, task_id: str, timeout_seconds: float = 5.0) -> Optional[dict]:
        return self._tasks.get(task_id)

    def emit_event(self, event_type: str, payload: dict):
        self._bus.publish_immediate(event_type, payload)
