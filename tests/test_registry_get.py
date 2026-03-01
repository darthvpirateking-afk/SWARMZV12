"""Registry get() behavior tests."""
from __future__ import annotations

from core.registry import ManifestRegistry


def test_registry_get_exact_and_alias() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")

    manifest = reg.get("fetcher@1.0.0")
    assert manifest is not None
    assert manifest["id"] == "fetcher@1.0.0"

    alias = reg.get("fetcher")
    assert alias is not None
    assert alias["id"].startswith("fetcher@")


def test_registry_get_missing_returns_none() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")
    assert reg.get("does-not-exist") is None
