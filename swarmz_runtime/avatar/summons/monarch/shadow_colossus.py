from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class ShadowColossus(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="ShadowColossus",
            name="Shadow Colossus",
            tier="monarch",
            form_required="AvatarMonarch",
            stats={"attack": 185, "defense": 145, "speed": 72},
            aura="shadow-cosmic",
            visual_profile={"theme": "cosmic stomp"},
        )
