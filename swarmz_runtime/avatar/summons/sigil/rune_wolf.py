from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class RuneWolf(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="RuneWolf",
            name="Rune Wolf",
            tier="sigil",
            form_required="AvatarOmegaPlus",
            stats={"attack": 125, "defense": 82, "speed": 112},
            aura="glyph-based",
            visual_profile={"theme": "sigil strikes"},
        )
