from __future__ import annotations

from typing import Any


class AvatarState:
    """Canonical runtime avatar state container."""

    def __init__(self) -> None:
        self.avatar_form: dict[str, Any] = {}
        self.mission_context: dict[str, Any] = {}

    def update_state(self, key: str, value: Any) -> None:
        self.avatar_form[str(key)] = value

    def get_state(self) -> dict[str, Any]:
        return dict(self.avatar_form)
