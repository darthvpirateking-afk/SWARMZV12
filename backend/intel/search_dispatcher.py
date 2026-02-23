from __future__ import annotations

from backend.entity.mood_modifiers import apply_numeric_modifier

SEARCH_PROVIDERS = [
    "duckduckgo",
    "tavily",
    "perplexity",
    "google_cse",
    "traversaal",
    "searxng",
]


def get_active_providers(
    curiosity: int, patience: int, mood: str | None = "calm"
) -> list[str]:
    count = max(1, int((curiosity / 100) * len(SEARCH_PROVIDERS)))
    include_slow = patience >= 50
    providers = SEARCH_PROVIDERS[:count]
    if not include_slow:
        providers = [p for p in providers if p not in ["perplexity", "traversaal"]]

    providers_bonus = int(max(0, apply_numeric_modifier(0, "search_providers", mood)))
    if providers_bonus > 0:
        final_count = min(len(SEARCH_PROVIDERS), len(providers) + providers_bonus)
        providers = SEARCH_PROVIDERS[:final_count]
    return providers
