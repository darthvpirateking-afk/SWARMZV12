from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class ChronoKnight(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="ChronoKnight",
            name="Chrono Knight",
            tier="relic",
            form_required="AvatarSovereign",
            stats={"attack": 140, "defense": 105, "speed": 92},
            aura="artifact-based",
            visual_profile={"theme": "time-slow"},
        )
