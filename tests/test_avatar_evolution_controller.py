from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from swarmz_runtime.avatar.evolution_controller import (
    EvolutionController,
    WitnessLogger,
)


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


def test_evolve_cannot_skip_forms() -> None:
    rank_system = _StubRankSystem("Sovereign")
    witness = _StubWitness()
    controller = EvolutionController(object(), rank_system, witness)

    assert controller.current_form == "AvatarOmega"
    assert controller.evolve() is True
    assert controller.current_form == "AvatarInfinity"


def test_unlock_sovereign_blocked_before_required_rank() -> None:
    rank_system = _StubRankSystem("A")
    witness = _StubWitness()
    controller = EvolutionController(object(), rank_system, witness)

    assert controller.unlock_sovereign() is False
    assert controller.current_form == "AvatarOmega"


def test_monarch_mode_blocked_until_sovereign() -> None:
    rank_system = _StubRankSystem("Sovereign")
    witness = _StubWitness()
    controller = EvolutionController(object(), rank_system, witness)

    assert controller.can_enter_monarch_mode() is False
    assert controller.operator_trigger("MONARCH") is False
    assert controller.current_form == "AvatarOmega"


def test_operator_trigger_sequence() -> None:
    rank_system = _StubRankSystem("Sovereign")
    witness = _StubWitness()
    controller = EvolutionController(object(), rank_system, witness)

    assert controller.operator_trigger("ASCEND") is True
    assert controller.current_form == "AvatarInfinity"
    assert controller.operator_trigger("SOVEREIGN") is True
    assert controller.current_form == "AvatarSovereign"
    assert controller.operator_trigger("MONARCH") is True
    assert controller.current_form == "AvatarMonarch"


def test_evolution_events_are_written_to_witness_log(tmp_path: Path) -> None:
    rank_system = _StubRankSystem("Sovereign")
    witness_path = tmp_path / "avatar_evolution.jsonl"
    witness = WitnessLogger(path=witness_path)
    controller = EvolutionController(object(), rank_system, witness)

    assert controller.evolve() is True
    lines = witness_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "expected witness log event"
    payload = json.loads(lines[-1])
    assert payload["type"] == "avatar_evolution"
    assert payload["new_form"] == "AvatarInfinity"
    assert "timestamp" in payload


def test_cockpit_status_exposes_evolution_state() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        response = client.get("/cockpit/status")
        assert response.status_code == 200
        payload = response.json()
        assert "evolution" in payload
        evo = payload["evolution"]
        assert "current_form" in evo
        assert "next_form" in evo
        assert "rank" in evo
        assert "can_evolve" in evo
        assert "sovereign_unlocked" in evo


def test_cockpit_avatar_mode_file_served() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        response = client.get("/cockpit/modes/avatar.tsx")
        assert response.status_code == 200


def test_avatar_trigger_endpoint_smoke() -> None:
    from swarmz_server import app

    with TestClient(app) as client:
        valid = client.post("/v1/avatar/matrix/trigger", json={"command": "MONARCH"})
        assert valid.status_code == 200
        body = valid.json()
        assert body["ok"] is True
        assert body["command"] == "MONARCH"
        assert "transitioned" in body
        assert "current_form" in body

        invalid = client.post("/v1/avatar/matrix/trigger", json={"command": "INVALID"})
        assert invalid.status_code == 400
