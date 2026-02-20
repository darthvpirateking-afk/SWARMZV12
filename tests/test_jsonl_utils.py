import os
import tempfile
from pathlib import Path
from swarmz_runtime.storage.jsonl_utils import read_jsonl, write_jsonl

def test_read_jsonl_returns_tuple_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing.jsonl"
        result = read_jsonl(missing)
        assert isinstance(result, tuple)
        assert result[0] == []

def test_read_jsonl_returns_tuple_empty_file():
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "empty.jsonl"
        empty.touch()
        result = read_jsonl(empty)
        assert isinstance(result, tuple)
        assert result[0] == []

def test_read_jsonl_returns_tuple_normal_file():
    with tempfile.TemporaryDirectory() as tmp:
        normal = Path(tmp) / "normal.jsonl"
        data = [{"a": 1}, {"b": 2}]
        write_jsonl(normal, data)
        result = read_jsonl(normal)
        assert isinstance(result, tuple)
        assert result[0] == data
