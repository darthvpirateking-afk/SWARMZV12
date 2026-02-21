# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Event bus for broadcasting state changes to WebSocket clients."""

import asyncio
import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger("swarmz.events")


class EventBus:
    """In-process event bus that dispatches to WebSocket manager and local callbacks."""

    def __init__(self):
        self._callbacks: Dict[str, List[Callable]] = {}

    def subscribe(self, channel: str, callback: Callable):
        self._callbacks.setdefault(channel, []).append(callback)

    def unsubscribe(self, channel: str, callback: Callable):
        if channel in self._callbacks:
            self._callbacks[channel] = [
                cb for cb in self._callbacks[channel] if cb is not callback
            ]

    async def emit(self, channel: str, data: Dict[str, Any]):
        """Emit an event to local subscribers and WebSocket clients."""
        # Local callbacks
        for cb in self._callbacks.get(channel, []):
            try:
                result = cb(channel, data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.warning("Event callback error on %s: %s", channel, exc)

        # WebSocket broadcast
        try:
            from swarmz_runtime.api.websocket import manager

            await manager.broadcast(channel, data)
        except Exception as exc:
            logger.debug("WS broadcast skipped: %s", exc)

    def emit_sync(self, channel: str, data: Dict[str, Any]):
        """Fire-and-forget emit for synchronous code paths."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(channel, data))
        except RuntimeError:
            # No event loop running — skip WS broadcast, run local only
            for cb in self._callbacks.get(channel, []):
                try:
                    cb(channel, data)
                except Exception:
                    pass


# Singleton
event_bus = EventBus()
