from swarmz_runtime.core.form_evolution_map import FormEvolutionMap
from swarmz_runtime.core.persona_layer import (
    Form,
    MissionRank,
    PersonaContext,
    PersonaLayer,
    PersonaStyle,
    Realm,
    SwarmTier,
)
from swarmz_runtime.core.presence_engine import PresenceConfig, PresenceEngine
from swarmz_runtime.core.realm_tone_matrix import RealmToneMatrix
from swarmz_runtime.core.swarm_behavior_model import SwarmBehaviorModel
from swarmz_runtime.core.throne_governance import ThroneGovernance


def _build_layer() -> PersonaLayer:
    return PersonaLayer(RealmToneMatrix(), FormEvolutionMap(), SwarmBehaviorModel())


def _build_context() -> PersonaContext:
    return PersonaContext(
        realm=Realm.COSMOS,
        form=Form.CORE,
        mission_rank=MissionRank.S,
        swarm_tier=SwarmTier.T3,
    )


def test_persona_layer_derive_style():
    layer = _build_layer()
    style = layer.derive_style(_build_context())

    assert isinstance(style, PersonaStyle)
    assert style.tone == "grand-ceremonial"
    assert style.density == "high"
    assert style.pacing == "fast"


def test_realm_tone_all_realms():
    matrix = RealmToneMatrix()
    for realm in Realm:
        style = matrix.get_style(realm)
        assert "tone" in style
        assert "metaphor_level" in style


def test_form_evolution_all_forms():
    evolution = FormEvolutionMap()
    for form in Form:
        style = evolution.get_style(form)
        assert "density" in style
        assert "formality" in style


def test_swarm_behavior_all_tiers():
    model = SwarmBehaviorModel()
    for tier in SwarmTier:
        style = model.get_style(tier)
        assert "pacing" in style
        assert "intensity" in style


def test_presence_engine_render_style():
    throne = ThroneGovernance(operator_id="regan")
    engine = PresenceEngine(_build_layer(), throne, PresenceConfig())

    style = engine.render_style(_build_context())

    assert style.tone == "grand-ceremonial"
    assert style.formality == "high"
    assert style.intensity == "medium-high"


def test_presence_engine_apply_constraints_truncates():
    throne = ThroneGovernance(operator_id="regan")
    engine = PresenceEngine(_build_layer(), throne, PresenceConfig(max_length=120))
    style = engine.render_style(_build_context())

    text = " ".join(["signal"] * 100)
    constrained = engine.apply_constraints(text, style)

    assert len(constrained) <= 120
    assert constrained.endswith("…")


def test_throne_governance_constraints():
    throne = ThroneGovernance(operator_id="regan")
    constraints = throne.describe_constraints()

    assert constraints["autonomy"] == "disabled"
    assert constraints["self_modification"] == "disabled"
    assert constraints["emotional_simulation"] == "disabled"
    assert constraints["operator_approval_required"] is True
