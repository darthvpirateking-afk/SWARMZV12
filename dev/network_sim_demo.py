# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Dev-only helper: simulate multiple infra nodes sending metrics
into the SWARMZ runtime, then print a simple network snapshot.

This script is non-destructive and intended for local experiments.
"""

import random
import time
from typing import Dict, Any

import requests

BASE_URL = "http://127.0.0.1:8012"
NODES = ["node-a", "node-b", "node-c"]


def _post(path: str, payload: Dict[str, Any]) -> None:
    resp = requests.post(f"{BASE_URL}{path}", json=payload, timeout=5)
    resp.raise_for_status()


def _get(path: str) -> Dict[str, Any]:
    resp = requests.get(f"{BASE_URL}{path}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def send_sample() -> None:
    for node in NODES:
        sample = {
            "node_id": node,
            "cpu": random.uniform(10, 90),
            "memory": random.uniform(10, 90),
            "gpu": random.uniform(0, 90),
            "disk": random.uniform(10, 90),
            "net_rx": random.uniform(1, 50),
            "net_tx": random.uniform(1, 50),
        }
        _post("/v1/infra/metrics", sample)


def main() -> None:
    print("[network-sim] sending metrics for nodes:", ", ".join(NODES))
    try:
        health = _get("/health")
    except Exception as exc:  # pragma: no cover - dev helper
        print("!! runtime health check failed:", exc)
        return

    if health.get("status") != "ok":
        print("!! runtime not healthy:", health)
        return

    try:
        resp = requests.get(f"{BASE_URL}/v1/infra/overview", timeout=5)
        if resp.status_code == 404:
            print("/v1/infra/overview returned 404 â€” infra orchestrator disabled.")
            return
    except Exception as exc:
        print("!! /v1/infra/overview not reachable:", exc)
        return

    for i in range(3):  # a few short rounds
        send_sample()
        print(f"round {i+1} sent")
        time.sleep(0.3)

    overview = _get("/v1/infra/overview")
    autoscale = _get("/v1/infra/autoscale_plan")

    nodes = overview.get("nodes", [])
    summary = autoscale.get("summary", {})

    print("\n=== NETWORK SNAPSHOT ===")
    print("Nodes:", len(nodes))
    print("Autoscale status:", summary.get("status"))
    print("Hot nodes:", summary.get("hot", []))
    print("Cold nodes:", summary.get("cold", []))


if __name__ == "__main__":  # pragma: no cover - dev helper
    main()
