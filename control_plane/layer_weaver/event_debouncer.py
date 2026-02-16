"""
event_debouncer.py – In-process event bus with debouncing.

Events are string names. Subscribers register callbacks; the debouncer
coalesces rapid-fire events so each handler fires at most once per
*window* seconds. Also supports internal queues for event routing.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, List, Optional

Callback = Callable[[str, Any], None]


class EventDebouncer:
    """Publish/subscribe event bus with per-event debouncing."""

    def __init__(self, window: float = 1.0):
        self._window = window
        self._subs: Dict[str, List[Callback]] = defaultdict(list)
        self._last_fire: Dict[str, float] = {}
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._queues: Dict[str, Deque[Any]] = defaultdict(deque)

    def subscribe(self, event: str, callback: Callback):
        """Register *callback* for *event*."""
        self._subs[event].append(callback)

    def publish(self, event: str, payload: Any = None):
        """Publish *event* with optional *payload* (debounced)."""
        with self._lock:
            now = time.monotonic()
            last = self._last_fire.get(event, 0.0)
            remaining = self._window - (now - last)

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

    def publish_immediate(self, event: str, payload: Any = None):
        """Publish without debouncing – always fires immediately."""
        with self._lock:
            self._last_fire[event] = time.monotonic()
        self._dispatch(event, payload)

    def enqueue(self, event: str, payload: Any):
        """Put payload into an internal queue for *event*."""
        self._queues[event].append(payload)

    def dequeue(self, event: str, timeout: float = 0) -> Optional[Any]:
        """Pop from the internal queue for *event* (non-blocking if timeout=0)."""
        deadline = time.monotonic() + timeout
        while True:
            try:
                return self._queues[event].popleft()
            except IndexError:
                if time.monotonic() >= deadline:
                    return None
                time.sleep(0.05)

    def _deferred(self, event: str, payload: Any):
        with self._lock:
            self._last_fire[event] = time.monotonic()
            self._timers.pop(event, None)
        self._dispatch(event, payload)

    def _dispatch(self, event: str, payload: Any):
        for cb in self._subs.get(event, []):
            try:
                cb(event, payload)
            except Exception as exc:
                import sys
                import traceback
                print(f"[EventDebouncer] handler error for {event}: {exc}",
                      file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
