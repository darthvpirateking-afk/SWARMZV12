from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class OSINTRecord:
    target: str
    country: str = "unknown"
    asn: str = "unknown"
    cloud_provider: str = "unknown"
    source: str = "osint_enricher"


def infer_provider(hostname: str) -> str:
    host = (hostname or "").lower()
    if "amazonaws" in host or host.endswith("aws.com"):
        return "aws"
    if "azure" in host or "windows.net" in host:
        return "azure"
    if "google" in host or "gcp" in host:
        return "gcp"
    if "cloudflare" in host:
        return "cloudflare"
    return "unknown"


def enrich_target(target: str) -> dict[str, Any]:
    target_value = (target or "").strip()
    provider = infer_provider(target_value)
    record = OSINTRecord(target=target_value, cloud_provider=provider)
    return asdict(record)


def get_osint_config(curiosity: int, patience: int) -> dict[str, Any]:
    return {
        "enabled": curiosity >= 30,
        "resolve_dns": True,
        "resolve_asn": curiosity >= 45,
        "geo_enrich": curiosity >= 40,
        "api_catalog_lookup": curiosity >= 55,
        "max_osint_calls": 5 if patience < 50 else 20,
    }
