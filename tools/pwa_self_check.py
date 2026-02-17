# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Minimal self-check for the PWA endpoints without extra dependencies."""

import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch(url: str, timeout: float = 5.0):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = resp.getcode()
        ctype = resp.headers.get("Content-Type", "") or ""
        body = resp.read()
    return status, ctype, body


def main():
    parser = argparse.ArgumentParser(description="PWA self-check")
    parser.add_argument("--base", default="http://127.0.0.1:8012", help="Base URL for the server")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    checks = []

    try:
        status, ctype, _ = fetch(f"{base}/")
        ok = status == 200 and "text/html" in ctype
        checks.append(("GET /", ok, f"status={status} ctype={ctype}"))
    except Exception as exc:  # pragma: no cover
        checks.append(("GET /", False, str(exc)))

    try:
        status, ctype, body = fetch(f"{base}/app.js")
        ok = status == 200 and "javascript" in ctype and b"document.addEventListener" in body
        checks.append(("GET /app.js", ok, f"status={status} ctype={ctype}"))
    except Exception as exc:  # pragma: no cover
        checks.append(("GET /app.js", False, str(exc)))

    try:
        status, ctype, _ = fetch(f"{base}/styles.css")
        ok = status == 200 and "text/css" in ctype
        checks.append(("GET /styles.css", ok, f"status={status} ctype={ctype}"))
    except Exception as exc:  # pragma: no cover
        checks.append(("GET /styles.css", False, str(exc)))

    try:
        status, ctype, body = fetch(f"{base}/v1/pairing/info")
        parsed = None
        try:
            parsed = json.loads(body.decode("utf-8"))
        except Exception:
            parsed = None
        ok = status == 200 and parsed is not None
        checks.append(("GET /v1/pairing/info", ok, f"status={status} ctype={ctype}"))
    except Exception as exc:  # pragma: no cover
        checks.append(("GET /v1/pairing/info", False, str(exc)))

    all_ok = True
    for name, ok, info in checks:
        if ok:
            print(f"PASS {name} :: {info}")
        else:
            all_ok = False
            print(f"FAIL {name} :: {info}")

    if all_ok:
        print("PWA self-check: PASS")
        return 0
    print("PWA self-check: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

