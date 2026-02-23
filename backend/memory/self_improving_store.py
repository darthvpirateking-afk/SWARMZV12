from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier, apply_override


def get_memory_config(curiosity: int, patience: int, mood: str | None = "calm") -> dict:
    config = {
        "store_failed_attempts": curiosity >= 50,
        "cross_mission_recall": curiosity >= 70,
        "auto_compress_after_mission": patience >= 40,
        "self_update_behavioral_weights": patience >= 65,
        "max_recalled_entries": int((curiosity / 100) * 50),
        "inject_context_threshold": 0.75,
        "xp_on_new_discovery": curiosity >= 40,
        "memory_decay_enabled": patience < 30,
    }
    config["cross_mission_recall"] = bool(
        apply_override(config["cross_mission_recall"], "cross_mission_recall", mood)
    )
    config["max_recalled_entries"] = int(
        max(
            0,
            apply_numeric_modifier(
                config["max_recalled_entries"], "experience_buffer_size", mood
            ),
        )
    )
    return config
