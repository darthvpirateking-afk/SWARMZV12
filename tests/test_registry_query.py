"""Registry query() behavior tests."""
from __future__ import annotations

from core.registry import ManifestRegistry


def test_query_returns_manifest_list_for_capability() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")

    rows = reg.query("data.read")
    assert rows
    assert all("data.read" in row.get("capabilities", []) for row in rows)


def test_query_empty_for_unknown_capability() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")
    assert reg.query("missing.capability") == []
