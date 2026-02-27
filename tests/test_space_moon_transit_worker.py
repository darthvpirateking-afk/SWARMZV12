import json
from datetime import datetime, timezone

import swarm_runner


def _configure_runner_paths(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    packs_dir = tmp_path / "packs"
    data_dir.mkdir(parents=True, exist_ok=True)
    packs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(swarm_runner, "DATA_DIR", data_dir)
    monkeypatch.setattr(swarm_runner, "MISSIONS_FILE", data_dir / "missions.jsonl")
    monkeypatch.setattr(swarm_runner, "AUDIT_FILE", data_dir / "audit.jsonl")
    monkeypatch.setattr(swarm_runner, "HEARTBEAT_FILE", data_dir / "runner_heartbeat.json")
    monkeypatch.setattr(swarm_runner, "PACKS_DIR", packs_dir)
    monkeypatch.setattr(swarm_runner, "RUNNER_STATE_DB", data_dir / "runner_state.db")
    return data_dir, packs_dir


def test_space_worker_valid_fallback_writes_artifact(monkeypatch, tmp_path):
    _, packs_dir = _configure_runner_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(swarm_runner, "_astropy_available", lambda: False)
    monkeypatch.setattr(
        swarm_runner,
        "_ingest_space_result",
        lambda **kwargs: (8.0, "artifact-1"),
    )

    mission = {
        "mission_id": "mission-space-1",
        "intent": "swarmz-minion-space-sim",
        "spec": {
            "date_utc": "2026-03-01",
            "lat_deg": -37.8136,
            "lon_deg": 144.9631,
            "elevation_m": 30,
            "timezone": "Australia/Melbourne",
        },
    }
    result = swarm_runner._worker_space_moon_transit(mission)

    assert result["ok"] is True
    assert result["type"] == "space_moon_transit"
    assert result["method"] == "fallback"
    assert result["artifact_id"] == "artifact-1"
    artifact_path = packs_dir / "mission-space-1" / "moon_transit.json"
    assert artifact_path.exists()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["sim_type"] == "moon_meridian_transit"
    assert payload["method"] == "fallback"


def test_space_worker_invalid_spec_returns_error(monkeypatch, tmp_path):
    _configure_runner_paths(monkeypatch, tmp_path)
    mission = {
        "mission_id": "mission-space-2",
        "intent": "swarmz-minion-space-sim",
        "spec": {"date_utc": "bad-date"},
    }
    result = swarm_runner._worker_space_moon_transit(mission)

    assert result["ok"] is False
    assert result["type"] == "space_moon_transit"
    assert "date_utc" in result["error"]


def test_space_worker_astropy_branch_mocked(monkeypatch, tmp_path):
    _, packs_dir = _configure_runner_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(swarm_runner, "_astropy_available", lambda: True)

    mocked_transit = {
        "method": "astropy",
        "transit_utc": "2026-03-02T03:00:00Z",
        "transit_local": "2026-03-02T14:00:00+11:00",
        "altitude_deg_at_transit": 66.2,
        "quality_score": 0.98,
        "notes": "mocked astropy result",
    }
    monkeypatch.setattr(swarm_runner, "_compute_moon_transit_astropy", lambda _spec: mocked_transit)
    monkeypatch.setattr(
        swarm_runner,
        "_ingest_space_result",
        lambda **kwargs: (18.0, "artifact-astropy"),
    )

    mission = {
        "mission_id": "mission-space-3",
        "intent": "swarmz-minion-space-sim",
        "spec": {},
    }
    result = swarm_runner._worker_space_moon_transit(mission)

    assert result["ok"] is True
    assert result["method"] == "astropy"
    assert result["quality_score"] >= 0.9
    payload = json.loads(
        (packs_dir / "mission-space-3" / "moon_transit.json").read_text(encoding="utf-8")
    )
    assert payload["method"] == "astropy"
    assert payload["quality_score"] == 0.98


def test_space_worker_ingestion_hooks_called(monkeypatch, tmp_path):
    _configure_runner_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(swarm_runner, "_astropy_available", lambda: False)
    calls = {"count": 0, "mission_id": "", "method": ""}

    def _capture_ingest(**kwargs):
        calls["count"] += 1
        calls["mission_id"] = kwargs["mission_id"]
        calls["method"] = kwargs["method"]
        return 8.0, "artifact-ingest"

    monkeypatch.setattr(swarm_runner, "_ingest_space_result", _capture_ingest)
    mission = {"mission_id": "mission-space-4", "intent": "swarmz-minion-space-sim", "spec": {}}

    result = swarm_runner._worker_space_moon_transit(mission)

    assert result["ok"] is True
    assert calls["count"] == 1
    assert calls["mission_id"] == "mission-space-4"
    assert calls["method"] == "fallback"
    assert result["xp_awarded"] == 8.0
    assert result["artifact_id"] == "artifact-ingest"


def test_parse_space_spec_defaults():
    spec = swarm_runner._parse_space_spec({"spec": {}})
    assert spec["date_utc"] == datetime.now(timezone.utc).date().isoformat()
    assert spec["lat_deg"] == -37.8136
    assert spec["lon_deg"] == 144.9631
