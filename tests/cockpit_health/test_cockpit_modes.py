from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from swarmz_server import app

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "cockpit" / "modes" / "registry.json"


def test_registry_exists() -> None:
    assert REGISTRY.exists()


def test_registry_entries_have_id_and_path() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    entries = payload.get("modes", [])
    assert isinstance(entries, list) and entries
    for entry in entries:
        assert entry.get("id")
        assert entry.get("path")


def test_each_mode_file_loads_without_404() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    entries = payload.get("modes", [])
    with TestClient(app) as client:
        for entry in entries:
            rel = str(entry["path"]).replace("cockpit/", "", 1)
            resp = client.get(f"/cockpit/{rel}")
            assert resp.status_code != 404, entry["path"]
            assert resp.status_code == 200, entry["path"]
