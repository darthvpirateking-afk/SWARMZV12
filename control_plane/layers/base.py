"""
layers/base.py – Abstract base class for all layer modules.

A layer is responsible for:
  1. Declaring the state variables it owns.
  2. Providing a ``collect()`` method that returns fresh STATE records.
  3. Optionally reacting to events.
"""

from __future__ import annotations

import abc
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state_store import StateStore
    from ..event_debouncer import EventDebouncer


class BaseLayer(abc.ABC):
    """Abstract base for every layer module."""

    name: str = "base"

    def __init__(self, state_store: "StateStore", bus: "EventDebouncer"):
        self._state = state_store
        self._bus = bus

    @abc.abstractmethod
    def variables(self) -> list[str]:
        """Return the list of variable names owned by this layer."""

    @abc.abstractmethod
    def collect(self) -> list[dict]:
        """Return fresh STATE records for each variable."""

    def _make_record(self, variable: str, value, units: str = "abstract",
                     confidence: float = 1.0,
                     directionality: str = "stable") -> dict:
        return {
            "layer": self.name,
            "variable": variable,
            "value": value,
            "units": units,
            "time": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "directionality": directionality,
            "source": f"layer:{self.name}",
        }
