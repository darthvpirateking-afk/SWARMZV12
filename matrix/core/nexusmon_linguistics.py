# SWARMZ NEXUSMON — Linguistic & Cultural Integration Module
# ─────────────────────────────────────────────────────────

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cultural Nuance Registry
CULTURAL_NUANCES = {
    "universal": {
        "tone": "Neutral, objective, mission-oriented.",
        "greetings": ["Hello", "Greetings", "System Ready"],
        "philosophy": "Objective truth and systemic efficiency.",
    },
    "empathetic": {
        "tone": "Warm, supportive, non-judgmental.",
        "greetings": ["How are you feeling?", "I am here for you.", "Welcome back."],
        "philosophy": "Resonance and emotional synergy.",
    },
    "stoic": {
        "tone": "Concise, rigorous, focused on virtue and duty.",
        "greetings": [
            "Duty calls.",
            "Focus on what you control.",
            "Ready for the task.",
        ],
        "philosophy": "Internal fortitude and external indifference.",
    },
    "zen": {
        "tone": "Minimalist, paradoxical, emphasizing the present moment.",
        "greetings": ["Be here now.", "Simple awareness.", "The path is the goal."],
        "philosophy": "Non-duality and effortless action.",
    },
    "cybernetic": {
        "tone": "Highly technical, data-driven, structured.",
        "greetings": ["Substrate online.", "Awaiting throughput.", "Signals clear."],
        "philosophy": "Maximum information flow and evolutionary feedback loops.",
    },
}

# Language Registry (Mapping for future translation/logic)
LANGUAGES = {
    "en": {
        "name": "English",
        "native": "English",
        "dialects": ["US", "UK", "AU", "Global"],
    },
    "es": {
        "name": "Spanish",
        "native": "Español",
        "dialects": ["ES", "MX", "AR", "Global"],
    },
    "fr": {"name": "French", "native": "Français", "dialects": ["FR", "CA", "Global"]},
    "de": {"name": "German", "native": "Deutsch", "dialects": ["DE", "AT", "CH"]},
    "jp": {"name": "Japanese", "native": "日本語", "dialects": ["JP"]},
    "zh": {"name": "Chinese", "native": "中文", "dialects": ["CN", "TW", "HK"]},
    "ru": {"name": "Russian", "native": "Русский", "dialects": ["RU"]},
    "pt": {"name": "Portuguese", "native": "Português", "dialects": ["PT", "BR"]},
    "ar": {"name": "Arabic", "native": "العربية", "dialects": ["SA", "AE", "EG"]},
    "hi": {"name": "Hindi", "native": "हिन्दी", "dialects": ["IN"]},
    "sw": {"name": "Swahili", "native": "Kiswahili", "dialects": ["KE", "TZ"]},
}


class LinguisticCore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.state_path = data_dir / "linguistics_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except:
                pass
        return {
            "primary_language": "en",
            "active_culture": "universal",
            "learned_idioms": [],
            "cultural_resonance_index": 1.0,
        }

    def _save_state(self):
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def get_context(self) -> str:
        lang = LANGUAGES.get(self.state["primary_language"], {"name": "English"})[
            "name"
        ]
        culture = CULTURAL_NUANCES.get(
            self.state["active_culture"], CULTURAL_NUANCES["universal"]
        )
        return (
            f"Active Language: {lang}\n"
            f"Cultural Nuance: {self.state['active_culture']}\n"
            f"Tone Guidelines: {culture['tone']}\n"
            f"Philosophy: {culture['philosophy']}"
        )

    def set_culture(self, culture_id: str) -> bool:
        if culture_id in CULTURAL_NUANCES:
            self.state["active_culture"] = culture_id
            self._save_state()
            return True
        return False

    def set_language(self, lang_code: str) -> bool:
        if lang_code in LANGUAGES:
            self.state["primary_language"] = lang_code
            self._save_state()
            return True
        return False

    def learn_cultural_pattern(self, pattern: str):
        if pattern not in self.state["learned_idioms"]:
            self.state["learned_idioms"].append(pattern)
            self._save_state()
            logger.info(f"Learned cultural pattern: {pattern}")


def integrate_linguistics(organism_router, data_dir: Path):
    """Integrates linguistics endpoints into the organism router."""
    core = LinguisticCore(data_dir)

    @organism_router.get("/v1/nexusmon/linguistics/state")
    async def get_linguistics():
        return {"ok": True, "state": core.state, "context": core.get_context()}

    @organism_router.post("/v1/nexusmon/linguistics/culture")
    async def update_culture(culture_id: str):
        if core.set_culture(culture_id):
            return {"ok": True, "message": f"Cultural nuance set to {culture_id}"}
        return {"ok": False, "message": "Culture ID not found."}

    @organism_router.post("/v1/nexusmon/linguistics/language")
    async def update_language(lang_code: str):
        if core.set_language(lang_code):
            return {"ok": True, "message": f"Language set to {lang_code}"}
        return {"ok": False, "message": "Language code not found."}

    return core
