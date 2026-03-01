from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BattleChip:
    chip_id: str
    category: str
    min_form: str
    base_damage: float
    base_speed: float
    base_cost: float
    evolution_modifiers: dict[str, dict[str, float]]
    monarch_modifiers: dict[str, Any]
    visual_effect: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BattleChip":
        return cls(
            chip_id=str(payload.get("id", "")).strip(),
            category=str(payload.get("category", "unknown")).strip(),
            min_form=str(payload.get("min_form", "AvatarOmega")).strip(),
            base_damage=float(payload.get("base_damage", 0.0)),
            base_speed=float(payload.get("base_speed", 0.0)),
            base_cost=float(payload.get("base_cost", 0.0)),
            evolution_modifiers=dict(payload.get("evolution_modifiers", {})),
            monarch_modifiers=dict(payload.get("monarch_modifiers", {})),
            visual_effect=str(payload.get("visual_effect", "none")),
        )

    def execute(self, stats: dict[str, float], current_form: str, monarch_mode: bool) -> dict[str, Any]:
        return {
            "chip": self.chip_id,
            "category": self.category,
            "form": current_form,
            "monarch_mode": monarch_mode,
            "stats": stats,
            "visual_effect": self.visual_effect,
        }

    def to_public_dict(self, locked: bool = False) -> dict[str, Any]:
        return {
            "id": self.chip_id,
            "category": self.category,
            "min_form": self.min_form,
            "visual_effect": self.visual_effect,
            "stats": {
                "base_damage": self.base_damage,
                "base_speed": self.base_speed,
                "base_cost": self.base_cost,
            },
            "evolution_modifiers": self.evolution_modifiers,
            "monarch_modifiers": self.monarch_modifiers,
            "locked": locked,
        }
