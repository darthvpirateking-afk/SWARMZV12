from datetime import datetime, timezone
from typing import Any, Dict

from api.companion_core_models import (
    CompanionCoreMessageResponse,
    CompanionCoreStatusResponse,
)


class CompanionCoreService:
    def get_status(self) -> CompanionCoreStatusResponse:
        memory = self._load_memory()
        outcomes = memory.get("mission_outcomes", []) if isinstance(memory, dict) else []
        return CompanionCoreStatusResponse(
            ok=True,
            source="core.companion",
            memory_version=int(memory.get("version", 0)) if isinstance(memory, dict) else 0,
            outcomes_count=len(outcomes) if isinstance(outcomes, list) else 0,
            summary=str(memory.get("summary", "")) if isinstance(memory, dict) else "",
            generated_at=datetime.now(timezone.utc),
        )

    def message(self, text: str) -> CompanionCoreMessageResponse:
        text = text.strip()
        if not text:
            return CompanionCoreMessageResponse(
                ok=False,
                reply="Empty message.",
                source="validation",
                generated_at=datetime.now(timezone.utc),
            )

        try:
            from core.companion import chat as companion_chat

            result: Dict[str, Any] = companion_chat(text)
            return CompanionCoreMessageResponse(
                ok=bool(result.get("ok", True)),
                reply=str(result.get("reply", "(empty)")),
                source=str(result.get("source", "core.companion")),
                generated_at=datetime.now(timezone.utc),
            )
        except Exception:
            return CompanionCoreMessageResponse(
                ok=True,
                reply="ACKNOWLEDGED: " + text[:120],
                source="fallback",
                generated_at=datetime.now(timezone.utc),
            )

    def _load_memory(self) -> Dict[str, Any]:
        try:
            from core.companion import load_memory

            memory = load_memory()
            if isinstance(memory, dict):
                return memory
        except Exception:
            pass
        return {"summary": "No companion memory available.", "version": 0, "mission_outcomes": []}
