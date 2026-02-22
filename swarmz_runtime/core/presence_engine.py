from dataclasses import dataclass

from .persona_layer import PersonaContext, PersonaLayer, PersonaStyle
from .throne_governance import ThroneGovernance


@dataclass
class PresenceConfig:
    max_length: int = 1200
    min_length: int = 50
    allow_metaphor: bool = True
    allow_ceremonial: bool = True


class PresenceEngine:
    """
    PresenceEngine
    --------------
    - Converts PersonaStyle into concrete output constraints.
    - No autonomy, no self-starting, no emotions.
    """

    def __init__(
        self,
        persona_layer: PersonaLayer,
        throne: ThroneGovernance,
        config: PresenceConfig | None = None,
    ):
        self.persona_layer = persona_layer
        self.throne = throne
        self.config = config or PresenceConfig()

    def render_style(self, ctx: PersonaContext) -> PersonaStyle:
        self.throne.assert_operator_control()
        return self.persona_layer.derive_style(ctx)

    def apply_constraints(self, text: str, style: PersonaStyle) -> str:
        self.throne.assert_operator_control()

        # Length shaping
        if style.density == "high":
            max_len = self.config.max_length
        elif style.density == "medium":
            max_len = int(self.config.max_length * 0.7)
        else:
            max_len = int(self.config.max_length * 0.5)

        text = text.strip()
        if len(text) > max_len:
            text = text[:max_len].rsplit(" ", 1)[0] + "…"

        # Formality / tone hints (non-emotional, purely stylistic)
        # This is where you'd plug in templates or post-processing rules.
        return text
