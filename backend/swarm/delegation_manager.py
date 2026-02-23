from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier, apply_override


def get_delegation_config(autonomy: int, loyalty: int, mood: str | None = "calm") -> dict:
    config = {
        "delegation_enabled": autonomy >= 45,
        "require_operator_approval_per_delegation": loyalty >= 70,
        "max_concurrent_agents": int((autonomy / 100) * 5),
        "agent_roles_available": (
            ["research"]
            if autonomy < 55
            else ["research", "development"] if autonomy < 75 else ["research", "development", "infrastructure"]
        ),
    }
    config["delegation_enabled"] = bool(
        apply_override(config["delegation_enabled"], "delegation_enabled", mood)
    )
    config["max_concurrent_agents"] = int(
        max(0, apply_numeric_modifier(config["max_concurrent_agents"], "max_concurrent_agents", mood))
    )
    return config
