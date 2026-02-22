from dataclasses import dataclass
from enum import Enum
from typing import Any


class Realm(str, Enum):
    MATRIX = "MATRIX"
    AETHER = "AETHER"
    FORGE = "FORGE"
    PRISM = "PRISM"
    ABYSS = "ABYSS"
    COSMOS = "COSMOS"


class Form(str, Enum):
    NODE = "NODE"
    SPARK = "SPARK"
    FLOW = "FLOW"
    SHARD = "SHARD"
    CORE = "CORE"
    ASCENDANT = "ASCENDANT"


class MissionRank(str, Enum):
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"


class SwarmTier(str, Enum):
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"


@dataclass(frozen=True)
class PersonaContext:
    realm: Realm
    form: Form
    mission_rank: MissionRank
    swarm_tier: SwarmTier


@dataclass(frozen=True)
class PersonaStyle:
    tone: str
    metaphor_level: str
    density: str
    formality: str
    pacing: str
    intensity: str


class PersonaLayer:
    def __init__(self, realm_matrix: Any, form_map: Any, swarm_model: Any):
        self.realm_matrix = realm_matrix
        self.form_map = form_map
        self.swarm_model = swarm_model

    def derive_style(self, ctx: PersonaContext) -> PersonaStyle:
        realm_style = self.realm_matrix.get_style(ctx.realm)
        form_style = self.form_map.get_style(ctx.form)
        swarm_style = self.swarm_model.get_style(ctx.swarm_tier)

        return PersonaStyle(
            tone=realm_style["tone"],
            metaphor_level=realm_style["metaphor_level"],
            density=form_style["density"],
            formality=form_style["formality"],
            pacing=swarm_style["pacing"],
            intensity=swarm_style["intensity"],
        )
