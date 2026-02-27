import json
from pathlib import Path

from api.companion_core_service import CompanionCoreService
from core import companion


def _setup_temp_memory(monkeypatch, tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OFFLINE_MODE", "true")
    monkeypatch.setattr(companion, "DATA_DIR", data_dir)
    monkeypatch.setattr(companion, "AUDIT_FILE", data_dir / "audit.jsonl")
    monkeypatch.setattr(companion, "_memory_path", lambda: data_dir / "companion_memory.json")
    return data_dir


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def test_companion_chat_persists_operator_turns(monkeypatch, tmp_path):
    data_dir = _setup_temp_memory(monkeypatch, tmp_path)

    result = companion.chat("do you remember me", operator_id="op-regan")
    assert result["ok"] is True
    assert result["operator_id"] == "op-regan"

    turns = _read_jsonl(data_dir / "conversation_turns.jsonl")
    assert len(turns) == 1
    assert turns[0]["operator_id"] == "op-regan"
    assert "remember me" in turns[0]["message"].lower()


def test_companion_builds_long_term_memory_after_multiple_turns(monkeypatch, tmp_path):
    data_dir = _setup_temp_memory(monkeypatch, tmp_path)

    for i in range(6):
        reply = companion.chat(f"turn {i}: help me plan next step", operator_id="op-regan")
        assert reply["ok"] is True

    memory_rows = _read_jsonl(data_dir / "operator_memory.jsonl")
    assert memory_rows, "Expected long-term memory rows after compaction interval"
    assert memory_rows[-1]["operator_id"] == "op-regan"
    assert memory_rows[-1]["summary"]


def test_companion_core_service_passes_operator_id(monkeypatch, tmp_path):
    data_dir = _setup_temp_memory(monkeypatch, tmp_path)
    service = CompanionCoreService()

    response = service.message("status", operator_id="op-regan")
    assert response.ok is True

    turns = _read_jsonl(data_dir / "conversation_turns.jsonl")
    assert turns and turns[-1]["operator_id"] == "op-regan"
