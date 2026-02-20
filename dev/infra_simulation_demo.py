# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""Dev-only helper to exercise the infra orchestrator simulation.

This script is **optional** and lives under `dev/` so it does not
interfere with core behavior. It assumes the SWARMZ runtime server is
running locally and, if infra is enabled, it will:

- Send a couple of sample infra metrics
- Show the infra overview, autoscale plan, and backup plan
- Trigger simulation-only infra missions via /v1/infra/plan_missions

Usage (from repository root):

  SWARMZ_INFRA_ORCHESTRATOR_ENABLED=1 python dev/infra_simulation_demo.py

The script fails gracefully if the server is not running or if the
infra orchestrator is disabled.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests

BASE_URL = os.environ.get("SWARMZ_RUNTIME_URL", "http://127.0.0.1:8012")


def _print(title: str, payload: Any) -> None:
    print("\n==", title, "==")
    try:
        print(json.dumps(payload, indent=2, sort_keys=True))
    except TypeError:
        print(payload)


def _get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=5)


def _post(path: str, body: Dict[str, Any] | None = None) -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=body or {}, timeout=5)


def main() -> None:
    print(f"[dev] Using runtime at {BASE_URL}")

    try:
        r = _get("/health")
        r.raise_for_status()
        _print("/health", r.json())
    except Exception as exc:  # pragma: no cover - Dev helper
        print(f"[dev] Could not reach runtime /health: {exc}")
        return

    # Check if infra endpoints are enabled.
    try:
        o = _get("/v1/infra/overview")
        if o.status_code == 404:
            print("[dev] /v1/infra/* endpoints are disabled (infra_orchestrator_enabled=False).")
            return
    except Exception as exc:  # pragma: no cover
        print(f"[dev] Error calling /v1/infra/overview: {exc}")
        return

    # Send a couple of sample metrics.
    samples = [
        {"node_id": "node-1", "cpu": 0.9, "memory": 0.8, "disk": 0.7, "net_rx": 10, "net_tx": 5},
        {"node_id": "node-2", "cpu": 0.2, "memory": 0.3, "disk": 0.4, "net_rx": 1, "net_tx": 2},
    ]
    for s in samples:
        try:
            resp = _post("/v1/infra/metrics", s)
            _print("POST /v1/infra/metrics", resp.json())
        except Exception as exc:  # pragma: no cover
            print(f"[dev] Error sending metrics sample {s}: {exc}")

    # Overview and plans
    try:
        overview = _get("/v1/infra/overview").json()
        _print("/v1/infra/overview", overview)
    except Exception as exc:
        print(f"[dev] Error fetching /v1/infra/overview: {exc}")

    try:
        auto = _get("/v1/infra/autoscale_plan").json()
        _print("/v1/infra/autoscale_plan", auto)
    except Exception as exc:
        print(f"[dev] Error fetching /v1/infra/autoscale_plan: {exc}")

    try:
        backup = _get("/v1/infra/backup_plan").json()
        _print("/v1/infra/backup_plan", backup)
    except Exception as exc:
        print(f"[dev] Error fetching /v1/infra/backup_plan: {exc}")

    # Plan missions (simulation-only)
    try:
        res = _post("/v1/infra/plan_missions")
        _print("POST /v1/infra/plan_missions", res.json())
    except Exception as exc:
        print(f"[dev] Error calling /v1/infra/plan_missions: {exc}")


if __name__ == "__main__":  # pragma: no cover
    main()

