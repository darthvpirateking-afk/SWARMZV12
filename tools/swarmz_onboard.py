#!/usr/bin/env python3
"""SWARMZ Onboard Wizard

Guides first-time setup:
- choose bind + port
- write config/runtime.json
- ensure operator anchor exists
- run doctor
- start server once and confirm /v1/health
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "runtime.json"
DATA_DIR = ROOT / "data"


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def prompt_bind() -> str:
    print("Bind options:")
    print("  1) 0.0.0.0 (LAN + phone) [recommended]")
    print("  2) 127.0.0.1 (desktop only)")
    choice = (input("Select [1/2, default 1]: ") or "1").strip()
    return "127.0.0.1" if choice == "2" else "0.0.0.0"


def prompt_port() -> int:
    while True:
        raw = (input("Port [8012]: ") or "8012").strip()
        try:
            port = int(raw)
            if 1 <= port <= 65535:
                return port
        except ValueError:
            pass
        print("Enter a valid port between 1-65535.")


def write_runtime_config(host: str, port: int) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    api_base = f"http://{host}:{port}"
    ui_base = f"{api_base}/"
    CONFIG_PATH.write_text(json.dumps({"api_base": api_base, "ui_base": ui_base}, indent=2))
    print(f"Wrote {CONFIG_PATH}")


def ensure_anchor() -> None:
    try:
        from core.operator_anchor import load_or_create_anchor
    except Exception:
        from swarmz_runtime.core.operator_anchor import load_or_create_anchor
    anchor = load_or_create_anchor(str(DATA_DIR))
    print(f"Operator anchor ready ({DATA_DIR / 'operator_anchor.json'})")
    if anchor.get("operator_public_key"):
        print(f"Public key: {anchor['operator_public_key'][:12]}…")


def run_doctor() -> int:
    doctor = ROOT / "tools" / "swarmz_doctor.py"
    if not doctor.exists():
        print("Doctor missing; skipping")
        return 0
    print("\nRunning doctor…")
    proc = subprocess.run([sys.executable, str(doctor)], cwd=ROOT)
    return proc.returncode


def wait_for_health(port: int, host: str, timeout: float = 20.0) -> bool:
    url = f"http://127.0.0.1:{port}/v1/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with request.urlopen(url, timeout=3) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                data = json.loads(body)
                if data.get("ok"):
                    print("Health ok:", json.dumps(data, indent=2))
                    return True
        except Exception:
            time.sleep(1)
    print(f"Health check failed after {timeout}s (tried {url})")
    return False


def start_server_once(host: str, port: int) -> bool:
    cmd = [sys.executable, str(ROOT / "run_server.py"), "--port", str(port), "--host", host]
    print(f"Starting server once: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    ok = False
    try:
        ok = wait_for_health(port, host)
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if proc.stdout:
        lines = proc.stdout.read().strip().splitlines()[-8:]
        print("--- server output (tail) ---")
        for line in lines:
            print(line)
        print("---------------------------")
    return ok


def main():
    print("SWARMZ Onboard Wizard")
    host = prompt_bind()
    port = prompt_port()

    write_runtime_config(host if host != "0.0.0.0" else "127.0.0.1", port)
    ensure_anchor()

    rc = run_doctor()
    if rc != 0:
        print("Doctor reported issues; you can rerun after fixing.")

    ok = start_server_once(host, port)
    lan = _lan_ip()
    print("\nLocal URL:", f"http://127.0.0.1:{port}/")
    print("LAN URL:", f"http://{lan}:{port}/")

    if ok:
        print("Onboarding complete. You can now run SWARMZ_UP or SWARMZ_DAEMON_UP.")
    else:
        print("Server did not pass health; check logs above and doctor output.")


if __name__ == "__main__":
    main()
