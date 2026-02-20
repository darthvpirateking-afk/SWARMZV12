#!/usr/bin/env python3
"""Render post-deploy verification for SWARMZ.

Usage:
  python tools/render_post_deploy_check.py --base https://swarmzV10-.onrender.com
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def get_json(url: str):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = response.read().decode("utf-8", errors="ignore")
        return response.status, raw


def post_json(url: str, payload: dict):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read().decode("utf-8", errors="ignore")
        return response.status, raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Base URL, e.g. https://swarmzV10-.onrender.com")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    checks = [
        ("health", f"{base}/v1/health", "GET"),
        ("docs", f"{base}/docs", "GET"),
        ("ai_status", f"{base}/v1/ai/status", "GET"),
    ]

    ok = True
    for label, url, method in checks:
        try:
            status, raw = get_json(url)
            print(f"[{label}] {status} {url}")
            print(raw[:240])
        except urllib.error.HTTPError as exc:
            ok = False
            body = exc.read().decode("utf-8", errors="ignore")
            print(f"[{label}] HTTP {exc.code} {url}")
            print(body[:240])
        except Exception as exc:
            ok = False
            print(f"[{label}] ERROR {url} -> {exc}")
        print("---")

    chat_url = f"{base}/v1/nexusmon/chat"
    try:
        status, raw = post_json(chat_url, {"operator_id": "render-check", "message": "status"})
        print(f"[chat] {status} {chat_url}")
        print(raw[:320])
    except urllib.error.HTTPError as exc:
        ok = False
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"[chat] HTTP {exc.code} {chat_url}")
        print(body[:320])
    except Exception as exc:
        ok = False
        print(f"[chat] ERROR {chat_url} -> {exc}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
