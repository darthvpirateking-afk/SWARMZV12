from __future__ import annotations


PROVIDER_CAPABILITIES = {
    "anthropic": {"reasoning": 95, "code": 85, "speed": 70},
    "openai": {"reasoning": 90, "code": 90, "speed": 80},
    "deepseek": {"reasoning": 80, "code": 90, "speed": 85},
    "ollama": {"reasoning": 70, "code": 75, "speed": 95},
    "gemini": {"reasoning": 85, "code": 80, "speed": 85},
}


def select_provider(task_type: str, creativity: int, autonomy: int) -> str:
    if autonomy >= 75:
        if task_type == "exploit_reasoning":
            return "anthropic"
        if task_type == "code_generation":
            return "deepseek"
        if task_type == "fast_scan":
            return "ollama"
    if creativity >= 70 and task_type == "code_generation":
        return "openai"
    return "anthropic"
