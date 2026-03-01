from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class ShadowKnight(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="ShadowKnight",
            name="Shadow Knight",
            tier="monarch",
            form_required="AvatarMonarch",
            stats={"attack": 165, "defense": 135, "speed": 96},
            aura="shadow-cosmic",
            visual_profile={"theme": "abyssal rend"},
        )
