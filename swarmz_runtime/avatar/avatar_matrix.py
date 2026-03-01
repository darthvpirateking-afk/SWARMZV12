# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Avatar Matrix — SWARMZ V3.0 management layer over avatar instances.

Routes operator interactions to the correct avatar variant and tracks
global avatar state for the cockpit.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarmz_runtime.avatar.avatar_omega import (
    AvatarInfinity,
    AvatarOmega,
    AvatarOmegaPlus,
)
from swarmz_runtime.avatar.abilities.battle_chip_engine import (
    BattleChipEngine,
    ChipWitnessLogger,
)
from swarmz_runtime.avatar.avatar_combat import resolve_combat_profile
from swarmz_runtime.avatar.evolution_controller import (
    EvolutionController,
    RankSystemAdapter,
    WitnessLogger,
)
from swarmz_runtime.avatar.forms.avatar_monarch import AvatarMonarch
from swarmz_runtime.avatar.operator_link import OperatorLink
from swarmz_runtime.avatar.summons.summon_engine import SummonEngine, SummonWitnessLogger

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
        self.operator_link = OperatorLink(self)
        self.monarch_form = AvatarMonarch()
        self._voice_lines = self._load_voice_lines()
        self._monarch_profile = self._load_monarch_profile()
        self.summons = SummonEngine(avatar=self, witness=SummonWitnessLogger())
        self._monarch_summons = [
            self.summons.registry["ShadowKnight"],
            self.summons.registry["ShadowArcher"],
            self.summons.registry["ShadowMage"],
            self.summons.registry["ShadowColossus"],
        ]
        self.battle_chip_engine = BattleChipEngine(
            avatar=self,
            witness=ChipWitnessLogger(),
        )

    @staticmethod
    def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return dict(default)

    def _load_voice_lines(self) -> dict[str, dict[str, str]]:
        path = Path("swarmz_runtime/avatar/voice_lines.json")
        data = self._read_json(path, {})
        return data if isinstance(data, dict) else {}

    def _load_monarch_profile(self) -> dict[str, Any]:
        path = Path("swarmz_runtime/avatar/visuals/monarch_profile.json")
        data = self._read_json(path, {})
        return data if isinstance(data, dict) else {}

    def _active_summons(self) -> list[dict[str, str]]:
        return [summon.to_dict() for summon in self.summons.active_summons]

    def get_monarch_state(self) -> dict[str, Any]:
        active = self.current_form == "AvatarMonarch"
        summons = self._active_summons()
        if active and not summons:
            summons = [summon.to_dict() for summon in self._monarch_summons]
        return {
            "active": active,
            "profile": self._monarch_profile if active else {},
            "summons": summons if active else [],
        }

    def get_chip_state(self) -> dict[str, Any]:
        return self.battle_chip_engine.get_state()

    def get_voice_line(self, event: str) -> str:
        event_key = str(event or "").strip().lower()
        if not event_key:
            return ""
        form_lines = self._voice_lines.get(self.current_form, {})
        if not form_lines:
            form_lines = self._voice_lines.get("AvatarOmega", {})
        value = form_lines.get(event_key) or form_lines.get(event_key.upper())
        return str(value) if value is not None else ""

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
            "monarch_available": self.evolution.can_enter_monarch_mode() or self.current_form == "AvatarMonarch",
        }

    def get_matrix_state(self) -> dict[str, Any]:
        evolution_state = self.get_evolution_state()
        monarch_state = self.get_monarch_state()
        combat_profile = resolve_combat_profile(self.current_form)
        return {
            "operator_rank": self._operator_rank,
            "active_variant": self._active_variant,
            "current_state": self._current_state,
            "current_form": evolution_state["current_form"],
            "available_variants": list(AVATAR_VARIANTS.keys()),
            "valid_states": sorted(_VALID_STATES),
            "evolution": evolution_state,
            "monarch_mode": monarch_state["active"],
            "active_summons": monarch_state["summons"],
            "abilities": {
                "unlocked": combat_profile.get("abilities", []),
                "combat_profile": combat_profile,
            },
            "chip_state": self.get_chip_state(),
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
        outcome = self.handle_operator_command(command)
        return bool(outcome.get("transitioned") or outcome.get("executed"))

    def handle_operator_command(self, command: str) -> dict[str, Any]:
        result = self.operator_link.execute_command(command)
        self.current_form = self.evolution.current_form
        return result


_matrix: AvatarMatrix | None = None


def get_avatar_matrix() -> AvatarMatrix:
    global _matrix
    if _matrix is None:
        _matrix = AvatarMatrix()
    return _matrix
