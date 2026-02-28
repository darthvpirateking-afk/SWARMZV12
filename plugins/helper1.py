from __future__ import annotations

from typing import Any

from plugins.helper1_internal_life_stubs import (
    build_module_stub_registry,
    get_module_stub,
)


def run(task: dict[str, Any]) -> dict[str, Any]:
    """
    Minimal helper1 kernel plugin.

    Deterministic behavior:
    - Reads optional `query` from task
    - Returns a structured result payload
    """
    action = str(task.get("action", "")).strip().lower()
    if action == "list_module_stubs":
        return {
            "result": "helper1 module stubs listed",
            "module_stub_ids": sorted(build_module_stub_registry().keys()),
            "symbolic_only": True,
        }

    module_id = str(task.get("module_stub_id", "")).strip()
    if action == "get_module_stub" and module_id:
        return {
            "result": "helper1 module stub fetched",
            "module_stub": get_module_stub(module_id),
            "symbolic_only": True,
        }

    query = str(task.get("query", ""))
    return {"result": f"helper1 processed: {query}"}
