from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class AetherGuardian(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="AetherGuardian",
            name="Aether Guardian",
            tier="pantheon",
            form_required="AvatarInfinity",
            stats={"attack": 130, "defense": 90, "speed": 88},
            aura="radiant",
            visual_profile={"theme": "cosmic-based"},
        )
