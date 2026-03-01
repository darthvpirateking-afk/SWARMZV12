from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class SolarWarden(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="SolarWarden",
            name="Solar Warden",
            tier="pantheon",
            form_required="AvatarInfinity",
            stats={"attack": 120, "defense": 95, "speed": 80},
            aura="radiant",
            visual_profile={"theme": "light-based"},
        )
