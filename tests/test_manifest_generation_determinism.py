"""Deterministic generation check for manifest test stubs."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_generator(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "tools/gen_manifest_tests.py",
            "--manifest-dir",
            "config/manifests",
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
    )


def _snapshot(output_dir: Path) -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(output_dir.glob("test_manifest_*.py"))
    }


def test_generation_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _run_generator(first)
    _run_generator(second)

    assert _snapshot(first) == _snapshot(second)
