import json
import sqlite3

import swarm_runner
from jsonl_utils import write_jsonl


def _configure_runner_paths(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    packs_dir = tmp_path / "packs"
    monkeypatch.setattr(swarm_runner, "DATA_DIR", data_dir)
    monkeypatch.setattr(swarm_runner, "MISSIONS_FILE", data_dir / "missions.jsonl")
    monkeypatch.setattr(swarm_runner, "AUDIT_FILE", data_dir / "audit.jsonl")
    monkeypatch.setattr(swarm_runner, "HEARTBEAT_FILE", data_dir / "runner_heartbeat.json")
    monkeypatch.setattr(swarm_runner, "PACKS_DIR", packs_dir)
    monkeypatch.setattr(swarm_runner, "RUNNER_STATE_DB", data_dir / "runner_state.db")
    return data_dir


def test_compute_backoff_bounds():
    assert swarm_runner._compute_backoff(0) == swarm_runner.TICK_INTERVAL
    assert swarm_runner._compute_backoff(1) == 2
    assert swarm_runner._compute_backoff(2) == 4
    assert swarm_runner._compute_backoff(999) == swarm_runner.MAX_BACKOFF_SECONDS


def test_run_loop_persists_heartbeat_and_state(monkeypatch, tmp_path):
    data_dir = _configure_runner_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(swarm_runner, "_process_one", lambda: False)
    monkeypatch.setattr(swarm_runner.time, "sleep", lambda _seconds: None)

    swarm_runner.run_loop(max_ticks=1)

    heartbeat = json.loads((data_dir / "runner_heartbeat.json").read_text(encoding="utf-8"))
    assert heartbeat["status"] == "up"
    assert heartbeat["consecutive_errors"] == 0
    assert heartbeat["total_ticks"] == 1

    with sqlite3.connect(data_dir / "runner_state.db") as conn:
        row = conn.execute(
            "SELECT total_ticks, consecutive_errors, last_status FROM runner_state WHERE id = 1"
        ).fetchone()
    assert row == (1, 0, "up")


def test_run_loop_uses_backoff_after_error(monkeypatch, tmp_path):
    data_dir = _configure_runner_paths(monkeypatch, tmp_path)

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(swarm_runner, "_process_one", _boom)
    monkeypatch.setattr(swarm_runner.time, "sleep", lambda _seconds: None)

    swarm_runner.run_loop(max_ticks=1)

    heartbeat = json.loads((data_dir / "runner_heartbeat.json").read_text(encoding="utf-8"))
    assert heartbeat["status"] == "degraded"
    assert heartbeat["consecutive_errors"] == 1
    assert heartbeat["backoff_seconds"] > swarm_runner.TICK_INTERVAL
    assert "boom" in heartbeat["last_error"]

    audit_text = (data_dir / "audit.jsonl").read_text(encoding="utf-8")
    assert "runner_loop_error" in audit_text


def test_process_one_space_mission_writes_moon_artifact(monkeypatch, tmp_path):
    data_dir = _configure_runner_paths(monkeypatch, tmp_path)
    (data_dir / "missions.jsonl").parent.mkdir(parents=True, exist_ok=True)
    mission = {
        "mission_id": "mission-space-int-1",
        "intent": "swarmz-minion-space-sim",
        "status": "PENDING",
        "spec": {
            "date_utc": "2026-03-01",
            "lat_deg": -37.8136,
            "lon_deg": 144.9631,
            "elevation_m": 30,
            "timezone": "Australia/Melbourne",
        },
    }
    write_jsonl(data_dir / "missions.jsonl", mission)

    monkeypatch.setattr(swarm_runner, "_astropy_available", lambda: False)
    monkeypatch.setattr(
        swarm_runner,
        "_ingest_space_result",
        lambda **kwargs: (8.0, "artifact-int-1"),
    )

    processed = swarm_runner._process_one()
    assert processed is True

    missions, _, _ = swarm_runner.read_jsonl(data_dir / "missions.jsonl")
    assert missions[0]["status"] == "SUCCESS"
    result_path = swarm_runner.PACKS_DIR / "mission-space-int-1" / "result.json"
    artifact_path = swarm_runner.PACKS_DIR / "mission-space-int-1" / "moon_transit.json"
    assert result_path.exists()
    assert artifact_path.exists()

    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert result_payload["ok"] is True
    assert result_payload["type"] == "space_moon_transit"
