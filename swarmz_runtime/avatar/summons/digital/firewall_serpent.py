from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class FirewallSerpent(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="FirewallSerpent",
            name="Firewall Serpent",
            tier="digital",
            form_required="AvatarOmega",
            stats={"attack": 95, "defense": 85, "speed": 115},
            aura="neon-cyber",
            visual_profile={"theme": "firewall shield"},
        )
