from __future__ import annotations

from enum import Enum

from backend.entity.mood_modifiers import apply_numeric_modifier


class TaskStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


def get_kanban_config(patience: int, autonomy: int, mood: str | None = "calm") -> dict:
    config = {
        "max_parallel_tasks": int((autonomy / 100) * 8),
        "auto_retry_failed": patience >= 50,
        "max_retries": int((patience / 100) * 5),
        "block_on_dependency": True,
        "show_in_cockpit": True,
        "persist_completed_tasks": patience >= 40,
    }
    config["max_parallel_tasks"] = int(
        max(
            0,
            apply_numeric_modifier(
                config["max_parallel_tasks"], "kanban_parallel_tasks", mood
            ),
        )
    )
    return config
