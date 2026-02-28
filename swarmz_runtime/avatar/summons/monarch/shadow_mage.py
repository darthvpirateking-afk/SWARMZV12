from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class ShadowMage(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="ShadowMage",
            name="Shadow Mage",
            tier="monarch",
            form_required="AvatarMonarch",
            stats={"attack": 172, "defense": 90, "speed": 102},
            aura="shadow-cosmic",
            visual_profile={"theme": "dark spells"},
        )
