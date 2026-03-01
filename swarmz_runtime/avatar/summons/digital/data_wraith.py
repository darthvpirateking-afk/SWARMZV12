from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class DataWraith(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="DataWraith",
            name="Data Wraith",
            tier="digital",
            form_required="AvatarOmega",
            stats={"attack": 100, "defense": 78, "speed": 120},
            aura="neon-cyber",
            visual_profile={"theme": "packet burst"},
        )
