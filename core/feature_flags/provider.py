"""Feature-flag provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FeatureFlagProvider(ABC):
    @abstractmethod
    def is_enabled(self, flag_id: str, context: dict[str, Any] | None = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_value(self, flag_id: str, context: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError
