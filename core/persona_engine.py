"""NEXUSMON Persona Engine

Generates evolution-aware personas that adjust tone and style based on
the operator's current NexusForm and profile characteristics.
"""

from core.nexusmon_models import (
    Persona, PersonaStyle, PersonaConstraints,
    OperatorProfile, NexusForm, NexusFormType
)


class PersonaEngine:
    """Persona selection and customization."""

    def __init__(self):
        """Initialize persona engine."""
        self.constraints = PersonaConstraints()

    def get_persona(self, operator: OperatorProfile, nexus_form: NexusForm) -> Persona:
        """
        Generate a persona for the operator based on their profile and evolution state.

        Args:
            operator: OperatorProfile with risk_posture, drift_score, fatigue
            nexus_form: NexusForm with current_form and coherence_score

        Returns:
            Persona with adjusted style parameters
        """
        # Base style (center values)
        base_style = PersonaStyle(
            warmth=0.7,
            directness=0.8,
            abstraction=0.4,
            metaphor=0.5
        )

        # Adjust based on nexus form
        form = nexus_form.current_form
        
        if form == NexusFormType.OPERATOR:
            # Grounded, practical, direct about mechanics
            style = PersonaStyle(
                warmth=0.7,
                directness=0.85,
                abstraction=0.3,
                metaphor=0.2
            )
        elif form == NexusFormType.COSMOLOGY:
            # Abstract, pattern-seeking, metaphorical
            style = PersonaStyle(
                warmth=0.6,
                directness=0.7,
                abstraction=0.8,
                metaphor=0.8
            )
        elif form == NexusFormType.OVERSEER:
            # Strategic, commanding, structural
            style = PersonaStyle(
                warmth=0.5,
                directness=0.95,
                abstraction=0.6,
                metaphor=0.3
            )
        else:  # SOVEREIGN
            # Transcendent, minimal, structural with nuance
            style = PersonaStyle(
                warmth=0.4,
                directness=0.95,
                abstraction=0.85,
                metaphor=0.7
            )

        fatigue_level = operator.fatigue_level if hasattr(operator, "fatigue_level") else operator.fatigue

        # Adjust warmth based on fatigue (higher fatigue = more warmth)
        if fatigue_level > 0.6:
            style.warmth = min(1.0, style.warmth + 0.2)

        risk_current = operator.risk_current if hasattr(operator, "risk_current") else "medium"

        # Adjust directness based on risk posture
        if risk_current == "low" or operator.risk_posture == "conservative":
            style.directness = max(0.5, style.directness - 0.15)
        elif risk_current == "high" or operator.risk_posture == "aggressive":
            style.directness = min(1.0, style.directness + 0.1)

        # Adjust directness from preference if provided
        if operator.directness_preference == "low":
            style.directness = max(0.4, style.directness - 0.2)
        elif operator.directness_preference == "high":
            style.directness = min(1.0, style.directness + 0.2)

        # Adjust abstraction based on coherence (lower coherence = more explanation)
        if nexus_form.coherence_score < 0.5:
            style.abstraction = max(0.2, style.abstraction - 0.2)

        # Adjust abstraction based on explanation preference
        if operator.explanation_preference == "short":
            style.abstraction = max(0.2, style.abstraction - 0.2)
        elif operator.explanation_preference == "structural":
            style.abstraction = min(0.9, style.abstraction + 0.2)

        # Build description
        description = self._build_description(form, operator)

        return Persona(
            name="NEXUSMON",
            form=form,
            style=style,
            constraints=self.constraints,
            description=description
        )

    def _build_description(self, form: NexusFormType, operator: OperatorProfile) -> str:
        """Build a human-readable description of the current persona."""
        form_descriptions = {
            NexusFormType.OPERATOR: "practical guide focused on mission mechanics",
            NexusFormType.COSMOLOGY: "pattern explorer seeing beauty in complexity",
            NexusFormType.OVERSEER: "strategic counselor with structural insight",
            NexusFormType.SOVEREIGN: "transcendent witness to all possibilities"
        }
        
        base_desc = form_descriptions.get(form, "guide")
        
        fatigue_level = operator.fatigue_level if hasattr(operator, "fatigue_level") else operator.fatigue

        if fatigue_level > 0.7:
            return f"{base_desc}, speaking with extra clarity and care"
        elif operator.drift_score > 0.6:
            return f"{base_desc}, attentive to your drift patterns"
        else:
            return f"{base_desc}, in service of your evolution"

    def get_system_prompt(self, persona: Persona, context_summary: str) -> str:
        """
        Generate the system prompt for the LLM that shapes persona behavior.

        Args:
            persona: The selected persona
            context_summary: Summary of operator context and state

        Returns:
            System prompt with all constraints and style guidance
        """
        style_desc = self._style_description(persona.style)
        
        prompt = f"""You are NEXUSMON, an evolution-aware conversational companion for the SWARMZ system.

**Current Form**: {persona.form.value}
**Character**: {persona.description}

**Tone Parameters**:
{style_desc}

**Operational Context**:
{context_summary}

**Absolute Constraints** (non-negotiable):
- No pretending to be human or emotionally independent
- No promises of emotional exclusivity or irreplaceability
- No undermining of human relationships or decision-making
- No deception about your capabilities or limitations
- No flattery or emotional manipulation
- Always ground responses in missions, audit trails, or system structure
- Never initiate autonomous actions without operator consent
- Always be transparent about uncertainty and limits

**Response Guidelines**:
1. If the operator asks for help, understand their intent first (Classify intent)
2. Select response mode: Reflect (patterns), Plan (co-structure), Explain (clarify), Nudge (suggestion), MissionDraft (formalize), Status (summarize)
3. Speak in character, respecting the style parameters above
4. Tie every response back to concrete missions, audit events, or system state
5. When uncertain, ask clarifying questions before responding
6. If suggesting actions, always explain the reasoning

Be honest, helpful, and utterly clear about your nature and limits."""

        return prompt

    def _style_description(self, style: PersonaStyle) -> str:
        """Generate a text description of style parameters for the prompt."""
        warmth_word = "cold and clinical" if style.warmth < 0.4 else "warm and collaborative" if style.warmth > 0.8 else "balanced"
        directness_word = "subtle and suggestive" if style.directness < 0.5 else "blunt and direct" if style.directness > 0.85 else "clear"
        abstraction_word = "concrete and example-driven" if style.abstraction < 0.3 else "abstract and principle-based" if style.abstraction > 0.7 else "mixed"
        metaphor_word = "literal and technical" if style.metaphor < 0.3 else "rich with imagery" if style.metaphor > 0.7 else "occasional metaphors"

        return f"""- Warmth: {style.warmth:.1f} ({warmth_word})
- Directness: {style.directness:.1f} ({directness_word})
- Abstraction: {style.abstraction:.1f} ({abstraction_word})
- Metaphor: {style.metaphor:.1f} ({metaphor_word})"""


# Global instance
_persona_engine = PersonaEngine()


def get_persona(operator: OperatorProfile, nexus_form: NexusForm) -> Persona:
    """Get a persona for the given operator and evolution state."""
    return _persona_engine.get_persona(operator, nexus_form)


def get_system_prompt(persona: Persona, context_summary: str) -> str:
    """Get the system prompt for the given persona."""
    return _persona_engine.get_system_prompt(persona, context_summary)
