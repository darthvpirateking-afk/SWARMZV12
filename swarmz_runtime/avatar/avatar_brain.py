from __future__ import annotations

from typing import Any


class AvatarBrain:
    """Canonical runtime command parser for avatar actions."""

    def parse_command(self, command: Any) -> dict[str, Any]:
        token = str(command or "").strip()
        return {
            "type": "create",
            "payload": {
                "command": token,
            },
        }
