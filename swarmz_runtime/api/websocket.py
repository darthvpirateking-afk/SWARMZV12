# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""WebSocket connection manager and cockpit WS endpoint."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("swarmz.ws")

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages active WebSocket connections with channel-based broadcasting."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channels: list[str] | None = None):
        await ws.accept()
        self._connections.add(ws)
        for ch in channels or ["*"]:
            self._channels.setdefault(ch, set()).add(ws)
        logger.info("WS client connected (%d total)", len(self._connections))

    def disconnect(self, ws: WebSocket):
        self._connections.discard(ws)
        for subscribers in self._channels.values():
            subscribers.discard(ws)
        logger.info("WS client disconnected (%d remaining)", len(self._connections))

    async def broadcast(self, channel: str, data: Dict[str, Any]):
        """Send a message to all subscribers of a channel (and wildcard)."""
        message = json.dumps(
            {
                "channel": channel,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        targets = self._channels.get(channel, set()) | self._channels.get("*", set())
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_personal(self, ws: WebSocket, data: Dict[str, Any]):
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            self.disconnect(ws)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Singleton manager
manager = ConnectionManager()


@router.websocket("/ws/cockpit")
async def cockpit_ws(ws: WebSocket):
    """Main cockpit WebSocket endpoint.

    Clients may send JSON messages with:
        {"subscribe": ["missions", "system", "evolution"]}
    to subscribe to specific channels. Default is wildcard (*).
    """
    channels = ["*"]

    await manager.connect(ws, channels)
    await manager.send_personal(
        ws,
        {
            "type": "welcome",
            "message": "Connected to SWARMZ cockpit",
            "channels": channels,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal(ws, {"type": "error", "detail": "invalid JSON"})
                continue

            # Handle subscription changes
            if "subscribe" in msg and isinstance(msg["subscribe"], list):
                for ch in msg["subscribe"]:
                    manager._channels.setdefault(ch, set()).add(ws)
                channels = list(set(channels) | set(msg["subscribe"]))
                await manager.send_personal(
                    ws, {"type": "subscribed", "channels": channels}
                )

            # Handle ping
            elif msg.get("type") == "ping":
                await manager.send_personal(ws, {"type": "pong"})

            # Echo anything else back for now
            else:
                await manager.send_personal(
                    ws, {"type": "echo", "received": msg}
                )

    except WebSocketDisconnect:
        manager.disconnect(ws)
