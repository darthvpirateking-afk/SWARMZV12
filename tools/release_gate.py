#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "SWARMZ_ONE_BUTTON_START.cmd",
    "SWARMZ_ONE_BUTTON_START.ps1",
    "APP_STORE_BUILD.cmd",
    "PHONE_APP_QUICKSTART.md",
    "docs/PRIVACY_POLICY.md",
    "mobile/app_store_wrapper/README.md",
    "mobile/app_store_wrapper/package.json",
    "mobile/app_store_wrapper/capacitor.config.json",
    "mobile/app_store_wrapper/store/PLAY_STORE_RELEASE_CHECKLIST.md",
    "mobile/app_store_wrapper/store/APP_STORE_CONNECT_RELEASE_CHECKLIST.md",
    "mobile/app_store_wrapper/store/APP_METADATA_TEMPLATE.json",
    "mobile/app_store_wrapper/store/STORE_SUBMISSION_NOTES.md",
    "config/runtime.local.json",
    "config/runtime.render.json",
]


def _check_files() -> List[str]:
    missing: List[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)
    return missing


def _check_runtime_config() -> Tuple[bool, str]:
    runtime_path = ROOT / "config" / "runtime.json"
    if not runtime_path.exists():
        return False, "config/runtime.json missing"

    try:
        data = json.loads(runtime_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"config/runtime.json parse failed: {exc}"

    required = ["apiBaseUrl", "uiBaseUrl", "bind", "port"]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"config/runtime.json missing keys: {', '.join(missing)}"

    return (
        True,
        f"apiBaseUrl={data.get('apiBaseUrl')} bind={data.get('bind')} port={data.get('port')}",
    )


def _run_smoke() -> int:
    cmd = [sys.executable, str(ROOT / "tools" / "release_smoke.py")]
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="SWARMZ release gate")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run tools/release_smoke.py as part of gate",
    )
    args = parser.parse_args()

    print("== SWARMZ RELEASE GATE ==")

    failed = False

    missing_files = _check_files()
    if missing_files:
        failed = True
        print("FAIL: required files missing")
        for rel in missing_files:
            print(f"  - {rel}")
    else:
        print("PASS: required files present")

    runtime_ok, runtime_info = _check_runtime_config()
    if not runtime_ok:
        failed = True
        print(f"FAIL: {runtime_info}")
    else:
        print(f"PASS: runtime config ({runtime_info})")

    if args.smoke:
        print("Running release smoke...")
        rc = _run_smoke()
        if rc != 0:
            failed = True
            print(f"FAIL: release smoke failed (exit={rc})")
        else:
            print("PASS: release smoke")

    if failed:
        print("\nRESULT: FAIL")
        return 1

    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
