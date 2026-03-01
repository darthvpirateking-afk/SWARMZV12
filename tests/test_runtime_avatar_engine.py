from __future__ import annotations

import pytest

from swarmz_runtime.avatar.avatar_brain import AvatarBrain
from swarmz_runtime.avatar.avatar_presence import AvatarPresence
from swarmz_runtime.avatar.avatar_state import AvatarState


def test_engine_uses_runtime_avatar_primitives() -> None:
    pytest.importorskip("yaml")
    from swarmz.backend.runtime.engine import Engine

    engine = Engine()
    engine.initialize_components()
    assert isinstance(engine.avatar["brain"], AvatarBrain)
    assert isinstance(engine.avatar["state"], AvatarState)
    assert isinstance(engine.avatar["presence"], AvatarPresence)


def test_avatar_state_update_and_get() -> None:
    state = AvatarState()
    state.update_state("avatar_form", "AvatarOmega")
    assert state.get_state()["avatar_form"] == "AvatarOmega"
