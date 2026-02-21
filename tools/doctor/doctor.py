# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Doctor â€” Diagnostic tool for operator troubleshooting.

Prints:
  - detected host/port bindings
  - which processes are running
  - last errors from logs
  - where data lives
  - recommended next fix (if any)
"""

import json
import os
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
CONFIG_PATH = ROOT / "config" / "runtime.json"
LOG_FILES = [
    DATA_DIR / "server_live.log",
    DATA_DIR / "server_debug.log",
    DATA_DIR / "audit.jsonl",
]


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}


def check_port(port):
    """Check if a port is listening."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1] if parts else "?"
                return True, pid
    except Exception:
        pass
    return False, None


def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def tail_file(path, n=10):
    """Return last n lines of a file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-n:]
    except Exception:
        return []


def find_errors_in_log(path, n=5):
    """Find last N error lines in a log file."""
    errors = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            low = line.lower()
            if "error" in low or "exception" in low or "traceback" in low:
                errors.append(line.strip()[:200])
    except Exception:
        pass
    return errors[-n:]


def main():
    print("SWARMZ DOCTOR")
    print(f"Run at: {datetime.now().isoformat()}")
    print(f"Root:   {ROOT}")

    # â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("CONFIGURATION")
    cfg = load_config()
    if "_error" in cfg:
        print(f"  [WARN] Cannot load config: {cfg['_error']}")
    else:
        port = cfg.get("port", 8012)
        bind = cfg.get("bind", "0.0.0.0")
        offline = cfg.get("offlineMode", False)
        print(f"  Port:         {port}")
        print(f"  Bind:         {bind}")
        print(f"  Offline Mode: {offline}")
        zapier = cfg.get("integrations", {}).get("zapier", {})
        if zapier:
            print(
                f"  Zapier:       enabled={zapier.get('enabled')}, hook={'SET' if zapier.get('zapier_catch_hook_url') else 'NOT SET'}"
            )

    # â”€â”€ Port Status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("PORT STATUS")
    port = cfg.get("port", 8012) if isinstance(cfg, dict) else 8012
    listening, pid = check_port(port)
    if listening:
        print(f"  Port {port}: LISTENING (PID {pid})")
    else:
        print(f"  Port {port}: NOT LISTENING")

    # â”€â”€ LAN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("NETWORK")
    lan_ip = get_lan_ip()
    print(f"  LAN IP:  {lan_ip}")
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  LAN:     http://{lan_ip}:{port}")

    # â”€â”€ Data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("DATA STORAGE")
    if DATA_DIR.exists():
        files = sorted(DATA_DIR.glob("*"))
        print(f"  Directory: {DATA_DIR}")
        print(f"  Files: {len(files)}")
        for f in files[:20]:
            size = f.stat().st_size if f.is_file() else 0
            kind = "DIR" if f.is_dir() else f"{size:,}b"
            print(f"    {f.name:40s} {kind}")
    else:
        print("  [WARN] data/ directory does not exist")

    # â”€â”€ Logs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("RECENT ERRORS (last 5 per log)")
    found_errors = False
    for lf in LOG_FILES:
        if lf.exists():
            errs = find_errors_in_log(lf)
            if errs:
                found_errors = True
                print(f"  [{lf.name}]")
                for e in errs:
                    print(f"    {e}")
    if not found_errors:
        print("  No recent errors found.")

    # â”€â”€ Recommendations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    section("RECOMMENDATIONS")
    recommendations = []
    if not listening:
        recommendations.append(
            "Server not running. Start with: SWARMZ_UP.cmd or SWARMZ_UP.ps1"
        )
    if isinstance(cfg, dict) and cfg.get("bind") == "127.0.0.1":
        recommendations.append(
            "bind is 127.0.0.1 â€” phone access requires 0.0.0.0 in config/runtime.json"
        )
    if isinstance(cfg, dict):
        secret = cfg.get("integrations", {}).get("zapier", {}).get("shared_secret", "")
        if secret == "change-me-to-a-real-secret":
            recommendations.append(
                "Change the Zapier shared_secret in config/runtime.json"
            )
    if not recommendations:
        recommendations.append("System looks healthy. No action needed.")
    for r in recommendations:
        print(f"  -> {r}")

    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Doctor error: {e}")
        sys.exit(1)
