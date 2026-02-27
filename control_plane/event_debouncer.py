# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
event_debouncer.py â€“ Simple in-process event bus with debouncing.

Events are string names (e.g. ``STATE_UPDATED``, ``ACTION_SELECTED``).
Subscribers register callbacks; the debouncer coalesces rapid-fire events
so each handler fires at most once per *window* seconds.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any, Callable

Callback = Callable[[str, Any], None]


class EventDebouncer:
    """Publish/subscribe event bus with per-event debouncing."""

    def __init__(self, window: float = 1.0):
        self._window = window
        self._subs: dict[str, list[Callback]] = defaultdict(list)
        self._last_fire: dict[str, float] = {}
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def subscribe(self, event: str, callback: Callback):
        """Register *callback* for *event*."""
        self._subs[event].append(callback)

    def publish(self, event: str, payload: Any = None):
        """Publish *event* with optional *payload* (debounced)."""
        with self._lock:
            now = time.monotonic()
            last = self._last_fire.get(event, 0.0)
            remaining = self._window - (now - last)

            # Cancel any pending timer for this event
            existing = self._timers.pop(event, None)
            if existing:
                existing.cancel()

            if remaining <= 0:
                self._last_fire[event] = now
                self._dispatch(event, payload)
            else:
                t = threading.Timer(remaining, self._deferred, args=(event, payload))
                t.daemon = True
                self._timers[event] = t
                t.start()

    def _deferred(self, event: str, payload: Any):
        with self._lock:
            self._last_fire[event] = time.monotonic()
            self._timers.pop(event, None)
        self._dispatch(event, payload)

    def _dispatch(self, event: str, payload: Any):
        for cb in self._subs.get(event, []):
            try:
                cb(event, payload)
            except Exception as exc:  # noqa: BLE001
                import sys
                import traceback

                print(
                    f"[EventDebouncer] handler error for {event}: {exc}",
                    file=sys.stderr,
                )
                traceback.print_exc(file=sys.stderr)
