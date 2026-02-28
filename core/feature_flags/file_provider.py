"""In-repo file-backed feature-flag provider."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.feature_flags.provider import FeatureFlagProvider


class FileFeatureFlagProvider(FeatureFlagProvider):
    def __init__(self, config_path: str = "config/feature_flags.json") -> None:
        self._config_path = Path(config_path)

    def _load_flags(self) -> dict[str, Any]:
        if not self._config_path.exists():
            return {}
        payload = json.loads(self._config_path.read_text(encoding="utf-8-sig"))
        return payload if isinstance(payload, dict) else {}

    def is_enabled(self, flag_id: str, context: dict[str, Any] | None = None) -> bool:
        value = self.get_value(flag_id, context)
        return bool(value)

    def get_value(self, flag_id: str, context: dict[str, Any] | None = None) -> Any:
        context = context or {}
        manifest_flags = context.get("manifest_feature_flags", {})
        if isinstance(manifest_flags, dict) and flag_id in manifest_flags:
            return manifest_flags[flag_id]

        flags = self._load_flags().get("flags", {})
        if isinstance(flags, dict):
            return flags.get(flag_id)
        return None
