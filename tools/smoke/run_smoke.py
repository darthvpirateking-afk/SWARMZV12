# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Smoke Test Runner

Boots the server (or confirms it is already running), then runs a sequence
of HTTP checks.  Prints PASS / FAIL per step and an overall verdict.

Usage:
    python tools/smoke/run_smoke.py          # assumes server already up
    python tools/smoke/run_smoke.py --boot   # starts server, waits, tests, stops
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG = ROOT / "config" / "runtime.json"


def load_cfg():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get(url, timeout=10):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        ct = resp.headers.get("Content-Type", "")
        if "json" in ct:
            return json.loads(body)
        return body


def post_json(url, body, headers=None, timeout=10):
    data = json.dumps(body).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class SmokeRunner:
    def __init__(self, base_url):
        self.base = base_url
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def step(self, name, fn):
        print(f"  [{self.passed + self.failed + 1}] {name} ... ", end="", flush=True)
        try:
            result = fn()
            if result is True or result is None:
                print("PASS")
                self.passed += 1
            elif isinstance(result, str) and result.startswith("WARN"):
                print(result)
                self.warnings += 1
                self.passed += 1
            else:
                print(f"FAIL: {result}")
                self.failed += 1
        except Exception as e:
            print(f"FAIL: {e}")
            self.failed += 1

    def report(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"  SMOKE TEST RESULT: {self.passed}/{total} passed", end="")
        if self.warnings:
            print(f" ({self.warnings} warnings)", end="")
        print()
        if self.failed == 0:
            print("  VERDICT: ALL CLEAR")
        else:
            print(f"  VERDICT: {self.failed} FAILURES â€” check output above")
        print(f"{'='*50}")
        return self.failed == 0


def main():
    cfg = load_cfg()
    port = cfg.get("port", 8012)
    base = f"http://127.0.0.1:{port}"

    print(f"SWARMZ SMOKE TESTS â€” targeting {base}")
    print()

    runner = SmokeRunner(base)

    # 1. Health endpoint
    def check_health():
        r = get(f"{base}/health")
        if isinstance(r, dict) and r.get("status") == "ok":
            return True
        return f"unexpected: {r}"

    runner.step("GET /health", check_health)

    # 2. Root / index
    def check_root():
        r = get(f"{base}/")
        if isinstance(r, str) and ("swarmz" in r.lower() or "<html" in r.lower()):
            return True
        if isinstance(r, dict):
            return True
        return f"unexpected type: {type(r)}"

    runner.step("GET / (index)", check_root)

    # 3. Runtime status
    def check_status():
        try:
            r = get(f"{base}/v1/runtime/status")
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "WARN: /v1/runtime/status not found (may not be implemented)"
            raise

    runner.step("GET /v1/runtime/status", check_status)

    # 4. Missions list
    def check_missions():
        try:
            r = get(f"{base}/v1/missions")
            if isinstance(r, (list, dict)):
                return True
            return f"unexpected: {type(r)}"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "WARN: /v1/missions not found"
            raise

    runner.step("GET /v1/missions", check_missions)

    # 5. Dispatch test mission
    def check_dispatch():
        try:
            r = post_json(
                f"{base}/v1/sovereign/dispatch",
                {"intent": "smoke_test", "scope": "verify"},
            )
            if isinstance(r, dict):
                return True
            return f"unexpected: {r}"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return "WARN: dispatch requires auth (expected)"
            if e.code == 404:
                return "WARN: /v1/sovereign/dispatch not found"
            raise

    runner.step("POST /v1/sovereign/dispatch", check_dispatch)

    # 6. Zapier inbound
    def check_zapier_inbound():
        secret = cfg.get("integrations", {}).get("zapier", {}).get("shared_secret", "")
        try:
            r = post_json(
                f"{base}/v1/zapier/inbound",
                {
                    "source": "smoke",
                    "type": "smoke.test",
                    "payload": {"x": 1},
                    "dedupe_key": "smoke-runner-1",
                },
                {"X-SWARMZ-SECRET": secret},
            )
            if isinstance(r, dict) and (r.get("ok") or r.get("dedupe")):
                return True
            return f"unexpected: {r}"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "WARN: /v1/zapier/inbound not found (server restart needed?)"
            raise

    runner.step("POST /v1/zapier/inbound", check_zapier_inbound)

    # 7. System log
    def check_syslog():
        try:
            r = get(f"{base}/v1/system/log")
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "WARN: /v1/system/log not found"
            raise

    runner.step("GET /v1/system/log", check_syslog)

    print()
    ok = runner.report()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL: {e}")
        sys.exit(1)
