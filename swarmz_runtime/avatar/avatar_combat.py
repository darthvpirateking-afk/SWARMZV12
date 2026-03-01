from __future__ import annotations

from typing import Any


def resolve_combat_profile(current_form: str) -> dict[str, Any]:
    profile = {
        "damage_multiplier": 1.0,
        "speed_multiplier": 1.0,
        "defense_multiplier": 1.0,
        "abilities": [],
    }

    if current_form == "AvatarMonarch":
        profile["damage_multiplier"] = 1.35
        profile["speed_multiplier"] = 1.20
        profile["defense_multiplier"] = 1.15
        profile["abilities"] = ["Abyssal Rend", "Cosmic Rift"]

    return profile
