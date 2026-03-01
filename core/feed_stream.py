"""feed_stream.py — FeedStream wraps an EventBus for hologram ingestor consumers.

FeedStream subscribes to an EventBus and re-exposes a `subscribe` interface so
that downstream consumers (e.g. HologramIngestor) stay decoupled from the raw
bus implementation.
"""

from __future__ import annotations


class FeedStream:
    """Thin adapter that exposes a stable `.subscribe(callback)` interface over
    any EventBus-compatible object (must have `.subscribe(fn)` and `.publish(event)`).
    """

    def __init__(self, event_bus) -> None:
        self._bus = event_bus
        self._subscribers: list = []

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def subscribe(self, callback) -> None:
        """Register a callback that receives every event published to the bus."""
        self._subscribers.append(callback)
        self._bus.subscribe(callback)

    def publish(self, event: dict) -> None:
        """Forward a publish to the underlying bus (convenience for tests)."""
        self._bus.publish(event)

    # ------------------------------------------------------------------ #
    # Passthrough helpers                                                  #
    # ------------------------------------------------------------------ #

    def recent(self, n: int = 50):
        """Return the most recent n events from the underlying bus."""
        return self._bus.recent(n)


__all__ = ["FeedStream"]
