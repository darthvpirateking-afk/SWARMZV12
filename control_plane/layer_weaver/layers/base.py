"""
base.py – Abstract base class for all Layer-Weaver layers.

Each layer:
  - Declares owned state variables
  - Provides collect() returning STATE records
  - Can react to events
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List


class BaseLayer(ABC):
    """Abstract base for all layers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Layer name used in STATE records."""
        ...

    @property
    @abstractmethod
    def variables(self) -> List[str]:
        """List of state variable names this layer owns."""
        ...

    @abstractmethod
    def collect(self) -> List[dict]:
        """Return fresh STATE records for all owned variables."""
        ...

    def on_event(self, event_type: str, payload: Any):
        """Optional event handler (override to react)."""
        pass

    @staticmethod
    def make_record(
        layer: str,
        variable: str,
        value: Any,
        units: str = "abstract",
        confidence: float = 0.8,
        directionality: str = "neutral",
        source: str = "",
    ) -> dict:
        """Helper to build a valid STATE record."""
        return {
            "layer": layer,
            "variable": variable,
            "value": value,
            "units": units,
            "time": datetime.now(timezone.utc).isoformat(),
            "confidence": confidence,
            "directionality": directionality,
            "source": source or f"layer:{layer}",
        }
