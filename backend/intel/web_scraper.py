from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier


def get_web_intel_config(curiosity: int, mood: str | None = "calm") -> dict:
    config = {
        "enabled": curiosity >= 30,
        "depth": "deep" if curiosity >= 70 else "surface",
        "max_pages_per_session": int((curiosity / 100) * 30),
        "auto_trigger_on_unknown_target": curiosity >= 60,
    }
    config["max_pages_per_session"] = int(
        max(
            0,
            apply_numeric_modifier(
                config["max_pages_per_session"], "web_intel_max_pages", mood
            ),
        )
    )
    return config
