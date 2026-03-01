# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Avatar Matrix — SWARMZ V3.0 management layer over avatar instances.

Routes operator interactions to the correct avatar variant and tracks
global avatar state for the cockpit.
"""

from __future__ import annotations

from typing import Any

from swarmz_runtime.avatar.avatar_omega import (
    AvatarInfinity,
    AvatarOmega,
    AvatarOmegaPlus,
)

AVATAR_VARIANTS: dict[str, tuple[str, str]] = {
    "omega": ("AvatarOmega", "Standard SWARMZ avatar"),
    "infinity": ("AvatarInfinity", "Permanent operator-link capable avatar"),
    "omega_plus": (
        "AvatarOmegaPlus",
        "Cosmology-aware avatar with DSL mission interpretation",
    ),
}

_VALID_STATES: frozenset[str] = frozenset(
    {
        "neutral",
        "kind",
        "focused",
        "protector",
        "overclock",
        "operator-link",
        "shadow-alert",
    }
)


class AvatarMatrix:
    """Routes operator interactions to the correct avatar variant and tracks global state."""

    def __init__(self, operator_rank: str = "OPERATOR") -> None:
        self._operator_rank = operator_rank
        self._instances: dict[str, AvatarOmega] = {
            "omega": AvatarOmega(operator_rank),
            "infinity": AvatarInfinity(operator_rank),
            "omega_plus": AvatarOmegaPlus(operator_rank, "default"),
        }
        self._active_variant = "omega"
        self._current_state = "neutral"

    def get_matrix_state(self) -> dict[str, Any]:
        return {
            "operator_rank": self._operator_rank,
            "active_variant": self._active_variant,
            "current_state": self._current_state,
            "available_variants": list(AVATAR_VARIANTS.keys()),
            "valid_states": sorted(_VALID_STATES),
            "variants": {
                k: {"class": v[0], "description": v[1]}
                for k, v in AVATAR_VARIANTS.items()
            },
        }

    def set_state(self, state: str, variant: str | None = None) -> dict[str, Any]:
        if state not in _VALID_STATES:
            return {
                "ok": False,
                "error": f"Invalid state '{state}'. Valid: {sorted(_VALID_STATES)}",
            }
        target_variant = variant or self._active_variant
        if target_variant not in self._instances:
            return {"ok": False, "error": f"Unknown variant '{target_variant}'"}
        self._instances[target_variant].set_state(state)
        self._current_state = state
        if variant:
            self._active_variant = variant
        return {"ok": True, "variant": target_variant, "state": state}

    def switch_variant(self, variant: str) -> dict[str, Any]:
        if variant not in self._instances:
            return {"ok": False, "error": f"Unknown variant '{variant}'"}
        self._active_variant = variant
        return {"ok": True, "active_variant": variant}


_matrix: AvatarMatrix | None = None


def get_avatar_matrix() -> AvatarMatrix:
    global _matrix
    if _matrix is None:
        _matrix = AvatarMatrix()
    return _matrix
