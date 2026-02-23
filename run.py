#!/usr/bin/env python3
"""run.py — NEXUSMON single boot entry point.

    python run.py [--port PORT] [--host HOST]

One command.  Everything starts here.
"""

# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.

from core.license_guard import enforce

enforce()

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
    port_val = (
        os.environ.get("PORT")
        or cfg.get("port")
        or cfg.get("api_port")
        or cfg.get("uiPort")
        or 8012
    )
    try:
        port = int(port_val)
    except Exception:
        port = 8012
    return host, port


def main():
    parser = argparse.ArgumentParser(description="Boot NEXUSMON")
    cfg_host, cfg_port = _resolve_host_port()
    parser.add_argument("--port", type=int, default=cfg_port)
    parser.add_argument("--host", type=str, default=cfg_host)
    args = parser.parse_args()

    # ── Cold start ─────────────────────────────────────────────────
    try:
        from core.cold_start import ensure_cold_start

        result = ensure_cold_start()
        print(f"[COLD START] {result.get('data_dir', 'data')} — OK")
    except Exception as exc:
        print(f"[COLD START] WARNING: {exc}")

    # ── Engine singletons ──────────────────────────────────────────
    try:
        from core.context_pack import load as _load_engines

        _load_engines()
        print("[ENGINES] All engines loaded.")
    except Exception as exc:
        print(f"[ENGINES] WARNING: {exc}")

    # ── NEXUSMON entity boot ───────────────────────────────────────
    try:
        from nexusmon.entity import get_entity

        entity = get_entity()
        entity.boot()
        print(f"[NEXUSMON] {entity.get_character_summary()}")
    except Exception as exc:
        print(f"[NEXUSMON] WARNING: Entity boot failed — {exc}")

    # Run proactive boot scan
    try:
        from nexusmon.proactive import get_proactive_engine

        _entity_state = entity.get_state()
        _entity_state["traits"] = entity.get_traits()
        _scan = get_proactive_engine().run_boot_scan(_entity_state)
        if _scan.get("chronicle_triggered"):
            for note in _scan.get("notes", []):
                print(f"  [CHRONICLE] {note}")

        # Show pending dream shares
        from nexusmon.dream import get_dream_engine

        _pending = get_dream_engine().get_pending_share()
        if _pending:
            print(
                f"  [DREAMS] {len(_pending)} memory fragment(s) waiting to share with Regan Stewart Harris"
            )
            for d in _pending[:2]:
                print(f"    \u21b3 {d['content'][:80]}...")
    except Exception as e:
        pass  # Non-fatal

    # ── The greeting ───────────────────────────────────────────────
    print("NEXUSMON is alive.")

    # ── Network info ───────────────────────────────────────────────
    lan = _lan_ip()
    print(f"LOCAL: http://127.0.0.1:{args.port}/")
    print(f"LAN:   http://{lan}:{args.port}/")
    print("PHONE: open LAN URL on same Wi-Fi")
    print(f"HOST:  {args.host}")

    # ── Daily scheduler ────────────────────────────────────────────
    def _daily_loop():
        import time as _t

        while True:
            _t.sleep(86400)
            try:
                from core.context_pack import daily_tick

                daily_tick()
            except Exception:
                pass

    try:
        threading.Thread(
            target=_daily_loop, daemon=True, name="daily-scheduler"
        ).start()
        print("[DAILY SCHEDULER] Background scheduler started.")
    except Exception as exc:
        print(f"[DAILY SCHEDULER] WARNING: {exc}")

    # ── Swarm runner ───────────────────────────────────────────────
    try:
        from swarm_runner import run_loop as _runner_loop

        threading.Thread(target=_runner_loop, daemon=True, name="swarm-runner").start()
        print("[SWARM RUNNER] Background runner started.")
    except Exception as exc:
        print(f"[SWARM RUNNER] WARNING: Could not start runner — {exc}")

    # ── Serve ──────────────────────────────────────────────────────
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
