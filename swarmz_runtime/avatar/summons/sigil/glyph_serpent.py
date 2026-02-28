from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class GlyphSerpent(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="GlyphSerpent",
            name="Glyph Serpent",
            tier="sigil",
            form_required="AvatarOmegaPlus",
            stats={"attack": 140, "defense": 75, "speed": 105},
            aura="glyph-based",
            visual_profile={"theme": "rune attacks"},
        )
