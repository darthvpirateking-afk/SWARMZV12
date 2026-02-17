from core.license_guard import enforce
enforce()
# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
import argparse
import json
import os
import socket
import threading
from pathlib import Path

import uvicorn


ROOT = Path(__file__).resolve().parent
RUNTIME_CONFIG = ROOT / "config" / "runtime.json"


def _load_runtime_config():
    if not RUNTIME_CONFIG.exists():
        return {}
    try:
        return json.loads(RUNTIME_CONFIG.read_text())
    except Exception:
        return {}


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _resolve_host_port() -> tuple[str, int]:
    cfg = _load_runtime_config()
    host = os.environ.get("HOST") or cfg.get("bind") or cfg.get("host") or "0.0.0.0"
    port_val = os.environ.get("PORT") or cfg.get("port") or cfg.get("api_port") or cfg.get("uiPort") or 8012
    try:
        port = int(port_val)
    except Exception:
        port = 8012
    return host, port


def main():
    parser = argparse.ArgumentParser(description="Run SWARMZ server")
    cfg_host, cfg_port = _resolve_host_port()
    parser.add_argument("--port", type=int, default=cfg_port, help=f"Port to bind (default {cfg_port})")
    parser.add_argument("--host", type=str, default=cfg_host, help="Host/interface to bind (0.0.0.0 or 127.0.0.1)")
    args = parser.parse_args()

    lan = _lan_ip()
    print(f"LOCAL: http://127.0.0.1:{args.port}/")
    print(f"LAN:   http://{lan}:{args.port}/")
    print("PHONE: open LAN URL on same Wi-Fi")
    print(f"HOST:  {args.host}")

    # Cold start: ensure all data files/dirs exist
    try:
        from core.cold_start import ensure_cold_start
        result = ensure_cold_start()
        print(f"[COLD START] {result.get('data_dir', 'data')} â€” OK")
    except Exception as exc:
        print(f"[COLD START] WARNING: {exc}")

    # Initialise engine singletons (fast, safe)
    try:
        from core.context_pack import load as _load_engines
        _load_engines()
        print("[ENGINES] All engines loaded.")
    except Exception as exc:
        print(f"[ENGINES] WARNING: {exc}")

    # Start daily scheduler as daemon thread
    def _daily_loop():
        import time as _t
        while True:
            _t.sleep(86400)  # 24h
            try:
                from core.context_pack import daily_tick
                daily_tick()
            except Exception:
                pass

    try:
        daily_thread = threading.Thread(target=_daily_loop, daemon=True, name="daily-scheduler")
        daily_thread.start()
        print("[DAILY SCHEDULER] Background scheduler started.")
    except Exception as exc:
        print(f"[DAILY SCHEDULER] WARNING: {exc}")

    # Start swarm runner as a daemon thread (won't block shutdown)
    try:
        from swarm_runner import run_loop as _runner_loop
        runner_thread = threading.Thread(target=_runner_loop, daemon=True, name="swarm-runner")
        runner_thread.start()
        print("[SWARM RUNNER] Background runner started.")
    except Exception as exc:
        print(f"[SWARM RUNNER] WARNING: Could not start runner â€” {exc}")

    uvicorn.run("server:app", host="0.0.0.0", port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()


