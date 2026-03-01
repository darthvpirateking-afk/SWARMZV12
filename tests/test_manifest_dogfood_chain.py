"""Dogfood chain integration test."""
from __future__ import annotations

from core.feature_flags.file_provider import FileFeatureFlagProvider
from core.registry import ManifestRegistry
from plugins.manifest_chain_plugin import ManifestChainPlugin


def test_manifest_chain_plugin_end_to_end() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")

    plugin = ManifestChainPlugin(reg, flags=FileFeatureFlagProvider())
    result = plugin.run_chain("https://example.test/data", trace_id="test-trace")

    assert result["fetcher"].startswith("fetcher@")
    assert result["transformer"].startswith("transformer@")
    assert result["reporter"].startswith("reporter@")
    assert result["report"]["count"] == 2
    assert result["report"]["rows"][0]["value"] == "ALPHA"


def test_registry_query_used_by_plugin() -> None:
    reg = ManifestRegistry()
    reg.load_all("config/manifests")

    assert reg.query("data.fetch")
    assert reg.query("data.transform")
    assert reg.query("report.generate")
