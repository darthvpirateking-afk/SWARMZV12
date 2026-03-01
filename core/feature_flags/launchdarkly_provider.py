"""LaunchDarkly provider scaffold (optional dependency)."""
from __future__ import annotations

from typing import Any

from core.feature_flags.provider import FeatureFlagProvider


class LaunchDarklyFeatureFlagProvider(FeatureFlagProvider):
    def __init__(self, sdk_key: str | None = None, fallback: dict[str, Any] | None = None) -> None:
        self._sdk_key = sdk_key
        self._fallback = fallback or {}
        self._client = None
        try:
            import ldclient  # type: ignore
            from ldclient.config import Config  # type: ignore

            if sdk_key:
                ldclient.set_config(Config(sdk_key))
                self._client = ldclient.get()
        except Exception:
            self._client = None

    def is_enabled(self, flag_id: str, context: dict[str, Any] | None = None) -> bool:
        value = self.get_value(flag_id, context)
        return bool(value)

    def get_value(self, flag_id: str, context: dict[str, Any] | None = None) -> Any:
        if self._client is None:
            return self._fallback.get(flag_id)

        ld_context = context or {"key": "anonymous"}
        try:
            return self._client.variation(flag_id, ld_context, self._fallback.get(flag_id))
        except Exception:
            return self._fallback.get(flag_id)
