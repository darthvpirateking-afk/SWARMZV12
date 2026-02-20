#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_runtime_port(root: Path) -> int:
    runtime_json = root / "config" / "runtime.json"
    if not runtime_json.exists():
        return 8012
    try:
        data = json.loads(runtime_json.read_text(encoding="utf-8"))
        return int(data.get("port", 8012))
    except Exception:
        return 8012


def _load_operator_pin(root: Path) -> str:
    env_pin = (os.getenv("SWARMZ_OPERATOR_PIN") or "").strip()
    if env_pin:
        return env_pin

    pin_file = root / "data" / "operator_pin.txt"
    if pin_file.exists():
        try:
            pin = pin_file.read_text(encoding="utf-8").strip()
            if pin:
                return pin
        except Exception:
            pass

    return "123456"


def _http_json(
    method: str,
    url: str,
    *,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 8.0,
) -> Tuple[int, Dict[str, Any], str]:
    raw_body = None
    final_headers = dict(headers or {})
    if body is not None:
        raw_body = json.dumps(body).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url=url, method=method.upper(), data=raw_body, headers=final_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        text = exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, {}, str(exc)

    parsed: Dict[str, Any] = {}
    if text.strip():
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = {}

    return status, parsed, text


def _wait_for_health(base_url: str, timeout_s: float, req_timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    url = f"{base_url}/v1/health"

    while time.time() < deadline:
        code, payload, _ = _http_json("GET", url, timeout=req_timeout_s)
        if code == 200:
            return True
        time.sleep(0.5)
    return False


def _shutdown_process(proc: subprocess.Popen[Any], grace_s: float = 8.0) -> None:
    if proc.poll() is not None:
        return

    try:
        if os.name == "nt":
            proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
        else:
            proc.terminate()
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass

    try:
        proc.wait(timeout=grace_s)
        return
    except subprocess.TimeoutExpired:
        pass

    try:
        proc.kill()
        proc.wait(timeout=3.0)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="SWARMZ release smoke: health + dispatch")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for run_server.py if launch is needed")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default: from config/runtime.json or 8012)")
    parser.add_argument("--startup-timeout", type=float, default=45.0, help="Seconds to wait for /v1/health")
    parser.add_argument("--request-timeout", type=float, default=8.0, help="HTTP timeout")
    parser.add_argument("--server-log", default=None, help="Optional server log path")
    args = parser.parse_args()

    root = _repo_root()
    port = args.port if args.port is not None else _load_runtime_port(root)
    base_url = f"http://127.0.0.1:{port}"
    pin = _load_operator_pin(root)

    started_here = False
    proc: Optional[subprocess.Popen[Any]] = None

    # Reuse existing server if healthy.
    if _wait_for_health(base_url, timeout_s=2.0, req_timeout_s=args.request_timeout):
        print(f"Using existing server at {base_url}")
    else:
        log_path = Path(args.server_log) if args.server_log else (root / "data" / "release_smoke_server.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env.setdefault("SWARMZ_OPERATOR_PIN", pin)
        env.setdefault("OPERATOR_KEY", pin)

        cmd = [sys.executable, "run_server.py", "--host", args.host, "--port", str(port)]
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0

        print(f"Starting server: {' '.join(cmd)}")
        log_file = open(log_path, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            cwd=str(root),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            text=True,
        )
        started_here = True

        if not _wait_for_health(base_url, timeout_s=args.startup_timeout, req_timeout_s=args.request_timeout):
            print(f"FAIL: /v1/health not ready at {base_url}")
            _shutdown_process(proc)
            return 11
        print("PASS: /v1/health")

    try:
        dispatch_ok = False
        mission_id = "unknown"

        # Primary runtime dispatch endpoint.
        payload = {
            "goal": "release smoke check",
            "category": "coin",
            "constraints": {"source": "release_smoke"},
        }
        code, data, raw = _http_json(
            "POST",
            f"{base_url}/v1/dispatch",
            body=payload,
            headers={"X-Operator-Key": pin, "Content-Type": "application/json"},
            timeout=args.request_timeout,
        )
        if code == 200 and isinstance(data, dict):
            created = data.get("created") if isinstance(data.get("created"), dict) else {}
            run = data.get("run") if isinstance(data.get("run"), dict) else {}
            mission_id = created.get("mission_id") or run.get("mission_id") or "unknown"
            dispatch_ok = True
        elif code == 404:
            # Fallback dispatch endpoint used by server.py wrapper.
            fallback_payload = {"intent": "release smoke check", "scope": "release", "limits": {}}
            f_code, f_data, f_raw = _http_json(
                "POST",
                f"{base_url}/v1/sovereign/dispatch",
                body=fallback_payload,
                headers={"X-Operator-Key": pin, "Content-Type": "application/json"},
                timeout=args.request_timeout,
            )
            if f_code == 200 and isinstance(f_data, dict):
                mission_id = str(f_data.get("mission_id") or "unknown")
                dispatch_ok = True
            else:
                print(f"FAIL: fallback dispatch returned {f_code}: {f_raw[:500]}")
                return 13
        else:
            print(f"FAIL: /v1/dispatch returned {code}: {raw[:500]}")
            return 13

        if not dispatch_ok:
            print("FAIL: dispatch did not succeed")
            return 13

        print(f"PASS: dispatch (mission_id={mission_id})")
        print("PASS: release smoke complete")
        return 0
    finally:
        if started_here and proc is not None:
            _shutdown_process(proc)


if __name__ == "__main__":
    raise SystemExit(main())
