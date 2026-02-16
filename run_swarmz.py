#!/usr/bin/env python3
import socket
import argparse
import cProfile
import pstats
import io
import uvicorn
import swarmz_runtime.api.server as server
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
    parser = argparse.ArgumentParser(description="Run SWARMZ runtime")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose runtime logging")
    parser.add_argument("--profile", action="store_true", help="Enable cProfile and write data/profile.txt")
    args = parser.parse_args()

    if args.verbose:
        server.VERBOSE = True
        server.telemetry.set_verbose(True)

    host = "0.0.0.0"
    port = 8012
    lan = _lan_ip()
    base_url = f"http://{lan}:{port}"
    print(f"  Local:   http://localhost:{port}")
    print(f"  LAN:     {base_url}")
    print(f"  UI:      {base_url}/")
    print(f"  Pair:    {base_url}/v1/pairing/info")
    pin_info = getattr(server, "_pin_info", {})
    pin_file = pin_info.get("file")
    pin_source = pin_info.get("source")
    if pin_info.get("generated"):
        print(f"  Operator PIN (generated now): {pin_info.get('pin')} (saved to {pin_file})")
    elif pin_file:
        print(f"  Operator PIN source: {pin_source} (stored at {pin_file})")
    print()

    if args.profile:
        prof_path = server.DATA_DIR / "profile.txt"
        pr = cProfile.Profile()
        pr.enable()
        uvicorn.run(app, host=host, port=port)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
        ps.print_stats(40)
        prof_path.write_text(s.getvalue())
        print(f"Profile written to {prof_path}")
    else:
        uvicorn.run(app, host=host, port=port)
