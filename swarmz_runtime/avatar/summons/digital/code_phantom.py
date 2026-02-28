from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class CodePhantom(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="CodePhantom",
            name="Code Phantom",
            tier="digital",
            form_required="AvatarOmega",
            stats={"attack": 108, "defense": 82, "speed": 108},
            aura="neon-cyber",
            visual_profile={"theme": "data slash"},
        )
