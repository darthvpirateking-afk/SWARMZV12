from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class AegisSentinel(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="AegisSentinel",
            name="Aegis Sentinel",
            tier="relic",
            form_required="AvatarSovereign",
            stats={"attack": 135, "defense": 130, "speed": 70},
            aura="artifact-based",
            visual_profile={"theme": "shield wall"},
        )
