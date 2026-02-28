from __future__ import annotations


class ShadowKnight:
    summon_id = "ShadowKnight"
    tier = "monarch"
    aura = "shadow-cosmic"

    def __init__(self) -> None:
        self.last_command = "idle"

    def obey(self, command: str) -> dict[str, str]:
        self.last_command = str(command or "idle")
        return {
            "summon": self.summon_id,
            "tier": self.tier,
            "aura": self.aura,
            "command": self.last_command,
        }

    def execute(self, command: str) -> dict[str, str]:
        return self.obey(command)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.summon_id,
            "tier": self.tier,
            "aura": self.aura,
            "last_command": self.last_command,
        }
