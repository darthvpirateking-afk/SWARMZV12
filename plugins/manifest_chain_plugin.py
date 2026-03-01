"""Dogfood plugin chain: fetcher -> transformer -> reporter."""
from __future__ import annotations

from typing import Any

from core.feature_flags.provider import FeatureFlagProvider
from core.manifest_audit import ManifestAuditLogger
from core.registry import ManifestRegistry


class _NullFlags(FeatureFlagProvider):
    def is_enabled(self, flag_id: str, context: dict[str, Any] | None = None) -> bool:
        return True

    def get_value(self, flag_id: str, context: dict[str, Any] | None = None) -> Any:
        return True


class ManifestChainPlugin:
    def __init__(
        self,
        manifest_registry: ManifestRegistry,
        flags: FeatureFlagProvider | None = None,
        audit: ManifestAuditLogger | None = None,
    ) -> None:
        self._registry = manifest_registry
        self._flags = flags or _NullFlags()
        self._audit = audit or ManifestAuditLogger(path="artifacts/dogfood-audit.jsonl")

    def _require_capability(self, capability: str) -> dict[str, Any]:
        rows = self._registry.query(capability)
        if not rows:
            raise RuntimeError(f"No manifest supports capability '{capability}'")
        return rows[0]

    def run_chain(self, source_url: str, trace_id: str = "dogfood-trace") -> dict[str, Any]:
        fetcher = self._require_capability("data.fetch")
        transformer = self._require_capability("data.transform")
        reporter = self._require_capability("report.generate")

        if not self._flags.is_enabled("manifest_chain_enhanced_report", {"trace_id": trace_id}):
            raise RuntimeError("manifest_chain_enhanced_report is disabled")

        fetched = {
            "source_url": source_url,
            "items": [
                {"id": 1, "value": "alpha"},
                {"id": 2, "value": "beta"},
            ],
            "producer": fetcher["id"],
        }
        transformed = {
            "rows": [{"id": row["id"], "value": str(row["value"]).upper()} for row in fetched["items"]],
            "producer": transformer["id"],
        }
        report = {
            "title": "Manifest chain report",
            "count": len(transformed["rows"]),
            "producer": reporter["id"],
            "rows": transformed["rows"],
        }

        self._audit.log_flag_evaluation(
            actor="manifest_chain_plugin",
            manifest_id=reporter["id"],
            flag_id="manifest_chain_enhanced_report",
            old_value=False,
            new_value=True,
            trace_id=trace_id,
        )

        return {
            "fetcher": fetcher["id"],
            "transformer": transformer["id"],
            "reporter": reporter["id"],
            "report": report,
        }
