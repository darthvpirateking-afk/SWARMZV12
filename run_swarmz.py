#!/usr/bin/env python3
import socket
import uvicorn
from swarmz_runtime.api.server import app

def _lan_ip() -> str:
    """Return the best-guess LAN IP for this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8012
    lan = _lan_ip()
    print(f"  Local:   http://localhost:{port}")
    print(f"  LAN:     http://{lan}:{port}")
    print()
    uvicorn.run(app, host=host, port=port)
