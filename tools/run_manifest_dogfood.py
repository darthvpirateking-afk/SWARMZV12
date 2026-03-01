"""Run manifest chain plugin and persist dogfood logs."""
from __future__ import annotations

import json
from pathlib import Path

from core.feature_flags.file_provider import FileFeatureFlagProvider
from core.registry import registry
from plugins.manifest_chain_plugin import ManifestChainPlugin


def main() -> int:
    registry.load_all("config/manifests")
    plugin = ManifestChainPlugin(registry, flags=FileFeatureFlagProvider())
    result = plugin.run_chain("https://example.test/api/events", trace_id="dogfood-run")

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    log_path = artifacts_dir / "dogfood-manifest-chain.log"
    log_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Dogfood run written to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
