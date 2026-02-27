from pathlib import Path

from fastapi.testclient import TestClient

from swarmz_server import app


def _seed_corrupt_missions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n{not valid json}\n\n", encoding="utf-8")


def test_storage_resilience_legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    missions_file = tmp_path / "data" / "missions.jsonl"
    _seed_corrupt_missions(missions_file)

    with TestClient(app) as client:
        r1 = client.post(
            "/v1/missions/create",
            json={
                "goal": "First live mission",
                "category": "test",
                "constraints": {},
                "results": {},
            },
        )
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1.get("ok") is True
        mission_id_1 = body1["mission_id"]

        r2 = client.post(
            "/v1/missions/create",
            json={
                "goal": "Second mission",
                "category": "test",
                "constraints": {},
                "results": {},
            },
        )
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2.get("ok") is True
        mission_id_2 = body2["mission_id"]

        listed = client.get("/v1/missions/list")
        assert listed.status_code == 200
        listed_body = listed.json()
        assert listed_body.get("ok") is True

        missions = listed_body["missions"]
        mission_ids = {m.get("mission_id") for m in missions}
        assert mission_id_1 in mission_ids
        assert mission_id_2 in mission_ids
        assert listed_body.get("count", 0) >= 2

        run_resp = client.post(f"/v1/missions/run?mission_id={mission_id_1}")
        assert run_resp.status_code == 200
        run_body = run_resp.json()
        assert run_body.get("ok") is True
        assert run_body.get("status") == "RUNNING"

        post_run_list = client.get("/v1/missions/list")
        assert post_run_list.status_code == 200
        post_run_body = post_run_list.json()
        post_run = next(
            (
                m
                for m in post_run_body["missions"]
                if m.get("mission_id") == mission_id_1
            ),
            None,
        )
        assert post_run is not None
        assert post_run.get("status") == "RUNNING"
