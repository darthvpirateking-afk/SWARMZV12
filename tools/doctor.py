# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Doctor

Checks runtime status, runs runtime_check, runs profiling, dumps profile/audit tails,
and emits a verdict: STABLE / DEGRADED / UNSTABLE.

Standard library only. Designed for Windows-friendly execution.
"""

import subprocess
import sys
import json
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROFILE_PATH = DATA_DIR / "profile.txt"
AUDIT_PATH = DATA_DIR / "audit.jsonl"
RUNTIME_CHECK = ROOT / "tools" / "runtime_check.py"
RUN_SWARMZ = ROOT / "run_swarmz.py"
STATUS_URL = "http://127.0.0.1:8012/v1/runtime/status"
ENABLE_PROFILING = True  # Toggle for profiling runs


def _section(title: str):
    print("\n" + "=" * 12 + f" {title} " + "=" * 12)


def get_runtime_status(timeout: float = 5.0):
    try:
        with request.urlopen(STATUS_URL, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(body)
            except Exception:
                data = {"raw": body}
            return True, data
    except Exception as exc:
        return False, str(exc)


def run_cmd(cmd):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=ROOT)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out
    except Exception as exc:
        return 1, str(exc)


def tail_file(path: Path, lines: int = 10, max_chars: int = 4000):
    if not path.exists():
        return f"(missing {path})"
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            pos = f.tell()
            buf = b""
            newlines = 0
            while pos > 0 and newlines <= lines:
                pos -= 1
                f.seek(pos)
                ch = f.read(1)
                if ch == b"\n":
                    newlines += 1
                buf = ch + buf
                if len(buf) > max_chars:
                    break
        return buf.decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"(error reading {path}: {exc})"


def main():
    problems = 0

    _section("Runtime Status")
    ok, payload = get_runtime_status()
    if not ok:
        problems += 1
        print("status: FAIL", payload)
    else:
        if isinstance(payload, dict) and payload.get("error"):
            problems += 1
        print(json.dumps(payload, indent=2))

    _section("Runtime Check")
    rc_code, rc_out = run_cmd([sys.executable, str(RUNTIME_CHECK)])
    if rc_code != 0:
        problems += 1
    if "busy" in rc_out.lower() or "loop" in rc_out.lower():
        problems += 1
    print(rc_out.strip())

    _section("Profiling Run")
    if ENABLE_PROFILING:
        prof_code, prof_out = run_cmd([sys.executable, str(RUN_SWARMZ), "--profile"])
        if prof_code != 0:
            problems += 1
        print(prof_out.strip())
    else:
        print("Profiling is disabled.")

    _section("Profile Snippet")
    if PROFILE_PATH.exists():
        snippet = tail_file(PROFILE_PATH, lines=200, max_chars=4000)
        print(snippet)
    else:
        problems += 1
        print(f"(missing {PROFILE_PATH})")

    _section("Audit Tail")
    print(tail_file(AUDIT_PATH, lines=10, max_chars=4000))

    if problems == 0:
        verdict = "STABLE"
        exit_code = 0
    elif problems == 1:
        verdict = "DEGRADED"
        exit_code = 2
    else:
        verdict = "UNSTABLE"
        exit_code = 3

    _section("VERDICT")
    print(verdict)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

