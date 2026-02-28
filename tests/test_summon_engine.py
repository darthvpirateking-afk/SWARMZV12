from __future__ import annotations

import json
from pathlib import Path

from swarmz_runtime.avatar.avatar_matrix import AvatarMatrix
from swarmz_runtime.avatar.summons.summon_engine import SummonEngine, SummonWitnessLogger


def _force_form(matrix: AvatarMatrix, form: str) -> None:
    matrix.evolution.current_form = form
    matrix.current_form = form


def test_summon_gating_by_form() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    engine = SummonEngine(matrix)

    _force_form(matrix, "AvatarOmega")
    pantheon_blocked = engine.spawn("SolarWarden")
    assert pantheon_blocked["executed"] is False

    digital_allowed = engine.spawn("FirewallSerpent")
    assert digital_allowed["executed"] is True

    _force_form(matrix, "AvatarInfinity")
    pantheon_allowed = engine.spawn("SolarWarden")
    assert pantheon_allowed["executed"] is True


def test_monarch_legion_requires_monarch_form() -> None:
    matrix = AvatarMatrix("TEST_OPERATOR")
    engine = SummonEngine(matrix)

    _force_form(matrix, "AvatarSovereign")
    blocked = engine.legion()
    assert blocked["executed"] is False

    _force_form(matrix, "AvatarMonarch")
    allowed = engine.legion()
    assert allowed["executed"] is True


def test_summon_witness_logging(tmp_path: Path) -> None:
    witness_path = tmp_path / "summons.jsonl"
    matrix = AvatarMatrix("TEST_OPERATOR")
    _force_form(matrix, "AvatarMonarch")
    engine = SummonEngine(matrix, witness=SummonWitnessLogger(witness_path))

    spawn = engine.spawn("ShadowKnight")
    assert spawn["executed"] is True
    dismiss = engine.dismiss("ShadowKnight")
    assert dismiss["executed"] is True

    lines = witness_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
    payload = json.loads(lines[-1])
    assert payload["type"] == "summon_event"
    assert payload["event"] == "dismiss"
