# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
regime.py â€“ Regime-based objectives with hysteresis.

Each objective belongs to a regime.  A regime becomes *active* when its entry
condition is met and stays active for at least ``min_duration_active`` seconds.
After exiting it enters a cooldown of ``cooldown_after_exit`` seconds during
which it cannot reactivate.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import jsonschema

from .expression_eval import evaluate

_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_DIR, "data", "objectives.json")) as _f:
    _OBJECTIVES: list[dict] = json.load(_f)

with open(os.path.join(_DIR, "schemas", "objective.schema.json")) as _f:
    _OBJ_SCHEMA = json.load(_f)

for obj in _OBJECTIVES:
    jsonschema.validate(instance=obj, schema=_OBJ_SCHEMA)


@dataclass
class _RegimeState:
    active: bool = False
    activated_at: float = 0.0
    deactivated_at: float = 0.0


class RegimeManager:
    """Manages objective regimes with hysteresis."""

    def __init__(self, objectives: list[dict] | None = None):
        self._objectives = objectives or _OBJECTIVES
        # regime_name -> _RegimeState
        self._regimes: dict[str, _RegimeState] = {}
        for obj in self._objectives:
            rname = obj["regime"]
            self._regimes.setdefault(rname, _RegimeState())

    def active_objectives(self, state_getter) -> list[dict]:
        """Return objectives whose regime is currently active given *state_getter*.

        *state_getter* is a callable ``(variable) -> value | None`` that looks
        up the latest value for a state variable.
        """
        now = time.monotonic()
        active: list[dict] = []
        for obj in self._objectives:
            rs = self._regimes[obj["regime"]]
            current = state_getter(obj["goal_variable"])
            met = False
            if current is not None:
                met = evaluate(obj["operator"], current, obj["target"])

            if met and not rs.active:
                # Check cooldown (deactivated_at == 0 means never deactivated)
                cooldown_elapsed = (rs.deactivated_at == 0.0
                                    or now - rs.deactivated_at >= obj.get("cooldown_after_exit", 0))
                if cooldown_elapsed:
                    rs.active = True
                    rs.activated_at = now
            elif not met and rs.active:
                # Hysteresis: keep active for min_duration
                if now - rs.activated_at >= obj.get("min_duration_active", 0):
                    rs.active = False
                    rs.deactivated_at = now

            if rs.active:
                active.append(obj)

        return active

    def all_regimes(self) -> dict[str, bool]:
        """Return a snapshot of regime activation states."""
        return {name: rs.active for name, rs in self._regimes.items()}

