from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_observatory_log_compression_script() -> None:
    subprocess.run(
        [sys.executable, "scripts/compress_observatory_logs.py"],
        cwd=ROOT,
        check=True,
    )
    log_dir = ROOT / "observatory" / "logs"
    assert log_dir.exists()
    assert any(log_dir.glob("*.log.gz"))
