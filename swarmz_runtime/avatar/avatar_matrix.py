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
from swarmz_runtime.avatar.evolution_controller import (
    EvolutionController,
    RankSystemAdapter,
    WitnessLogger,
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
        self.rank_system = RankSystemAdapter()
        self.witness = WitnessLogger()
        self.evolution = EvolutionController(self, self.rank_system, self.witness)
        self.current_form = self.evolution.current_form

    def get_evolution_state(self) -> dict[str, Any]:
        rank = self.rank_system.refresh_rank()
        self.current_form = self.evolution.current_form
        next_form = self.evolution.get_next_form()
        can_evolve = self.evolution.can_evolve_to(next_form) if next_form else False
        return {
            "current_form": self.current_form,
            "next_form": next_form,
            "rank": rank,
            "can_evolve": can_evolve,
            "sovereign_unlocked": self.rank_system.rank_at_least("Sovereign"),
            "monarch_available": self.evolution.can_enter_monarch_mode(),
        }

    def get_matrix_state(self) -> dict[str, Any]:
        evolution_state = self.get_evolution_state()
        return {
            "operator_rank": self._operator_rank,
            "active_variant": self._active_variant,
            "current_state": self._current_state,
            "current_form": evolution_state["current_form"],
            "available_variants": list(AVATAR_VARIANTS.keys()),
            "valid_states": sorted(_VALID_STATES),
            "evolution": evolution_state,
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

    def operator_trigger(self, command: str) -> bool:
        transitioned = self.evolution.operator_trigger(command)
        self.current_form = self.evolution.current_form
        return transitioned


_matrix: AvatarMatrix | None = None


def get_avatar_matrix() -> AvatarMatrix:
    global _matrix
    if _matrix is None:
        _matrix = AvatarMatrix()
    return _matrix
