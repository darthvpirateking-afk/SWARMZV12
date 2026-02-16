#!/usr/bin/env python3
import argparse
import socket
import uvicorn


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
    parser.add_argument("--port", type=int, default=8012, help="Port to bind (default 8012)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host/interface to bind (0.0.0.0 or 127.0.0.1)")
    args = parser.parse_args()

    lan = _lan_ip()
    print(f"LOCAL: http://127.0.0.1:{args.port}/")
    print(f"LAN:   http://{lan}:{args.port}/")
    print(f"HOST:  {args.host}")

    uvicorn.run("server:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
