from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, DefaultDict, Dict, List


SUPPORTED_EVENTS: tuple[str, ...] = (
    "invoke",
    "consult",
    "interpret",
    "generate_geometry",
    "trigger_anomaly",
    "resolve_correspondence",
    "render_altar_mode",
    "simulate_branch",
)


@dataclass
class RuntimeEvent:
    event_type: str
    payload: Dict[str, Any]
    created_at: str


class RuntimeEventBus:
    """
    Deterministic in-process event bus for unified runtime hooks.
    """

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[RuntimeEvent], None]]] = (
            defaultdict(list)
        )
        self._history: List[RuntimeEvent] = []

    def subscribe(self, event_type: str, callback: Callable[[RuntimeEvent], None]) -> None:
        if event_type not in SUPPORTED_EVENTS:
            raise ValueError(f"unsupported event type: {event_type}")
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> RuntimeEvent:
        if event_type not in SUPPORTED_EVENTS:
            raise ValueError(f"unsupported event type: {event_type}")
        event = RuntimeEvent(
            event_type=event_type,
            payload=dict(payload),
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self._history.append(event)
        for callback in self._subscribers[event_type]:
            callback(event)
        return event

    def history(self, limit: int = 200) -> List[RuntimeEvent]:
        if limit <= 0:
            return []
        return self._history[-limit:]


EVENT_BUS = RuntimeEventBus()

