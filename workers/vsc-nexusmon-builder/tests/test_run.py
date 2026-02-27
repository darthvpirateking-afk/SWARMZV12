from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_worker_module():
    module_path = Path(__file__).resolve().parents[1] / "run.py"
    spec = importlib.util.spec_from_file_location("vsc_nexusmon_builder_run", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load worker module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_rejects_missing_module_name() -> None:
    worker_run = _load_worker_module()
    with pytest.raises(ValueError, match="module_name"):
        worker_run.validate({"requirements": ["a"]})


def test_run_returns_planned_envelope() -> None:
    worker_run = _load_worker_module()
    result = worker_run.run({"module_name": "hello_world", "requirements": ["prints hello"]})
    assert result["status"] == "planned"
    assert "hello_world" in result["summary"]
    assert result["generated_files"] == [
        "plugins/hello_world/manifest.json",
        "plugins/hello_world/index.js",
        "plugins/hello_world/README.md",
    ]


def test_emit_artifacts_writes_result_files(tmp_path: Path) -> None:
    worker_run = _load_worker_module()
    output = worker_run.run({"module_name": "hello_world", "requirements": []})
    emit_result = worker_run.emit_artifacts(output, tmp_path)
    result_file = tmp_path / "result.json"
    summary_file = tmp_path / "artifact_summary.txt"

    assert result_file.exists()
    assert summary_file.exists()
    assert len(emit_result["generated_files"]) == 2
    stored = json.loads(result_file.read_text(encoding="utf-8"))
    assert stored["status"] == "planned"
