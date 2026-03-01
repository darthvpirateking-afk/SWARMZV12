from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class PrismGolem(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="PrismGolem",
            name="Prism Golem",
            tier="relic",
            form_required="AvatarSovereign",
            stats={"attack": 145, "defense": 118, "speed": 78},
            aura="artifact-based",
            visual_profile={"theme": "prism burst"},
        )
