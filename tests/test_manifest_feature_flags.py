"""Feature flag provider behavior tests."""
from __future__ import annotations

import json
from pathlib import Path

from core.feature_flags.file_provider import FileFeatureFlagProvider


def test_file_provider_returns_flag_values(tmp_path: Path) -> None:
    config = tmp_path / "flags.json"
    config.write_text(json.dumps({"flags": {"alpha": True, "beta": "rollout"}}), encoding="utf-8")

    provider = FileFeatureFlagProvider(config_path=str(config))
    assert provider.is_enabled("alpha") is True
    assert provider.get_value("beta") == "rollout"


def test_manifest_context_overrides_file_flag(tmp_path: Path) -> None:
    config = tmp_path / "flags.json"
    config.write_text(json.dumps({"flags": {"enabled": False}}), encoding="utf-8")

    provider = FileFeatureFlagProvider(config_path=str(config))
    value = provider.get_value("enabled", {"manifest_feature_flags": {"enabled": True}})
    assert value is True
