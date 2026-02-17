# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Smoke test for doctor script.
Ensures doctor runs to completion and returns one of the allowed codes (0,2,3)
when server may or may not be running.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCTOR = ROOT / "tools" / "doctor.py"


def main():
    try:
        proc = subprocess.run([sys.executable, str(DOCTOR)], capture_output=True, text=True, timeout=180, cwd=ROOT)
    except Exception as exc:
        print(f"doctor invocation failed: {exc}")
        sys.exit(1)
    if proc.returncode not in (0, 2, 3):
        print(proc.stdout)
        print(proc.stderr)
        print(f"Unexpected exit code: {proc.returncode}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()

