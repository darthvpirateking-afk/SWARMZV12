"""
Swarm Internal Protocol — multi-agent consistency.

All internal agents communicate via structured packets only:
  intent / context / constraints / plan / artifact / verification / result.

Only one "voice" talks to the user; others are packet-only.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SwarmPacket:
    """Structured communication packet between internal agents."""

    __slots__ = (
        "packet_id", "source", "target", "packet_type",
        "intent", "context", "constraints", "plan",
        "artifact", "verification", "result", "timestamp",
    )

    VALID_TYPES = {"intent", "context", "constraints", "plan", "artifact", "verification", "result"}

    def __init__(
        self,
        source: str,
        target: str,
        packet_type: str,
        *,
        intent: str = "",
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        plan: Optional[Dict[str, Any]] = None,
        artifact: Optional[Dict[str, Any]] = None,
        verification: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
    ):
        if packet_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid packet type: {packet_type}")
        self.packet_id = str(uuid.uuid4())[:8]
        self.source = source
        self.target = target
        self.packet_type = packet_type
        self.intent = intent
        self.context = context or {}
        self.constraints = constraints or {}
        self.plan = plan or {}
        self.artifact = artifact or {}
        self.verification = verification or {}
        self.result = result or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "source": self.source,
            "target": self.target,
            "packet_type": self.packet_type,
            "intent": self.intent,
            "context": self.context,
            "constraints": self.constraints,
            "plan": self.plan,
            "artifact": self.artifact,
            "verification": self.verification,
            "result": self.result,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwarmPacket":
        pkt = cls(
            source=data["source"],
            target=data["target"],
            packet_type=data["packet_type"],
            intent=data.get("intent", ""),
            context=data.get("context"),
            constraints=data.get("constraints"),
            plan=data.get("plan"),
            artifact=data.get("artifact"),
            verification=data.get("verification"),
            result=data.get("result"),
        )
        pkt.packet_id = data.get("packet_id", pkt.packet_id)
        pkt.timestamp = data.get("timestamp", pkt.timestamp)
        return pkt


class PacketBus:
    """In-process message bus for swarm agents.  Append-only log."""

    def __init__(self):
        self._log: List[Dict[str, Any]] = []

    def send(self, packet: SwarmPacket) -> str:
        self._log.append(packet.to_dict())
        return packet.packet_id

    def receive(self, target: str, since: int = 0) -> List[Dict[str, Any]]:
        return [
            p for p in self._log[since:]
            if p["target"] == target
        ]

    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._log[-limit:]

    def dump_json(self) -> str:
        return json.dumps(self._log, indent=2)
