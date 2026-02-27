from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required")
def test_nexusmon_wiring_cli_and_patchpack_flow(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text(
        json.dumps({"module_name": "hello_world_wire", "requirements": ["print hello"]}),
        encoding="utf-8",
    )

    list_proc = subprocess.run(
        [sys.executable, "-m", "nexusmon.cli", "worker", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert list_proc.returncode == 0, list_proc.stderr
    listed = json.loads(list_proc.stdout)
    assert any(item.get("id") == "vsc-nexusmon-builder" for item in listed)

    run_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "nexusmon.cli",
            "worker",
            "run",
            "vsc-nexusmon-builder",
            "--input",
            str(input_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_proc.returncode == 0, run_proc.stderr
    run_payload = json.loads(run_proc.stdout)
    assert run_payload["ok"] is True
    assert run_payload["result"]["status"] == "planned"

    validate_proc = subprocess.run(
        ["node", "tools/validators/noCoreMutation.js", "nexusmon/workers/patchpack.example.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validate_proc.returncode == 0, validate_proc.stderr
    assert json.loads(validate_proc.stdout)["ok"] is True

    apply_proc = subprocess.run(
        [
            "node",
            "tools/patchpack/applyPatchpack.js",
            "--patchpack",
            "nexusmon/workers/patchpack.example.json",
            "--root",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply_proc.returncode == 0, apply_proc.stderr
    apply_payload = json.loads(apply_proc.stdout)
    assert apply_payload["ok"] is True
    assert (tmp_path / "plugins/hello_world/manifest.json").exists()
    assert (tmp_path / "plugins/hello_world/index.js").exists()
    assert (tmp_path / "plugins/hello_world/README.md").exists()
