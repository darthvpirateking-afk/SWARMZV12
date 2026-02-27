"""
regime.py – Regime-based objectives with hysteresis.

Each objective defines:
  - activation_condition: safe expression evaluated against latest state
  - hysteresis: min_duration_active + cooldown_after_exit
  - priority: lower number = higher priority

The RegimeManager tracks which objectives are active, enforcing hysteresis
to prevent oscillation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from .expression_eval import safe_eval


class RegimeManager:
    """Manages regime-based objectives with hysteresis."""

    def __init__(self):
        self._active: Dict[str, float] = {}  # obj_id → activated_at (monotonic)
        self._cooldowns: Dict[str, float] = {}  # obj_id → cooldown_until (monotonic)

    def evaluate(
        self, objectives: List[dict], state_values: Dict[str, Any]
    ) -> List[dict]:
        """Return list of currently active objectives (respecting hysteresis).

        *objectives* come from the objectives config.
        *state_values* is {variable_name: value} from latest state.
        """
        now = time.monotonic()
        active: List[dict] = []

        for obj in objectives:
            oid = obj["id"]
            condition = obj.get("activation_condition", "True")
            hysteresis = obj.get("hysteresis", {})
            min_duration = hysteresis.get("min_duration_active", 0)
            cooldown = hysteresis.get("cooldown_after_exit", 0)

            cond_met = safe_eval(condition, state_values)

            if oid in self._active:
                # Currently active
                elapsed = now - self._active[oid]
                if cond_met or elapsed < min_duration:
                    # Stay active
                    active.append(obj)
                else:
                    # Deactivate
                    del self._active[oid]
                    self._cooldowns[oid] = now + cooldown
            else:
                # Currently inactive
                cool_until = self._cooldowns.get(oid, 0)
                if cond_met and now >= cool_until:
                    # Activate
                    self._active[oid] = now
                    active.append(obj)
                    self._cooldowns.pop(oid, None)

        # Sort by priority (lower = higher)
        active.sort(key=lambda o: o.get("priority", 999))
        return active

    def is_active(self, objective_id: str) -> bool:
        return objective_id in self._active
