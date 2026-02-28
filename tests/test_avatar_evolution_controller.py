from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from swarmz_runtime.avatar.evolution_controller import EvolutionController, WitnessLogger


class _StubRankSystem:
    _LADDER = ["E", "D", "C", "B", "A", "S", "Sovereign"]

    def __init__(self, current_rank: str) -> None:
        self.current_rank = current_rank

    def refresh_rank(self) -> str:
        return self.current_rank

    def rank_at_least(self, required_rank: str) -> bool:
        return self._LADDER.index(self.current_rank) >= self._LADDER.index(required_rank)


class _StubWitness:
    def __init__(self) -> None:
        self.events: list[dict[str, str]] = []

    def log_event(self, payload: dict) -> None:
        self.events.append(payload)


def test_rank_gate_blocks_early_evolution() -> None:
    controller = EvolutionController(object(), _StubRankSystem("E"), _StubWitness())
    assert controller.can_evolve_to("AvatarInfinity") is False
    assert controller.evolve() is False
    assert controller.current_form == "AvatarOmega"


def test_evolution_progresses_one_step_only() -> None:
    controller = EvolutionController(object(), _StubRankSystem("Sovereign"), _StubWitness())

    assert controller.current_form == "AvatarOmega"
    assert controller.evolve() is True
    assert controller.current_form == "AvatarInfinity"
    assert controller.evolve() is True
    assert controller.current_form == "AvatarOmegaPlus"
    assert controller.evolve() is True
    assert controller.current_form == "AvatarSovereign"
    assert controller.evolve() is False


def test_unlock_sovereign_requires_rank() -> None:
    blocked = EvolutionController(object(), _StubRankSystem("A"), _StubWitness())
    assert blocked.unlock_sovereign() is False
    assert blocked.current_form == "AvatarOmega"

    allowed = EvolutionController(object(), _StubRankSystem("Sovereign"), _StubWitness())
    assert allowed.unlock_sovereign() is True
    assert allowed.current_form == "AvatarSovereign"


def test_monarch_gate_and_return_flow() -> None:
    controller = EvolutionController(object(), _StubRankSystem("Sovereign"), _StubWitness())

    assert controller.operator_trigger("MONARCH") is False
    assert controller.operator_trigger("SOVEREIGN") is True
    assert controller.current_form == "AvatarSovereign"
    assert controller.operator_trigger("MONARCH") is True
    assert controller.current_form == "AvatarMonarch"
    assert controller.operator_trigger("RETURN") is True
    assert controller.current_form == "AvatarSovereign"


def test_evolution_events_are_written_to_witness_log(tmp_path: Path) -> None:
    witness_path = tmp_path / "avatar_evolution.jsonl"
    controller = EvolutionController(
        object(),
        _StubRankSystem("Sovereign"),
        WitnessLogger(path=witness_path),
    )

    assert controller.operator_trigger("SOVEREIGN") is True
    assert controller.operator_trigger("MONARCH") is True

    lines = witness_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 2
    payload = json.loads(lines[-1])
    assert payload["type"] == "avatar_evolution"
    assert payload["new_form"] == "AvatarMonarch"
    assert "timestamp" in payload


def test_cockpit_status_contains_evolution_block() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        response = client.get("/cockpit/status")
        assert response.status_code == 200
        data = response.json()
        evolution = data["evolution"]
        assert "current_form" in evolution
        assert "next_form" in evolution
        assert "rank" in evolution
        assert "can_evolve" in evolution
        assert "sovereign_unlocked" in evolution
        assert "monarch_available" in evolution


def test_avatar_trigger_endpoint_supports_return_and_chip_envelope() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        return_res = client.post("/v1/avatar/matrix/trigger", json={"command": "RETURN"})
        assert return_res.status_code == 200
        return_payload = return_res.json()
        assert return_payload["ok"] is True
        assert return_payload["command"] == "RETURN"
        assert "transitioned" in return_payload
        assert "current_form" in return_payload

        chip_res = client.post("/v1/avatar/matrix/trigger", json={"command": "CHIP Arcane Spiral"})
        assert chip_res.status_code == 200
        chip_payload = chip_res.json()
        assert chip_payload["ok"] is True
        assert chip_payload["command"].startswith("CHIP ")
        assert "executed" in chip_payload
        assert "chip_result" in chip_payload


def test_cockpit_avatar_mode_file_served() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        response = client.get("/cockpit/modes/avatar.tsx")
        assert response.status_code == 200
