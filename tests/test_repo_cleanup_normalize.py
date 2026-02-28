from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBS_CLEANUP = ROOT / "observatory" / "cleanup"


def test_cleanup_script_runs_without_deleting_canonical_tests_folder() -> None:
    subprocess.run(
        [sys.executable, "scripts/repo_cleanup_normalize.py"],
        cwd=ROOT,
        check=True,
    )
    reports = sorted(OBS_CLEANUP.glob("cleanup-report-*.json"))
    assert reports, "cleanup report not generated"
    latest = json.loads(reports[-1].read_text(encoding="utf-8-sig"))
    deleted_dirs = latest.get("deleted_dirs", [])
    assert "tests" not in deleted_dirs
