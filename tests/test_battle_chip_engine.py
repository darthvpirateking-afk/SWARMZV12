from __future__ import annotations

import json
from pathlib import Path

from swarmz_runtime.avatar.abilities.battle_chip_engine import (
    BattleChipEngine,
    ChipWitnessLogger,
)


class _AvatarStub:
    def __init__(self, form: str) -> None:
        self.current_form = form


def test_chip_is_blocked_when_min_form_not_met(tmp_path: Path) -> None:
    avatar = _AvatarStub("AvatarOmega")
    engine = BattleChipEngine(avatar, witness=ChipWitnessLogger(tmp_path / "chips.jsonl"))

    result = engine.execute_chip("Dimensional Tear")
    assert result["ok"] is True
    assert result["executed"] is False
    assert result["reason"] == "form_locked"


def test_chip_executes_and_writes_witness_event(tmp_path: Path) -> None:
    log_path = tmp_path / "chips.jsonl"
    avatar = _AvatarStub("AvatarSovereign")
    engine = BattleChipEngine(avatar, witness=ChipWitnessLogger(log_path))

    result = engine.execute_chip("Dimensional Tear")
    assert result["ok"] is True
    assert result["executed"] is True
    assert result["chip"] == "Dimensional Tear"
    assert "stats" in result
    assert log_path.exists() is True

    payload = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert payload["type"] == "chip_execution"
    assert payload["chip"] == "Dimensional Tear"
    assert "timestamp" in payload


def test_monarch_mode_applies_extra_modifiers(tmp_path: Path) -> None:
    sovereign_avatar = _AvatarStub("AvatarSovereign")
    monarch_avatar = _AvatarStub("AvatarMonarch")
    sovereign_engine = BattleChipEngine(
        sovereign_avatar,
        witness=ChipWitnessLogger(tmp_path / "sovereign.jsonl"),
    )
    monarch_engine = BattleChipEngine(
        monarch_avatar,
        witness=ChipWitnessLogger(tmp_path / "monarch.jsonl"),
    )

    sovereign = sovereign_engine.execute_chip("Solar Judgement")
    monarch = monarch_engine.execute_chip("Solar Judgement")
    assert sovereign["executed"] is True
    assert monarch["executed"] is True
    assert monarch["stats"]["damage"] > sovereign["stats"]["damage"]
    assert monarch["stats"]["speed"] > sovereign["stats"]["speed"]
    assert "special_variants" in monarch


def test_burst_and_chain_paths(tmp_path: Path) -> None:
    avatar = _AvatarStub("AvatarSovereign")
    engine = BattleChipEngine(avatar, witness=ChipWitnessLogger(tmp_path / "burst_chain.jsonl"))

    burst = engine.burst()
    assert burst["ok"] is True
    assert burst["executed"] is True
    assert burst["chip_result"]["executed"] is True

    chain = engine.chain()
    assert chain["ok"] is True
    assert chain["executed"] is True
    assert 1 <= chain["count"] <= 3
    assert all(item["executed"] for item in chain["sequence"])


def test_chip_state_reports_available_and_locked(tmp_path: Path) -> None:
    avatar = _AvatarStub("AvatarOmega")
    engine = BattleChipEngine(avatar, witness=ChipWitnessLogger(tmp_path / "state.jsonl"))

    state = engine.get_state()
    assert isinstance(state["available"], list)
    assert isinstance(state["locked"], list)
    assert isinstance(state["categories"], dict)
    assert len(state["available"]) > 0
    assert len(state["locked"]) > 0
