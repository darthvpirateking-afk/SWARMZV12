from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ResourceBudget:
    cpu_seconds: int
    memory_mb: int
    network_mb: int
    max_parallel_tasks: int


def get_resource_budget(
    patience: int, protectiveness: int, mood: str | None = "calm"
) -> dict[str, Any]:
    base = ResourceBudget(
        cpu_seconds=600 + int((patience / 100) * 2400),
        memory_mb=1024 + int((patience / 100) * 4096),
        network_mb=256 + int((patience / 100) * 2048),
        max_parallel_tasks=1 + int((patience / 100) * 4),
    )

    if protectiveness >= 70:
        base.network_mb = int(base.network_mb * 0.7)
        base.max_parallel_tasks = max(1, base.max_parallel_tasks - 1)

    if (mood or "").lower() == "restless":
        base.max_parallel_tasks += 1
    if (mood or "").lower() == "dormant":
        base.max_parallel_tasks = 1

    return asdict(base)


def enforce_budget(current: dict[str, int], budget: dict[str, int]) -> dict[str, Any]:
    violations = []
    for key in ["cpu_seconds", "memory_mb", "network_mb", "max_parallel_tasks"]:
        if int(current.get(key, 0)) > int(budget.get(key, 0)):
            violations.append(key)
    return {"ok": len(violations) == 0, "violations": violations}
