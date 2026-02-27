"""event_bus.py — Public re-export of SimpleEventBus as EventBus.

Provides a stable import path (`core.event_bus.EventBus`) independent of
the internal agent_runtime module layout.
"""

from core.agent_runtime import SimpleEventBus as EventBus

__all__ = ["EventBus"]
