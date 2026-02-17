# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Dev-only helper: synthesizes a simple "decision space" view
for the operator by querying existing SWARMZ endpoints.

This does not change runtime behavior; it only reads state and prints
contextual guidance messages to the console.
"""

import json
import sys
from typing import Any, Dict

import requests

BASE_URL = "http://127.0.0.1:8012"


def _get(path: str) -> Dict[str, Any]:
  resp = requests.get(f"{BASE_URL}{path}", timeout=5)
  resp.raise_for_status()
  try:
    return resp.json()
  except Exception:
    return {}


def main() -> None:
  print("[decision-space] probing runtime at", BASE_URL)
  try:
    health = _get("/health")
  except Exception as exc:  # pragma: no cover - dev helper
    print("!! runtime health check failed:", exc)
    sys.exit(1)

  if health.get("status") != "ok":
    print("!! runtime not healthy:", health)
    sys.exit(1)

  ui = {}
  missions = []
  infra_overview = None
  autoscale = None
  backup = None

  try:
    ui = _get("/v1/ui/state")
  except Exception as exc:  # pragma: no cover - dev helper
    print("!! /v1/ui/state failed:", exc)

  try:
    m = _get("/v1/missions/list")
    missions = m.get("missions", []) if m.get("ok") else []
  except Exception as exc:  # pragma: no cover - dev helper
    print("!! /v1/missions/list failed:", exc)

  try:
    resp = requests.get(f"{BASE_URL}/v1/infra/overview", timeout=5)
    if resp.status_code != 404:
      infra_overview = resp.json()
      autoscale = _get("/v1/infra/autoscale_plan")
      backup = _get("/v1/infra/backup_plan")
  except Exception:
    pass

  pending = sum(1 for m in missions if (m.get("status") or "PENDING") == "PENDING")
  total = ui.get("missions", {}).get("count_total") or len(missions)

  print("\n=== DECISION SPACE ===")
  print("Total missions:", total)
  print("Pending missions:", pending)

  if infra_overview is not None:
    nodes = len(infra_overview.get("nodes", []))
    print("Infra nodes:", nodes)
    if autoscale and autoscale.get("summary"):
      print("Autoscale status:", autoscale["summary"].get("status"))
    if backup and backup.get("summary"):
      print("Backup status:", backup["summary"].get("status"))

  suggestions = []
  if pending:
    suggestions.append(f"Review and commit one of {pending} pending missions.")

  if infra_overview is not None and autoscale and autoscale.get("summary"):
    status = autoscale["summary"].get("status")
    if status and status != "normal":
      suggestions.append(f"Infra autoscale status is '{status}' â€” consider an infra simulation run.")

  if not suggestions:
    suggestions.append("System steady. Define a new INTENT or companion query.")

  print("\nSuggested next moves:")
  for idx, line in enumerate(suggestions, 1):
    print(f" {idx}. {line}")

  print("\nRaw snapshot (for debugging):")
  print(json.dumps({
    "ui": ui,
    "missions_count": len(missions),
    "infra_overview_present": infra_overview is not None,
  }, indent=2))


if __name__ == "__main__":  # pragma: no cover - dev helper
  main()

