from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SummonBase:
    id: str
    name: str
    tier: str
    form_required: str
    stats: dict[str, float] = field(default_factory=dict)
    aura: str = "neutral"
    visual_profile: dict[str, Any] = field(default_factory=dict)
    last_command: str = "idle"

    def on_spawn(self) -> dict[str, Any]:
        self.last_command = "spawned"
        return {"summon": self.id, "event": "spawn"}

    def on_dismiss(self) -> dict[str, Any]:
        self.last_command = "dismissed"
        return {"summon": self.id, "event": "dismiss"}

    def on_command(self, cmd: str) -> dict[str, Any]:
        self.last_command = str(cmd or "idle")
        return {"summon": self.id, "event": "command", "command": self.last_command}

    def obey(self, command: str) -> dict[str, Any]:
        return self.on_command(command)

    def execute(self, command: str) -> dict[str, Any]:
        return self.on_command(command)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier,
            "form_required": self.form_required,
            "stats": dict(self.stats),
            "aura": self.aura,
            "visual_profile": dict(self.visual_profile),
            "last_command": self.last_command,
        }
