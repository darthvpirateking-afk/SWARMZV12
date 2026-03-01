from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class StormHerald(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="StormHerald",
            name="Storm Herald",
            tier="pantheon",
            form_required="AvatarInfinity",
            stats={"attack": 115, "defense": 85, "speed": 100},
            aura="radiant",
            visual_profile={"theme": "storm-based"},
        )
