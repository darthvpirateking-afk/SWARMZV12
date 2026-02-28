from __future__ import annotations

from swarmz_runtime.avatar.summons.summon_base import SummonBase


class PacketSwarm(SummonBase):
    def __init__(self) -> None:
        super().__init__(
            id="PacketSwarm",
            name="Packet Swarm",
            tier="digital",
            form_required="AvatarOmega",
            stats={"attack": 90, "defense": 70, "speed": 130},
            aura="neon-cyber",
            visual_profile={"theme": "swarm packet burst"},
        )
