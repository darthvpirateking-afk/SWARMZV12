from __future__ import annotations

from typing import Any

from swarmz_runtime.avatar.avatar_state import AvatarState


class AvatarPresence:
    """Canonical runtime projection layer for cockpit/system surfaces."""

    def surface_system_state(self, state: Any) -> str:
        return f"System State: {state}"

    def render(self, state: AvatarState) -> dict[str, Any]:
        return {
            "avatar_state": dict(state.avatar_form),
            "mission_context": dict(state.mission_context),
        }
