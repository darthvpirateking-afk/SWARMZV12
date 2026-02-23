from __future__ import annotations

from backend.entity.mood_modifiers import apply_override


def get_monitoring_config(protectiveness: int, patience: int, mood: str | None = "calm") -> dict:
    config = {
        "log_level": "debug" if protectiveness >= 70 else "info" if protectiveness >= 40 else "warn",
        "trace_all_tool_calls": protectiveness >= 60,
        "alert_on_anomaly": protectiveness >= 50,
        "metrics_retention_days": int((patience / 100) * 90),
        "dashboard_refresh_ms": 5000 if protectiveness >= 80 else 30000,
    }
    config["log_level"] = apply_override(config["log_level"], "log_level", mood)
    return config
