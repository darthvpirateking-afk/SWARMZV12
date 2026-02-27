from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from nexusmon.runtime.context import build_context
from nexusmon.runtime.executor import execute_worker
from nexusmon.runtime.registry import list_workers


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "nexusmon/workers/registry.json"
WORKER_DIR = ROOT / "workers/vsc-nexusmon-builder"


def test_registry_load_includes_builder_worker() -> None:
    workers = list_workers(REGISTRY_PATH)
    assert any(w.get("id") == "vsc-nexusmon-builder" for w in workers)


def test_mission_template_loads_and_references_valid_worker() -> None:
    template = json.loads(
        (ROOT / "nexusmon/missions/templates/build_module.json").read_text(encoding="utf-8")
    )
    assert template["mission"] == "build_module"
    assert template["worker"] == "vsc-nexusmon-builder"


def test_executor_runs_worker_and_writes_artifact() -> None:
    payload = {"module_name": "hello_world", "requirements": ["print hello"]}
    result = execute_worker(WORKER_DIR, payload, build_context(ROOT))
    assert result["ok"] is True
    assert result["worker_id"] == "vsc-nexusmon-builder"
    assert result["result"]["status"] == "planned"
    artifact_dir = Path(result["artifact_dir"])
    if not artifact_dir.is_absolute():
        artifact_dir = ROOT / artifact_dir
    assert artifact_dir.exists()


def test_cli_worker_list_resolves_registry() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "nexusmon.cli", "worker", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert any(item.get("id") == "vsc-nexusmon-builder" for item in payload)
