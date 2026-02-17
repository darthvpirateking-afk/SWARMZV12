# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_core_safety.py â€” Tests for core safety helpers (Commit 1).

Tests: atomic, time_source, schema_guard, cold_start.
"""

import json
import tempfile
from pathlib import Path


def test_atomic_write_json():
    from core.atomic import atomic_write_json
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sub" / "test.json"
        atomic_write_json(p, {"a": 1, "b": [2, 3]})
        assert p.exists()
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data == {"a": 1, "b": [2, 3]}
        # No leftover .tmp file
        assert not p.with_suffix(".tmp").exists()


def test_atomic_append_jsonl():
    from core.atomic import atomic_append_jsonl
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "log.jsonl"
        atomic_append_jsonl(p, {"x": 1})
        atomic_append_jsonl(p, {"x": 2})
        lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 2
        assert lines[0]["x"] == 1
        assert lines[1]["x"] == 2


def test_time_source_now():
    from core.time_source import now
    ts = now()
    assert ts.endswith("Z")
    assert "T" in ts
    assert len(ts) > 20


def test_time_source_today():
    from core.time_source import today
    d = today()
    assert len(d) == 10  # YYYY-MM-DD
    assert d.count("-") == 2


def test_time_source_mission_timestamp():
    from core.time_source import mission_timestamp
    ts = mission_timestamp()
    assert ts.isdigit()
    assert len(ts) >= 13  # ms precision


def test_schema_guard_valid():
    from core.schema_guard import validate
    ok, errs = validate(
        {"mission_id": "m1", "status": "PENDING", "extra": 42},
        required={"mission_id": "str", "status": "str"},
    )
    assert ok
    assert errs == []


def test_schema_guard_missing_field():
    from core.schema_guard import validate
    ok, errs = validate(
        {"status": "PENDING"},
        required={"mission_id": "str", "status": "str"},
    )
    assert not ok
    assert any("missing" in e for e in errs)


def test_schema_guard_wrong_type():
    from core.schema_guard import validate
    ok, errs = validate(
        {"mission_id": 123, "status": "PENDING"},
        required={"mission_id": "str", "status": "str"},
    )
    assert not ok
    assert any("expected str" in e for e in errs)


def test_schema_guard_optional():
    from core.schema_guard import validate
    ok, errs = validate(
        {"mission_id": "m1", "status": "OK", "score": "not_a_float"},
        required={"mission_id": "str"},
        optional={"score": "float"},
    )
    assert not ok
    assert any("score" in e for e in errs)


def test_cold_start_idempotent():
    """cold_start.ensure_cold_start() creates missing files without overwriting existing ones."""
    from core.cold_start import ensure_cold_start
    result = ensure_cold_start()
    assert result["ok"] is True
    # data dir exists
    assert Path(result["data_dir"]).exists()
    # system_identity.txt exists
    assert Path(result["system_identity"]).exists()
    # calling again is safe
    result2 = ensure_cold_start()
    assert result2["ok"] is True

