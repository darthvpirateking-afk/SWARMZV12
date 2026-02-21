"""
test_mission_jsonl_robust.py – Tests for robust JSONL handling and mission
create/list endpoints.

Usage::

    python -m pytest test_mission_jsonl_robust.py -v
    # or, for a quick smoke test against a running server:
    python test_mission_jsonl_robust.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from swarmz_runtime.storage.jsonl_utils import read_jsonl, write_jsonl, append_jsonl

# ---------------------------------------------------------------------------
# JSONL utility tests
# ---------------------------------------------------------------------------


class TestReadJsonl:
    def test_missing_file(self, tmp_path):
        assert read_jsonl(tmp_path / "nope.jsonl") == []

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        assert read_jsonl(p) == []

    def test_blank_lines_skipped(self, tmp_path):
        p = tmp_path / "blanks.jsonl"
        p.write_text('\n\n{"a":1}\n\n{"b":2}\n\n')
        result = read_jsonl(p)
        assert result == [{"a": 1}, {"b": 2}]

    def test_malformed_lines_quarantined(self, tmp_path):
        p = tmp_path / "bad.jsonl"
        p.write_text('{"ok":1}\nNOT_JSON\n{"ok":2}\n')
        result = read_jsonl(p)
        assert result == [{"ok": 1}, {"ok": 2}]
        # quarantine sidecar should exist
        q = p.with_suffix(".jsonl.quarantine")
        assert q.exists()

    def test_valid_file(self, tmp_path):
        p = tmp_path / "good.jsonl"
        p.write_text('{"x":1}\n{"x":2}\n{"x":3}\n')
        assert len(read_jsonl(p)) == 3


class TestWriteJsonl:
    def test_creates_file(self, tmp_path):
        p = tmp_path / "sub" / "out.jsonl"
        write_jsonl(p, [{"a": 1}])
        assert p.exists()
        lines = p.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == {"a": 1}

    def test_overwrites(self, tmp_path):
        p = tmp_path / "over.jsonl"
        write_jsonl(p, [{"x": 1}, {"x": 2}])
        write_jsonl(p, [{"y": 99}])
        recs = read_jsonl(p)
        assert recs == [{"y": 99}]


class TestAppendJsonl:
    def test_creates_and_appends(self, tmp_path):
        p = tmp_path / "append.jsonl"
        append_jsonl(p, {"a": 1})
        append_jsonl(p, {"b": 2})
        recs = read_jsonl(p)
        assert recs == [{"a": 1}, {"b": 2}]


# ---------------------------------------------------------------------------
# Database robustness tests
# ---------------------------------------------------------------------------


class TestDatabaseRobustJsonl:
    def test_load_missions_with_corrupted_file(self, tmp_path):
        from swarmz_runtime.storage.db import Database

        db = Database(str(tmp_path / "data"))
        # Write a corrupted missions file
        db.missions_file.write_text(
            '{"id":"m1","goal":"g","category":"coin","constraints":{},'
            '"expiry":null,"status":"pending","created_at":"2025-01-01",'
            '"updated_at":"2025-01-01","leverage_score":0,"revisit_interval":3600}\n'
            "GARBAGE_LINE\n"
            '{"id":"m2","goal":"g2","category":"forge","constraints":{},'
            '"expiry":null,"status":"active","created_at":"2025-01-01",'
            '"updated_at":"2025-01-01","leverage_score":0,"revisit_interval":3600}\n'
        )
        missions = db.load_all_missions()
        assert len(missions) == 2
        assert missions[0]["id"] == "m1"
        assert missions[1]["id"] == "m2"

    def test_load_missions_missing_file(self, tmp_path):
        from swarmz_runtime.storage.db import Database

        db = Database(str(tmp_path / "data"))
        db.missions_file.unlink(missing_ok=True)
        assert db.load_all_missions() == []

    def test_load_audit_log_corrupted(self, tmp_path):
        from swarmz_runtime.storage.db import Database

        db = Database(str(tmp_path / "data"))
        db.audit_file.write_text('BAD\n{"event_type":"test"}\nBAD\n')
        entries = db.load_audit_log()
        assert len(entries) == 1


# ---------------------------------------------------------------------------
# Engine mission create tests
# ---------------------------------------------------------------------------


class TestMissionCreate:
    def test_create_valid(self, tmp_path):
        from swarmz_runtime.core.engine import SwarmzEngine

        engine = SwarmzEngine(data_dir=str(tmp_path / "data"))
        result = engine.create_mission(goal="test", category="coin", constraints={})
        assert "mission_id" in result
        assert result["status"] == "created"

    def test_create_invalid_category_returns_error(self, tmp_path):
        from swarmz_runtime.core.engine import SwarmzEngine

        engine = SwarmzEngine(data_dir=str(tmp_path / "data"))
        result = engine.create_mission(
            goal="test", category="invalid_cat", constraints={}
        )
        assert "error" in result
        assert "mission_id" not in result

    def test_list_after_create(self, tmp_path):
        from swarmz_runtime.core.engine import SwarmzEngine

        engine = SwarmzEngine(data_dir=str(tmp_path / "data"))
        engine.create_mission(goal="m1", category="coin", constraints={})
        engine.create_mission(goal="m2", category="forge", constraints={})
        missions = engine.list_missions()
        assert len(missions) == 2


# ---------------------------------------------------------------------------
# Smoke test against a running server (optional, run as script)
# ---------------------------------------------------------------------------


def _smoke_test():
    """Quick smoke test against a running server at localhost:8012."""
    import requests

    base = "http://localhost:8012"

    # 1. Mission create
    r = requests.post(
        f"{base}/v1/missions/create",
        json={"goal": "smoke", "category": "coin", "constraints": {}},
    )
    assert r.status_code == 200, f"create failed: {r.status_code} {r.text}"
    data = r.json()
    assert "mission_id" in data
    print(f"  ✓ create → {data['mission_id']}")

    # 2. Mission list
    r = requests.get(f"{base}/v1/missions/list")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    print(f"  ✓ list → {data['count']} missions")

    # 3. Debug storage check
    r = requests.get(f"{base}/v1/debug/storage_check")
    assert r.status_code == 200, f"storage_check failed: {r.status_code} {r.text}"
    data = r.json()
    assert "missions_jsonl" in data
    print(f"  ✓ storage_check → {data}")

    print("\nAll smoke tests passed!")


if __name__ == "__main__":
    _smoke_test()
