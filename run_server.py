#!/usr/bin/env python3
import argparse
import json
import socket
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


def _resolve_host_port() -> tuple[str, int]:
    cfg = _load_runtime_config()
    host = cfg.get("bind") or cfg.get("host") or "0.0.0.0"
    port = cfg.get("port") or cfg.get("api_port") or cfg.get("uiPort")
    try:
        port = int(port)
    except Exception:
        port = 8012
    return host, port


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="Run SWARMZ server")
    cfg_host, cfg_port = _resolve_host_port()
    parser.add_argument("--port", type=int, default=cfg_port, help=f"Port to bind (default {cfg_port})")
    parser.add_argument("--host", type=str, default=cfg_host, help="Host/interface to bind (0.0.0.0 or 127.0.0.1)")
    args = parser.parse_args()

    lan = _lan_ip()
    print(f"LOCAL: http://127.0.0.1:{args.port}/")
    print(f"LAN:   http://{lan}:{args.port}/")
    print(f"HOST:  {args.host}")

    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
