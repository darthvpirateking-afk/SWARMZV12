from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class ShadowArcher(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="ShadowArcher",
            name="Shadow Archer",
            tier="monarch",
            form_required="AvatarMonarch",
            stats={"attack": 158, "defense": 100, "speed": 118},
            aura="shadow-cosmic",
            visual_profile={"theme": "void arrows"},
        )
