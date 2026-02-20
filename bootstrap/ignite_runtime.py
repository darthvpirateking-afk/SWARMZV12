# /bootstrap/ignite_runtime.py
"""
SWARMZ Runtime Ignition
═══════════════════════
Starts the Python backend (uvicorn) and the React cockpit UI (vite)
in parallel, streams their combined logs, and tears both down on Ctrl-C.
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

procs: list[subprocess.Popen] = []


def run(cmd, cwd=None, shell=False):
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell,
    )
    procs.append(p)
    return p


def shutdown(*_):
    print("\n=== SHUTTING DOWN ===")
    for p in procs:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            p.kill()
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def ensure_node_modules():
    if not (UI_DIR / "node_modules").exists():
        print("[ui] node_modules missing — running npm install …")
        subprocess.run(["npm", "install"], cwd=UI_DIR, shell=True, check=True)


def main():
    print("=" * 44)
    print("  SWARMZ RUNTIME IGNITION")
    print("=" * 44)

    # 1. Ensure UI deps
    ensure_node_modules()

    # 2. Backend
    backend = run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        cwd=ROOT,
    )
    print("[backend] starting  →  http://localhost:8000")

    # 3. UI dev server
    ui = run(["npm", "run", "dev"], cwd=UI_DIR, shell=True)
    print("[ui]      starting  →  http://localhost:5173")

    time.sleep(3)
    print()
    print("=== STATUS ===")
    print("  backend : http://localhost:8000")
    print("  ui      : http://localhost:5173")
    print("  cockpit : http://localhost:5173  (Health + Governor cards)")
    print()
    print("=== STREAMING LOGS  (Ctrl-C to stop) ===")

    while True:
        for proc, label in [(backend, "backend"), (ui, "ui")]:
            if proc.poll() is not None:
                continue
            line = proc.stdout.readline()
            if line:
                print(f"[{label}] {line.rstrip()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        shutdown()
