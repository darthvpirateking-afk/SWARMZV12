from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Feature:
    name: str
    value: Any
    target_id: str
    computed_at: float = field(default_factory=time.time)
    ttl_hours: float = 24.0
    source: str = ""

    @property
    def is_fresh(self) -> bool:
        age_h = (time.time() - self.computed_at) / 3600
        return age_h < self.ttl_hours


FEATURE_CATALOG: dict[str, dict[str, Any]] = {
    "tech_stack": {"ttl_hours": 48, "source": "fingerprinter"},
    "open_ports": {"ttl_hours": 12, "source": "nmap"},
    "admin_panel_exposed": {"ttl_hours": 24, "source": "browser_recon"},
    "has_sqli_params": {"ttl_hours": 6, "source": "api_engine"},
    "default_creds_tested": {"ttl_hours": 168, "source": "default_creds"},
    "cves_known": {"ttl_hours": 6, "source": "vuln_db"},
    "secrets_found": {"ttl_hours": 168, "source": "secret_scanner"},
    "osint_enriched": {"ttl_hours": 48, "source": "osint_enricher"},
}


def get_feature(target_id: str, feature_name: str, feature_store: dict[str, dict[str, Feature]]) -> Feature | None:
    feat = feature_store.get(target_id, {}).get(feature_name)
    if feat and feat.is_fresh:
        return feat
    return None


def set_feature(target_id: str, feature: Feature, feature_store: dict[str, dict[str, Feature]]) -> None:
    feature_store.setdefault(target_id, {})[feature.name] = feature


def get_feature_store_config(patience: int, curiosity: int) -> dict[str, Any]:
    return {
        "enabled": patience >= 35,
        "persist_to_db": True,
        "cross_target_features": curiosity >= 60,
        "auto_invalidate": True,
        "prefetch_on_mission_start": patience >= 50,
        "storage_table": "nexusmon_features",
    }


def prefetch_features(target_id: str, feature_store: dict[str, dict[str, Feature]]) -> dict[str, Feature]:
    cached = feature_store.get(target_id, {})
    return {name: feat for name, feat in cached.items() if feat.is_fresh}
