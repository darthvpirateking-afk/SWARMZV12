#!/usr/bin/env python3
"""Switch SWARMZ runtime profile.

Usage:
  python tools/switch_runtime_profile.py local
  python tools/switch_runtime_profile.py render
  python tools/switch_runtime_profile.py --show
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
RUNTIME = CONFIG_DIR / "runtime.json"
PROFILE_FILES = {
    "local": CONFIG_DIR / "runtime.local.json",
    "render": CONFIG_DIR / "runtime.render.json",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _show_current() -> int:
    if not RUNTIME.exists():
        print("runtime.json missing")
        return 1
    data = _load_json(RUNTIME)
    print("Active runtime profile:")
    print(f"  apiBaseUrl: {data.get('apiBaseUrl', '')}")
    print(f"  uiBaseUrl:  {data.get('uiBaseUrl', '')}")
    print(f"  bind:       {data.get('bind', '')}")
    print(f"  port:       {data.get('port', '')}")
    print(f"  offline:    {data.get('offlineMode', False)}")
    return 0


def _switch(profile: str) -> int:
    src = PROFILE_FILES.get(profile)
    if not src or not src.exists():
        print(f"Profile not found: {profile}")
        return 1

    # Validate profile JSON before writing.
    data = _load_json(src)
    required = ["apiBaseUrl", "uiBaseUrl", "bind", "port"]
    missing = [k for k in required if k not in data]
    if missing:
        print(f"Invalid profile ({profile}) missing keys: {', '.join(missing)}")
        return 1

    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, RUNTIME)

    print(f"Switched runtime profile -> {profile}")
    print(f"  source:     {src.name}")
    print(f"  apiBaseUrl: {data.get('apiBaseUrl', '')}")
    print(f"  uiBaseUrl:  {data.get('uiBaseUrl', '')}")
    print(f"  bind:       {data.get('bind', '')}")
    print(f"  port:       {data.get('port', '')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Switch SWARMZ runtime profile")
    parser.add_argument("profile", nargs="?", choices=sorted(PROFILE_FILES.keys()))
    parser.add_argument("--show", action="store_true", help="Show active runtime.json settings")
    args = parser.parse_args()

    if args.show:
        return _show_current()
    if not args.profile:
        parser.print_help()
        return 1
    return _switch(args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
