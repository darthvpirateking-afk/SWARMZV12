from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class FractalDragon(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="FractalDragon",
            name="Fractal Dragon",
            tier="sigil",
            form_required="AvatarOmegaPlus",
            stats={"attack": 150, "defense": 88, "speed": 95},
            aura="glyph-based",
            visual_profile={"theme": "fractal breath"},
        )
